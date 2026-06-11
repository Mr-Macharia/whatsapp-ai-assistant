import logging
from fastapi import Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from app.db import whatsapp_db
from agno.os import AgentOS
from app.config import settings
from app.gichogu_agent import gichogu_agent
from app.rachael_agent import rachael_agent
from app.prompts import get_rachael_instructions, get_gichogu_instructions
from app.tools.whatsapp import _evo_send_text, _evo_send_text_async

AGENT_ROUTER = {
    settings.GICHOGU_NUMBER: gichogu_agent,
    settings.RACHAEL_NUMBER: rachael_agent,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
log = logging.getLogger("agents")

# Use AgentOS to wrap the FastAPI app so that WebSocket connections to /workflows/ws (e.g. from Agno Playground) are handled correctly
app = AgentOS(
    agents=[gichogu_agent, rachael_agent],
    db=whatsapp_db,
    scheduler=True,
    scheduler_base_url=settings.SERVER_URL,
    scheduler_poll_interval=15,
).get_app()

def _extract_text(message: dict) -> str | None:
    """Extract plain text from an Evolution API message object."""
    if text := message.get("conversation"):
        return text
    if ext := message.get("extendedTextMessage"):
        return ext.get("text")
    if btn := message.get("buttonsResponseMessage"):
        return btn.get("selectedDisplayText")
    if lst := message.get("listResponseMessage"):
        return lst.get("singleSelectReply", {}).get("selectedRowId")
    return None

def _extract_sender(data: dict) -> tuple[str | None, str | None]:
    """
    Return (reply_jid, phone_number) for an incoming message.
    """
    key = data.get("key", {})
    if key.get("fromMe", False):
        return None, None

    remote_jid: str = key.get("remoteJid", "")
    remote_jid_alt: str = key.get("remoteJidAlt", "")
    addressing_mode: str = key.get("addressingMode", "")

    if not remote_jid:
        return None, None

    if addressing_mode == "lid" and remote_jid_alt:
        phone_number = remote_jid_alt.split("@")[0]
        log.debug("LID mode: reply_jid=%s phone=%s", remote_jid, phone_number)
    else:
        phone_number = remote_jid.split("@")[0]

    return remote_jid, phone_number

@app.get("/webhook/whatsapp")
async def webhook_verify():
    """Health-check — Evolution API pings this to confirm the URL is live."""
    return Response(content="OK", media_type="text/plain")

async def process_message(text: str, sender_number: str, sender_jid: str, push_name: str):
    log.info("Message from %s (%s): %s", push_name, sender_jid, text[:120])

    agent = AGENT_ROUTER.get(sender_number)

    # Stamp the real current Kenya time (EAT) into the instructions on every request.
    # This ensures the correct time is used regardless of the server's deployment timezone.
    if sender_number == settings.RACHAEL_NUMBER:
        agent.instructions = get_rachael_instructions()
    elif sender_number == settings.GICHOGU_NUMBER:
        agent.instructions = get_gichogu_instructions()

    try:
        response = await agent.arun(
            text,
            session_id=sender_number,
            user_id=sender_number,
        )
        reply_text: str = response.content if response and response.content else ""
    except Exception as e:
        log.exception("Agent error for message from %s: %s", sender_jid, e)
        return

    if not reply_text:
        log.warning("Agent returned empty response for message from %s", sender_jid)
        return

    log.info("Replying to %s: %s", sender_jid, reply_text[:120])

    result = await _evo_send_text_async(to=sender_number, text=reply_text)
    if result.get("success"):
        log.info("Reply sent to %s", sender_jid)
    else:
        log.error("Failed to send reply to %s: %s", sender_jid, result.get("error"))

@app.post("/scheduled-run/{agent_id}")
async def scheduled_run(agent_id: str, request: Request):
    """Endpoint called by the Agno ScheduleManager when a schedule fires.

    Runs the agent with the scheduled message and sends the response
    back to the user on WhatsApp.
    """
    # Security: reject unauthorized triggers
    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("apikey", "")
    if not auth_header and api_key != settings.WEBHOOK_SECRET:
        log.error("Unauthorized attempt to trigger scheduled run for %s", agent_id)
        return Response(status_code=403, content="Unauthorized")

    payload = await request.json()
    message = payload.get("message", "")

    if not message:
        return JSONResponse(
            {"status": "failed", "reason": "missing 'message' in payload"},
            status_code=400,
        )

    # Resolve which agent to run and the phone number to deliver to.
    # Always use the phone number from AGENT_ROUTER (don't trust LLM-provided user_id).
    agent = None
    phone_number = None
    for number, registered_agent in AGENT_ROUTER.items():
        if registered_agent.id == agent_id or registered_agent.name == agent_id:
            agent = registered_agent
            phone_number = number
            break

    if agent is None:
        log.error("No agent found for id=%s", agent_id)
        return JSONResponse(
            {"status": "failed", "reason": f"agent '{agent_id}' not found"},
            status_code=404,
        )

    log.info("Scheduled run for agent=%s phone=%s message=%s", agent_id, phone_number, message[:120])

    # Refresh instructions (including current EAT time) before running —
    # mirrors the same stamp done in process_message for normal messages.
    if phone_number == settings.GICHOGU_NUMBER:
        agent.instructions = get_gichogu_instructions()
    elif phone_number == settings.RACHAEL_NUMBER:
        agent.instructions = get_rachael_instructions()

    # Wrap the payload message with an execution directive so the agent
    # performs the task rather than commenting on the schedule or its timing.
    # Without this, the agent picks up the "schedule testing" tone from
    # chat history and responds with celebration instead of actual output.
    scheduled_prompt = (
        f"[SCHEDULED TASK — execute autonomously]\n"
        f"Do NOT comment on schedules, timing, or whether this worked. "
        f"Simply perform the following task and deliver the result directly to the user:\n\n"
        f"{message}"
    )

    try:
        response = await agent.arun(
            scheduled_prompt,
            session_id=phone_number,
            user_id=phone_number,
        )
        reply_text = response.content if response and response.content else ""
    except Exception as e:
        log.exception("Scheduled run error for agent=%s: %s", agent_id, e)
        return JSONResponse(
            {"status": "failed", "reason": str(e)},
            status_code=500,
        )

    if reply_text and phone_number:
        result = await _evo_send_text_async(to=phone_number, text=reply_text)
        if result.get("success"):
            log.info("Scheduled run reply sent to %s", phone_number)
        else:
            log.error("Failed to send scheduled reply to %s: %s", phone_number, result.get("error"))

    return JSONResponse({
        "status": "success",
        "delivered_to": phone_number,
        "content": reply_text[:200] if reply_text else None,
    })

@app.post("/webhook/whatsapp")
async def webhook_receive(request: Request, background_tasks: BackgroundTasks):
    """
    Receive Evolution API webhook events and reply via the agent.
    """
    if settings.WEBHOOK_SECRET:
        if request.headers.get("apikey", "") != settings.WEBHOOK_SECRET:
            log.warning("Webhook secret mismatch — request ignored.")
            return Response(status_code=403)

    try:
        body = await request.json()
    except Exception:
        log.error("Failed to parse webhook body as JSON.")
        return Response(status_code=400)

    event: str = body.get("event", "")
    instance: str = body.get("instance", "")
    data: dict = body.get("data", {})

    log.info("Received event=%s instance=%s", event, instance)

    event_key = event.lower().replace(".", "_").replace("-", "_")
    if event_key != "messages_upsert":
        return JSONResponse({"status": "ignored", "reason": f"event={event}"})

    sender_jid, sender_number = _extract_sender(data)
    if sender_jid is None:
        return JSONResponse({"status": "ignored", "reason": "fromMe=true"})

    if settings.ALLOWED_NUMBERS and sender_number not in settings.ALLOWED_NUMBERS:
        log.info("Ignoring message from %s / %s (not allowed)", sender_number)
        return JSONResponse({"status": "ignored", "reason": "not allowed"})

    message_obj: dict = data.get("message", {})
    text = _extract_text(message_obj)
    if not text:
        log.info("No text content in message from %s — skipping.", sender_number)
        return JSONResponse({"status": "ignored", "reason": "no text content"})

    push_name: str = data.get("pushName", sender_number)

    # Process message in the background to return 200 OK immediately to Evolution API
    background_tasks.add_task(process_message, text, sender_number, sender_jid, push_name)

    return JSONResponse({"status": "ok", "note": "processing in background"})
