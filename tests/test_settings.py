import os
import pytest
from tg_bot_chat.config.settings import get_settings, Settings

def test_get_settings_loads_from_env():
    # Arrange
    # Setup environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "env_token"
    os.environ["AI_API_KEY"] = "env_key"
    os.environ["BOT_USERNAME"] = "env_bot"
    os.environ["TRIGGER_WORDS"] = "one,two,three"

    # Act
    settings = get_settings()

    # Assert
    assert isinstance(settings, Settings)
    assert settings.telegram.bot_token == "env_token"
    assert settings.ai.api_key == "env_key"
    assert settings.telegram.bot_username == "env_bot"
    assert "one" in settings.bot.trigger_words
    assert "two" in settings.bot.trigger_words
    assert "three" in settings.bot.trigger_words

def test_get_settings_loads_fallback_from_env():
    # Arrange
    os.environ["TELEGRAM_BOT_TOKEN"] = "token"
    os.environ["AI_API_KEY"] = "key"
    os.environ["FALLBACK_AI_API_KEY"] = "fallback_key"
    os.environ["FALLBACK_AI_MODEL"] = "fallback_model"
    os.environ["FALLBACK_AI_PROVIDER"] = "deepseek"

    # Act
    settings = get_settings()

    # Assert
    assert settings.fallback_ai is not None
    assert settings.fallback_ai.api_key == "fallback_key"
    assert settings.fallback_ai.model == "fallback_model"
    assert settings.fallback_ai.provider == "deepseek"
    assert settings.fallback_ai.base_url == "https://api.deepseek.com" # default for deepseek

def test_get_settings_no_fallback():
    # Arrange
    os.environ["TELEGRAM_BOT_TOKEN"] = "token"
    os.environ["AI_API_KEY"] = "key"
    if "FALLBACK_AI_API_KEY" in os.environ:
        del os.environ["FALLBACK_AI_API_KEY"]

    # Act
    settings = get_settings()

    # Assert
    assert settings.fallback_ai is None

def test_get_settings_missing_token_raises_error():
    # Arrange
    # Clear environment variable
    if "TELEGRAM_BOT_TOKEN" in os.environ:
        del os.environ["TELEGRAM_BOT_TOKEN"]

    # Act & Assert
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN is required"):
        get_settings()

