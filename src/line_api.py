"""
LINE Messaging API integration module
LINE APIからメッセージを取得する機能
"""

import logging
from typing import List, Dict

from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import MessageEvent, TextMessage

from .config import Config

logger = logging.getLogger(__name__)


class LineClient:
    """LINE Messaging API client"""

    def __init__(self):
        """Initialize LINE Bot API client"""
        if not Config.LINE_CHANNEL_ACCESS_TOKEN:
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is not set")

        self.api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)

    def fetch_messages(self, limit: int = 10) -> List[Dict]:
        """
        Fetch recent messages from LINE
        LINEから最新のトーク履歴を取得

        Note: Webhookサーバーで受信したメッセージをメッセージストアから取得します。

        Args:
            limit: 取得するメッセージ数の上限

        Returns:
            List[Dict]: メッセージのリスト
            [
                {
                    "timestamp": "2025-12-26T12:34:56",
                    "user_id": "user_id",
                    "text": "12/28 PayPalで月4回プラン 35,200円",
                    "message_id": "message_id"
                },
                ...
            ]
        """
        from .message_store import get_message_store

        message_store = get_message_store()
        messages = message_store.get_messages(limit=limit)

        logger.info(f"Fetched {len(messages)} messages from store")

        return messages

    def send_message(self, user_id: str, text: str):
        """
        Send a message to a LINE user
        LINEユーザーにメッセージを送信

        Args:
            user_id: LINE user ID
            text: メッセージ本文
        """
        try:
            self.api.push_message(user_id, TextMessage(text=text))
            logger.info(f"Message sent to {user_id}: {text}")
        except LineBotApiError as e:
            logger.error(f"Failed to send message: {e}")
            raise
