"""
Сервис для работы с OpenAI API
"""

import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from ..config.settings import AIConfig, BotConfig
from .context_manager import ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Ответ от AI модели"""

    content: str
    """Содержимое ответа"""

    tokens_used: int | None = None
    """Количество использованных токенов"""

    model_used: str | None = None
    """Использованная модель"""


class AIService:
    """Сервис для работы с AI"""

    def __init__(
        self,
        ai_config: AIConfig,
        bot_config: BotConfig,
        fallback_ai_config: AIConfig | None = None,
    ):
        """
        Инициализация AI сервиса

        Args:
            ai_config: Конфигурация AI провайдера
            bot_config: Конфигурация бота
            fallback_ai_config: Конфигурация резервного AI провайдера
        """
        # Создание основного клиента
        self.client = self._create_client(ai_config)
        self.model = ai_config.model
        self.provider = ai_config.provider

        # Настройка резервного клиента
        self.fallback_client = None
        self.fallback_model = None
        if fallback_ai_config:
            self.fallback_client = self._create_client(fallback_ai_config)
            self.fallback_model = fallback_ai_config.model

        self.base_prompt = bot_config.base_prompt
        self.trigger_words = bot_config.trigger_words or []

    def _create_client(self, config: AIConfig) -> AsyncOpenAI:
        """Создание клиента OpenAI"""
        client_kwargs = {"api_key": config.api_key}
        if config.base_url:
            client_kwargs["base_url"] = config.base_url
        return AsyncOpenAI(**client_kwargs)

    def _format_context_messages(
        self,
        context: list[ChatMessage],
        bot_username: str | None = None,
        user_context: list[ChatMessage] | None = None,
    ) -> list[dict]:
        """
        Форматирование контекста для OpenAI API

        Args:
            context: Контекст сообщений
            bot_username: Имя пользователя бота для фильтрации
            user_context: Контекст сообщений конкретного пользователя

        Returns:
            Форматированные сообщения для API
        """
        system_content = f"{self.base_prompt}\n\nIMPORTANT: When responding, do NOT include your username in your response. Simply provide a natural response without identifying yourself by name."

        if user_context:
            user_history_text = "\n".join(
                [f"{msg.username or 'User'}: {msg.message}" for msg in user_context]
            )
            system_content += f"\n\nRelevant user history:\n{user_history_text}"

        messages = [
            {
                "role": "system",
                "content": system_content,
            }
        ]

        for msg in context:
            # Проверяем, является ли сообщение от бота
            is_bot_message = (
                bot_username
                and msg.username
                and msg.username.lower() == bot_username.lower().strip("@")
            )

            if is_bot_message:
                # Сообщения бота форматируем как assistant без username
                messages.append({"role": "assistant", "content": msg.message})
            else:
                # Сообщения пользователей форматируем с username
                username = msg.username or f"user_{msg.user_id}"
                content = f"{username}: {msg.message}"
                messages.append({"role": "user", "content": content})

        return messages

    async def generate_response(
        self,
        context: list[ChatMessage],
        current_message: str,
        mentioned_username: str | None = None,
        user_context: list[ChatMessage] | None = None,
    ) -> AIResponse:
        """
        Генерация ответа на основе контекста

        Args:
            context: Контекст предыдущих сообщений
            current_message: Текущее сообщение
            mentioned_username: Имя упомянутого пользователя (бота)
            user_context: Контекст сообщений конкретного пользователя

        Returns:
            Ответ от AI модели
        """
        try:
            # Формирование сообщений для API
            messages = self._format_context_messages(
                context, mentioned_username, user_context
            )

            # Проверяем, есть ли уже текущее сообщение в конце контекста
            # Если нет, добавляем его
            last_message_content = (
                messages[-1]["content"]
                if messages and "content" in messages[-1]
                else ""
            )
            if current_message not in last_message_content:
                messages.append({"role": "user", "content": current_message})

            # Вызов OpenAI API (v1.0+ синтаксис)
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                )
                model_used = self.model
            except Exception as e:
                if not self.fallback_client:
                    raise e

                logger.warning(
                    f"Primary AI provider failed: {e}. Switching to fallback model: {self.fallback_model}"
                )

                # Попытка использования fallback
                response = await self.fallback_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                )
                model_used = self.fallback_model

            # Извлечение ответа
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None

            return AIResponse(
                content=content or "Извините, не могу сформировать ответ.",
                tokens_used=tokens_used,
                model_used=model_used,
            )

        except Exception as e:
            return AIResponse(
                content=f"Произошла ошибка при обработке запроса: {str(e)}"
            )

    def should_respond_to_message(
        self, message: str, bot_username: str | None = None
    ) -> bool:
        """
        Проверка, должен ли бот отвечать на сообщение

        Args:
            message: Текст сообщения
            bot_username: Имя пользователя бота

        Returns:
            True, если бот должен ответить
        """
        message_lower = message.lower()

        # Проверяем упоминание по имени пользователя
        if bot_username and bot_username.lower() in message_lower:
            return True

        # Проверяем ключевые слова для активации из конфигурации
        for word in self.trigger_words:
            if word.lower() in message_lower:
                return True

        return False
