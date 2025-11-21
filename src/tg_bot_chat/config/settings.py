"""
Конфигурационные настройки для Telegram бота
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class TelegramConfig:
    """Конфигурация для Telegram бота"""

    bot_token: str
    """Токен бота Telegram"""

    bot_username: str | None = None
    """Имя пользователя бота"""


@dataclass
class AIConfig:
    """Конфигурация для AI API"""

    api_key: str
    """API ключ для AI провайдера"""

    model: str = "gpt-4o-mini"
    """Модель для использования"""

    provider: str = "openai"
    """AI провайдер (openai, deepseek)"""

    base_url: str | None = None
    """Базовый URL для API (для кастомных провайдеров)"""


@dataclass
class RedisConfig:
    """Конфигурация для Redis"""

    host: str = "localhost"
    """Хост Redis сервера"""

    port: int = 6379
    """Порт Redis сервера"""

    password: str | None = None
    """Пароль для Redis"""

    db: int = 0
    """Номер базы данных Redis"""


@dataclass
class BotConfig:
    """Основная конфигурация бота"""

    base_prompt: str
    """Базовый промпт для бота"""

    context_window_size: int = 50
    """Размер окна контекста сообщений"""

    trigger_words: list[str] | None = None
    """Ключевые слова для активации бота"""


@dataclass
class Settings:
    """Все настройки приложения"""

    telegram: TelegramConfig
    """Настройки Telegram"""

    ai: AIConfig
    """Настройки AI провайдера"""

    redis: RedisConfig
    """Настройки Redis"""

    bot: BotConfig
    """Настройки бота"""


def get_settings() -> Settings:
    """Загрузка настроек из переменных окружения"""

    # Проверка обязательных переменных
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    ai_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not ai_api_key:
        raise ValueError("AI_API_KEY or OPENAI_API_KEY is required")

    # Определение провайдера AI
    ai_provider = os.getenv("AI_PROVIDER", "openai").lower()

    # Настройки для разных провайдеров
    if ai_provider == "deepseek":
        default_model = "deepseek-chat"
        default_base_url = "https://api.deepseek.com"
    elif ai_provider == "openrouter":
        default_model = "deepseek/deepseek-chat"
        default_base_url = "https://openrouter.ai/api/v1"
    else:  # openai
        default_model = "gpt-4o-mini"
        default_base_url = None

    base_prompt = os.getenv(
        "BASE_PROMPT",
        "You are a helpful assistant in a Telegram chat. You maintain context and respond when mentioned. Always respond naturally without including your username.",
    )

    # Загрузка trigger words из .env
    trigger_words_str = os.getenv(
        "TRIGGER_WORDS", "бот,bot,помощь,help,вопрос,question,вика"
    )
    trigger_words = [
        word.strip() for word in trigger_words_str.split(",") if word.strip()
    ]

    return Settings(
        telegram=TelegramConfig(
            bot_token=bot_token, bot_username=os.getenv("BOT_USERNAME")
        ),
        ai=AIConfig(
            api_key=ai_api_key,
            model=os.getenv("AI_MODEL") or os.getenv("OPENAI_MODEL", default_model),
            provider=ai_provider,
            base_url=os.getenv("AI_BASE_URL", default_base_url),
        ),
        redis=RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
        ),
        bot=BotConfig(
            base_prompt=base_prompt,
            context_window_size=int(os.getenv("CONTEXT_WINDOW_SIZE", "50")),
            trigger_words=trigger_words,
        ),
    )
