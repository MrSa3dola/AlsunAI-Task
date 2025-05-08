import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

# Import the unified workflow
from math_agent import handle_query  # adjust import path

load_dotenv()

# WhatsApp Cloud API credentials
token = os.getenv("WA_TOKEN")
phone_number_id = os.getenv("PHONE_NUMBER_ID")
verify_token = os.getenv("WA_VERIFY_TOKEN")

# Use a fixed public URL for your ngrok or hosting
public_url = "https://internal-teaching-kiwi.ngrok-free.app"

app = FastAPI()

# Serve audio files
app.mount("/static", StaticFiles(directory="./static"), name="static")


# WhatsApp API sender utility
async def send_whatsapp_message(payload: dict):
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        # debug logging:
        # print("→ POST", url)
        # print("→ payload:", json.dumps(payload, indent=2))
        # print("← status:", resp.status_code)
        # print("← response:", await resp.text)
        resp.raise_for_status()
        return resp.json()


# Verification endpoint
@app.get("/")
async def root():
    return {"message": "OK"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token_sent = request.query_params.get("hub.verify_token")
    # print("token_sent = ", token_sent)
    # print("verify_token = ", verify_token)
    if mode == "subscribe" and token_sent == verify_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


# Incoming message handler
@app.post("/webhook")
async def whatsapp_webhook(req: Request):
    data = await req.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages")
            if not messages:
                continue
            msg = messages[0]
            from_phone = msg.get("from")

            # Text messages
            if msg.get("type") == "text":
                body = msg["text"]["body"]
                # Delegate all logic (language, math detection, translation, agent call)
                reply = handle_query(body)
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_phone,
                    "type": "text",
                    "text": {"preview_url": False, "body": reply},
                }
                await send_whatsapp_message(payload)

            # Audio messages
            elif msg.get("type") == "audio":
                # Always reply with the predefined Arabic audio
                audio_link = f"{public_url}/static/Arabic.mp3"
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_phone,
                    "type": "audio",
                    "audio": {"link": audio_link},
                }
                await send_whatsapp_message(payload)

    return Response(status_code=200)
