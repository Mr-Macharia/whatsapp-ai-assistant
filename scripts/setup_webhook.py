"""
One-time setup script: register your local webhook URL with Evolution API.

Run once after starting your server:
    uv run python scripts/setup_webhook.py

Evolution API will then POST all MESSAGES_UPSERT events to your WEBHOOK_URL.
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

EVO_BASE_URL = os.getenv("EVO_BASE_URL", "http://localhost:8080")
EVO_API_KEY  = os.getenv("EVO_API_KEY", "")
EVO_INSTANCE = os.getenv("EVO_INSTANCE", "my-agent")
WEBHOOK_URL  = os.getenv("WEBHOOK_URL", "http://192.168.82.127:7777/webhook/whatsapp")

if not EVO_API_KEY:
    print("ERROR: EVO_API_KEY is not set in .env")
    sys.exit(1)

print(f"Registering webhook for instance '{EVO_INSTANCE}'")
print(f"  Evolution API : {EVO_BASE_URL}")
print(f"  Webhook URL   : {WEBHOOK_URL}")
print()

url     = f"{EVO_BASE_URL}/webhook/set/{EVO_INSTANCE}"
headers = {"apikey": EVO_API_KEY, "Content-Type": "application/json"}
payload = {
    "webhook": {
        "url": WEBHOOK_URL,
        "enabled": True,
        "webhookByEvents": False,   # single URL for all events
        "webhookBase64": False,     # don't inline media as base64
        "events": [
            "MESSAGES_UPSERT",      # incoming (and sent) messages
            "CONNECTION_UPDATE",    # QR code / connect status (optional but handy)
        ],
    }
}

try:
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    print("Webhook registered successfully!")
    print(resp.json())
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
    print("Response:", e.response.text)
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print(f"Could not connect to Evolution API at {EVO_BASE_URL}")
    print("Is the Docker container running?")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
