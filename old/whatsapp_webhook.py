import json
import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

# Import the unified workflow
from math_agent import handle_query  # adjust import path

load_dotenv()

# WhatsApp router
whatsapp_router = FastAPI()

public_url = "https://internal-teaching-kiwi.ngrok-free.app"


@whatsapp_router.get("/")
async def root():
    return {"message": "OK"}


@whatsapp_router.api_route("/webhook", methods=["GET", "POST"])
async def handle_whatsapp_events(request: Request) -> Response:
    """
    Handles incoming messages and status updates from the WhatsApp Cloud API.

    Args:
        request (Request): Incoming HTTP request containing message or status update.

    Returns:
        Response: HTTP response with appropriate status code and message.
    """
    if request.method == "GET":
        logging.info("Received GET request for verification")
        params = request.query_params
        print(params.get("hub.verify_token"))
        print(os.getenv("WA_VERIFY_TOKEN"))
        # if params.get("hub.verify_token") == os.getenv("WA_VERIFY_TOKEN"):
        return Response(content=params.get("hub.challenge"), status_code=200)
        # return Response(content="Invalid verification token", status_code=403)

    try:
        logging.info("Processing incoming event...")
        payload = await request.json()
        event_data = payload["entry"][0]["changes"][0]["value"]
        logging.info(f"Event data: {event_data}")

        if "messages" in event_data:
            logging.info(f"📩 Incoming Message: {event_data['messages'][0]}")
            user_message = event_data["messages"][0]
            sender_id = user_message["from"]
            message_content = user_message["text"]["body"]

            bot_reply = handle_query(message_content)
            response_status = await send_whatsapp_message(sender_id, bot_reply)

            if response_status:
                return {"status": "success", "message": "Processed"}
            else:
                return Response(content="Failed to send response", status_code=500)
        elif "statuses" in event_data:
            logging.info(
                f"📊 Status Update: {event_data['statuses'][0]['status']} (ID: {event_data['statuses'][0]['id']})"
            )
            return Response(content="Status update received", status_code=200)

        else:
            return Response(content="Unknown event type", status_code=400)

    except Exception as error:
        logging.error(f"Error handling event: {error}", exc_info=True)
        return Response(content="Internal server error", status_code=500)


async def send_whatsapp_message(recipient_id: str, message_text: str) -> bool:
    """
    Sends a response message to a user via the WhatsApp Cloud API.

    Args:
        from_number (str): The recipient's phone number.
        response_text (str): The message content to be sent.
        message_type (str, optional): The type of message (default is "text").

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    headers = {
        "Authorization": "Bearer " + os.getenv("WA_TOKEN"),
        "Content-Type": "application/json",
    }

    message_payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message_text},
    }

    logging.info(f"Sending message to {recipient_id} with content: {message_payload}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/{os.getenv('VERSION')}/{os.getenv('PHONE_NUMBER_ID')}/messages",
                headers=headers,
                json=message_payload,
            )
            logging.info(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                logging.error(f"Error: {response.status_code}, {response.text}")
                return False
            return True
    except httpx.RequestError as http_error:
        logging.error(f"HTTP request error: {http_error}")
        return False
    except Exception as general_error:
        logging.error(f"Unexpected error: {general_error}")
        return False
