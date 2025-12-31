"""
LINE Webhook server
FastAPIを使用してLINE Messaging APIのWebhookを受信する
"""

import hashlib
import hmac
import base64
import logging
from typing import List

from fastapi import FastAPI, Request, HTTPException, Header
from linebot import WebhookParser
from linebot.models import MessageEvent, TextMessage
from linebot.exceptions import InvalidSignatureError

from .config import Config
from .message_store import get_message_store

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="LINE Webhook Server for Limit Yotsuya")

# Initialize LINE webhook parser
parser = WebhookParser(Config.LINE_CHANNEL_SECRET)


def verify_signature(body: bytes, signature: str) -> bool:
    """
    Verify LINE webhook signature

    Args:
        body: Request body
        signature: X-Line-Signature header value

    Returns:
        bool: True if signature is valid
    """
    if not Config.LINE_CHANNEL_SECRET:
        logger.error("LINE_CHANNEL_SECRET is not set")
        return False

    hash_digest = hmac.new(
        Config.LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(hash_digest).decode('utf-8')

    return hmac.compare_digest(signature, expected_signature)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "LINE Webhook Server for Limit Yotsuya",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    message_store = get_message_store()
    messages = message_store.get_messages(limit=1)

    return {
        "status": "healthy",
        "messages_count": len(messages),
        "last_message_time": messages[0]["timestamp"] if messages else None
    }


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    """
    LINE Webhook endpoint
    LINEからのWebhookを受信してメッセージを保存する

    Args:
        request: FastAPI Request object
        x_line_signature: LINE signature header
    """
    # Get request body
    body = await request.body()

    # Verify signature
    if not x_line_signature:
        logger.error("Missing X-Line-Signature header")
        raise HTTPException(status_code=400, detail="Missing signature")

    if not verify_signature(body, x_line_signature):
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse webhook events
    try:
        events = parser.parse(body.decode('utf-8'), x_line_signature)
    except InvalidSignatureError:
        logger.error("Invalid signature from parser")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Process events
    message_store = get_message_store()

    for event in events:
        logger.info(f"Received event: {event}")

        # Handle text messages
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_id = event.source.user_id
            text = event.message.text
            message_id = event.message.id

            logger.info(f"Text message from {user_id}: {text}")

            # Store message
            message_store.add_message(
                user_id=user_id,
                text=text,
                message_id=message_id
            )

    return {"status": "ok", "events_processed": len(events)}


@app.get("/messages")
async def get_messages(limit: int = 10):
    """
    Get recent messages (for debugging)

    Args:
        limit: Number of messages to return

    Returns:
        List of recent messages
    """
    message_store = get_message_store()
    messages = message_store.get_messages(limit=limit)

    return {
        "count": len(messages),
        "messages": messages
    }


@app.delete("/messages")
async def clear_messages():
    """Clear all messages (for debugging)"""
    message_store = get_message_store()
    message_store.clear()

    return {"status": "ok", "message": "All messages cleared"}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the webhook server

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn

    logger.info(f"Starting webhook server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Validate config
    Config.validate()

    # Run server
    run_server()
