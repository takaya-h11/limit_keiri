"""
Message store module
LINE Webhookから受信したメッセージを保存・取得する
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class MessageStore:
    """Simple message storage for LINE webhook messages"""

    def __init__(self, max_messages: int = 100, persist_file: Optional[str] = None):
        """
        Initialize message store

        Args:
            max_messages: Maximum number of messages to store in memory
            persist_file: Optional file path to persist messages
        """
        self.max_messages = max_messages
        self.persist_file = persist_file
        self.messages: List[Dict] = []
        self.lock = Lock()

        # Load from file if exists
        if self.persist_file:
            self._load_from_file()

    def add_message(self, user_id: str, text: str, message_id: str):
        """
        Add a new message to the store

        Args:
            user_id: LINE user ID
            text: Message text
            message_id: LINE message ID
        """
        with self.lock:
            message = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "text": text,
                "message_id": message_id
            }

            # Add to beginning of list (newest first)
            self.messages.insert(0, message)

            # Limit to max_messages
            if len(self.messages) > self.max_messages:
                self.messages = self.messages[:self.max_messages]

            logger.info(f"Message added: {text[:50]}... (total: {len(self.messages)})")

            # Persist if configured
            if self.persist_file:
                self._save_to_file()

    def get_messages(self, limit: int = 10) -> List[Dict]:
        """
        Get recent messages

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of messages (newest first)
        """
        with self.lock:
            return self.messages[:limit]

    def clear(self):
        """Clear all messages"""
        with self.lock:
            self.messages = []
            logger.info("All messages cleared")

            if self.persist_file:
                self._save_to_file()

    def _save_to_file(self):
        """Save messages to file"""
        try:
            if self.persist_file:
                Path(self.persist_file).parent.mkdir(parents=True, exist_ok=True)
                with open(self.persist_file, 'w', encoding='utf-8') as f:
                    json.dump(self.messages, f, ensure_ascii=False, indent=2)
                logger.debug(f"Messages saved to {self.persist_file}")
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")

    def _load_from_file(self):
        """Load messages from file"""
        try:
            if self.persist_file and Path(self.persist_file).exists():
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
                logger.info(f"Loaded {len(self.messages)} messages from {self.persist_file}")
        except Exception as e:
            logger.error(f"Failed to load messages: {e}")
            self.messages = []


# Global message store instance
_message_store: Optional[MessageStore] = None


def get_message_store() -> MessageStore:
    """Get or create the global message store"""
    global _message_store
    if _message_store is None:
        # Persist to data/messages.json
        persist_file = "data/messages.json"
        _message_store = MessageStore(max_messages=100, persist_file=persist_file)
    return _message_store
