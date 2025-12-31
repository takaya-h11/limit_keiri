"""
Tests for message_store module
"""

import pytest
from src.message_store import MessageStore


def test_message_store_add_message():
    """Test adding messages to store"""
    store = MessageStore(max_messages=5, persist_file=None)

    store.add_message("user1", "Test message 1", "msg1")
    store.add_message("user2", "Test message 2", "msg2")

    messages = store.get_messages()
    assert len(messages) == 2
    assert messages[0]["text"] == "Test message 2"  # Newest first
    assert messages[1]["text"] == "Test message 1"


def test_message_store_max_messages():
    """Test that store limits messages to max_messages"""
    store = MessageStore(max_messages=3, persist_file=None)

    for i in range(5):
        store.add_message(f"user{i}", f"Message {i}", f"msg{i}")

    messages = store.get_messages()
    assert len(messages) == 3
    assert messages[0]["text"] == "Message 4"  # Newest
    assert messages[2]["text"] == "Message 2"  # Oldest kept


def test_message_store_get_messages_limit():
    """Test getting limited number of messages"""
    store = MessageStore(max_messages=10, persist_file=None)

    for i in range(5):
        store.add_message(f"user{i}", f"Message {i}", f"msg{i}")

    messages = store.get_messages(limit=2)
    assert len(messages) == 2
    assert messages[0]["text"] == "Message 4"


def test_message_store_clear():
    """Test clearing all messages"""
    store = MessageStore(max_messages=10, persist_file=None)

    store.add_message("user1", "Test message", "msg1")
    assert len(store.get_messages()) == 1

    store.clear()
    assert len(store.get_messages()) == 0
