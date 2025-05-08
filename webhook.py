import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

from math_agent import handle_query

load_dotenv()

# WhatsApp Cloud API credentials
token = os.getenv("WA_TOKEN")
phone_number_id = os.getenv("PHONE_NUMBER_ID")
verify_token = os.getenv("WA_VERIFY_TOKEN")
public_url = "https://internal-teaching-kiwi.ngrok-free.app"

app = FastAPI()
app.mount("/static", StaticFiles(directory="./static"), name="static")


async def send_whatsapp_message(payload: dict):
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


@app.get("/")
async def root():
    return {"message": "OK"}


# Verification endpoint
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token_sent = request.query_params.get("hub.verify_token")
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
            if msg.get("type") == "text":
                body = msg["text"]["body"]
                reply = handle_query(body)
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_phone,
                    "type": "text",
                    "text": {"preview_url": False, "body": reply},
                }
                await send_whatsapp_message(payload)
            elif msg.get("type") == "audio":
                audio_link = f"{public_url}/static/Arabic.mp3"
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_phone,
                    "type": "audio",
                    "audio": {"link": audio_link},
                }
                await send_whatsapp_message(payload)
    return Response(status_code=200)
