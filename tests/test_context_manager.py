import json
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from tg_bot_chat.services.context_manager import ContextManager, ChatMessage

@pytest.fixture
def context_manager(mock_settings, mock_redis):
    # Arrange
    with patch("tg_bot_chat.services.context_manager.redis.Redis", return_value=mock_redis):
        return ContextManager(mock_settings.redis)

def test_add_message(context_manager, mock_redis):
    # Arrange
    chat_id = 123
    message = ChatMessage(
        user_id=1,
        username="user",
        message="hello",
        timestamp=datetime.now(),
        message_id=100
    )

    # Act
    context_manager.add_message(chat_id, message)

    # Assert
    mock_redis.lpush.assert_called_once()
    mock_redis.expire.assert_called_once()
    # Verify key format
    call_args = mock_redis.lpush.call_args
    assert call_args[0][0] == f"chat_context:{chat_id}"

def test_get_context(context_manager, mock_redis):
    # Arrange
    chat_id = 123
    limit = 5
    timestamp = datetime.now().isoformat()
    # Mock redis data
    message_data = {
        "user_id": 1,
        "username": "user",
        "message": "hello",
        "timestamp": timestamp,
        "message_id": 100
    }
    mock_redis.lrange.return_value = [json.dumps(message_data)]

    # Act
    messages = context_manager.get_context(chat_id, limit)

    # Assert
    mock_redis.lrange.assert_called_once_with(f"chat_context:{chat_id}", 0, limit - 1)
    assert len(messages) == 1
    assert messages[0].message == "hello"
    assert messages[0].user_id == 1

def test_clear_context(context_manager, mock_redis):
    # Arrange
    chat_id = 123

    # Act
    context_manager.clear_context(chat_id)

    # Assert
    mock_redis.delete.assert_called_once_with(f"chat_context:{chat_id}")

def test_get_user_context(context_manager, mock_redis):
    # Arrange
    chat_id = 123
    user_id = 456
    timestamp = datetime.now().isoformat()
    message_data = {
        "user_id": user_id,
        "username": "user",
        "message": "private msg",
        "timestamp": timestamp,
        "message_id": 101
    }
    mock_redis.lrange.return_value = [json.dumps(message_data)]

    # Act
    messages = context_manager.get_user_context(chat_id, user_id)

    # Assert
    expected_key = f"user_context:{chat_id}:{user_id}"
    mock_redis.lrange.assert_called_once_with(expected_key, 0, 19) # default limit 20 -> 0..19
    assert len(messages) == 1
    assert messages[0].message == "private msg"

def test_add_user_message(context_manager, mock_redis):
    # Arrange
    chat_id = 123
    user_id = 456
    message = ChatMessage(
        user_id=user_id,
        username="user",
        message="test msg",
        timestamp=datetime.now(),
        message_id=200
    )

    # Act
    context_manager.add_user_message(chat_id, user_id, message)

    # Assert
    expected_key = f"user_context:{chat_id}:{user_id}"
    mock_redis.lpush.assert_called_once()
    args = mock_redis.lpush.call_args
    assert args[0][0] == expected_key
    mock_redis.expire.assert_called_once_with(expected_key, 86400)

def test_get_chat_users(context_manager, mock_redis):
    # Arrange
    chat_id = 123
    # Mock scan_iter return values
    # Note: user asked to test get_chat_users, and we recently changed it to use scan_iter
    mock_redis.scan_iter.return_value = [
        f"user_context:{chat_id}:100",
        f"user_context:{chat_id}:200"
    ]

    # Act
    user_ids = context_manager.get_chat_users(chat_id)

    # Assert
    mock_redis.scan_iter.assert_called_once()
    assert 100 in user_ids
    assert 200 in user_ids
    assert len(user_ids) == 2

