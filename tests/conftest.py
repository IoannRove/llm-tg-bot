import pytest
from unittest.mock import MagicMock, AsyncMock
import os
from tg_bot_chat.config.settings import Settings, TelegramConfig, AIConfig, RedisConfig, BotConfig

@pytest.fixture
def mock_settings():
    """
    Fixture for application settings
    """
    return Settings(
        telegram=TelegramConfig(
            bot_token="test_token",
            bot_username="test_bot"
        ),
        ai=AIConfig(
            api_key="test_key",
            model="gpt-4o-mini",
            provider="openai"
        ),
        redis=RedisConfig(
            host="localhost",
            port=6379,
            db=0
        ),
        bot=BotConfig(
            base_prompt="Test prompt",
            context_window_size=10,
            trigger_words=["test", "bot"]
        )
    )

@pytest.fixture
def mock_redis():
    """
    Fixture for mocked Redis client
    """
    mock = MagicMock()
    # Setup default behaviors for redis methods if needed
    mock.lrange.return_value = []
    mock.get.return_value = None
    return mock

@pytest.fixture
def mock_ai_client():
    """
    Fixture for mocked AsyncOpenAI client
    """
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock()
    return mock

