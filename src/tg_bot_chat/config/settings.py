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

    fallback_ai: AIConfig | None = None
    """Настройки резервного AI провайдера"""


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
    def get_provider_config(provider: str) -> tuple[str, str | None]:
        if provider == "deepseek":
            return "deepseek-chat", "https://api.deepseek.com"
        elif provider == "openrouter":
            return "deepseek/deepseek-chat", "https://openrouter.ai/api/v1"
        else:  # openai
            return "gpt-4o-mini", None

    default_model, default_base_url = get_provider_config(ai_provider)

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

    # Настройка основного AI
    ai_config = AIConfig(
        api_key=ai_api_key,
        model=os.getenv("AI_MODEL") or os.getenv("OPENAI_MODEL", default_model),
        provider=ai_provider,
        base_url=os.getenv("AI_BASE_URL", default_base_url),
    )

    # Настройка резервного AI (если есть ключ)
    fallback_ai_config = None
    fallback_api_key = os.getenv("FALLBACK_AI_API_KEY")

    if fallback_api_key:
        fallback_provider = os.getenv("FALLBACK_AI_PROVIDER", "openai").lower()
        fb_default_model, fb_default_base_url = get_provider_config(fallback_provider)

        fallback_ai_config = AIConfig(
            api_key=fallback_api_key,
            model=os.getenv("FALLBACK_AI_MODEL", fb_default_model),
            provider=fallback_provider,
            base_url=os.getenv("FALLBACK_AI_BASE_URL", fb_default_base_url),
        )

    return Settings(
        telegram=TelegramConfig(
            bot_token=bot_token, bot_username=os.getenv("BOT_USERNAME")
        ),
        ai=ai_config,
        fallback_ai=fallback_ai_config,
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
