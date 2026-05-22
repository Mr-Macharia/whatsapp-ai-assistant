import requests
from typing import Any, Dict, List, Optional

from agno.tools import tool
from app.config import settings


def _evo_send_text(
    to: str,
    text: str,
    delay: int = 0,
    link_preview: bool = True,
    mentioned: Optional[List[str]] = None,
    quoted: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Core Evolution API send — plain callable, no Agno wrapper.
    Import and call this directly from webhook handlers.
    """
    url = f"{settings.EVO_BASE_URL}/message/sendText/{settings.EVO_INSTANCE}"

    payload: Dict[str, Any] = {"number": to, "text": text}
    if delay:
        payload["delay"] = delay
    if not link_preview:
        payload["linkPreview"] = link_preview
    if mentioned:
        payload["mentioned"] = mentioned
    if quoted:
        payload["quoted"] = quoted

    headers = {
        "apikey": settings.EVO_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return {"success": True, **response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": str(e), "response_text": e.response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


# when giving the agent sending capability as a tool
@tool
def send_whatsapp_text(
    to: str,
    text: str,
    delay: int = 0,
    link_preview: bool = True,
    mentioned: Optional[List[str]] = None,
    quoted: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Send a WhatsApp text message through Evolution API.

    Args:
        to:           Recipient phone number or JID (e.g. "254743490973@s.whatsapp.net").
        text:         The message text to send.
        delay:        Optional delay in milliseconds before sending.
        link_preview: Whether to generate link previews (default True).
        mentioned:    Optional list of JIDs to mention.
        quoted:       Optional quoted message object.
    """
    return _evo_send_text(
        to=to,
        text=text,
        delay=delay,
        link_preview=link_preview,
        mentioned=mentioned,
        quoted=quoted,
    )
