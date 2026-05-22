import logging
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import settings
from app.agent import whatsapp_agent
from app.tools.whatsapp import _evo_send_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
log = logging.getLogger("whatsapp-agent")

app = FastAPI(title="WhatsApp Agent", version="1.0.0")

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

    try:
        response = await whatsapp_agent.arun(
            text,
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

    result = _evo_send_text(to=sender_number, text=reply_text)
    if result.get("success"):
        log.info("Reply sent to %s", sender_jid)
    else:
        log.error("Failed to send reply to %s: %s", sender_jid, result.get("error"))


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

    if settings.ALLOWED_NUMBER and sender_number != settings.ALLOWED_NUMBER:
        log.info("Ignoring message from %s / %s (not allowed)", sender_jid, sender_number)
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
