"""
Сервис для управления контекстом чата
"""

import json
from dataclasses import dataclass
from datetime import datetime

import redis

from ..config.settings import RedisConfig


@dataclass
class ChatMessage:
    """Сообщение в чате"""

    user_id: int
    """ID пользователя"""

    username: str | None
    """Имя пользователя"""

    message: str
    """Текст сообщения"""

    timestamp: datetime
    """Время сообщения"""

    message_id: int
    """ID сообщения"""


class ContextManager:
    """Менеджер контекста чата"""

    def __init__(self, redis_config: RedisConfig):
        """
        Инициализация менеджера контекста

        Args:
            redis_config: Конфигурация Redis
        """
        self.redis_client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            db=redis_config.db,
            decode_responses=True,
        )
        self.context_key_prefix = "chat_context"
        self.user_context_key_prefix = "user_context"

    def _get_context_key(self, chat_id: int) -> str:
        """Получение ключа для контекста чата"""
        return f"{self.context_key_prefix}:{chat_id}"

    def _get_user_context_key(self, chat_id: int, user_id: int) -> str:
        """
        Получение ключа для пользовательского контекста

        Args:
            chat_id: ID чата
            user_id: ID пользователя

        Returns:
            Ключ для хранения пользовательского контекста
        """
        return f"{self.user_context_key_prefix}:{chat_id}:{user_id}"

    def add_message(self, chat_id: int, message: ChatMessage) -> None:
        """
        Добавление сообщения в контекст

        Args:
            chat_id: ID чата
            message: Сообщение для добавления
        """
        key = self._get_context_key(chat_id)

        # Сериализация сообщения
        message_data = {
            "user_id": message.user_id,
            "username": message.username,
            "message": message.message,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id,
        }

        # Добавление в список Redis
        self.redis_client.lpush(key, json.dumps(message_data))

        # Установка времени жизни ключа (24 часа)
        self.redis_client.expire(key, 24 * 60 * 60)

    def get_context(self, chat_id: int, limit: int = 50) -> list[ChatMessage]:
        """
        Получение контекста чата

        Args:
            chat_id: ID чата
            limit: Максимальное количество сообщений

        Returns:
            Список сообщений из контекста
        """
        key = self._get_context_key(chat_id)

        # Получение сообщений из Redis
        messages_data = self.redis_client.lrange(key, 0, limit - 1)

        messages = []
        for message_json in messages_data:
            try:
                message_data = json.loads(message_json)
                message = ChatMessage(
                    user_id=message_data["user_id"],
                    username=message_data.get("username"),
                    message=message_data["message"],
                    timestamp=datetime.fromisoformat(message_data["timestamp"]),
                    message_id=message_data["message_id"],
                )
                messages.append(message)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        # Возвращаем в хронологическом порядке (самые старые сначала)
        return list(reversed(messages))

    def clear_context(self, chat_id: int) -> None:
        """
        Очистка контекста чата

        Args:
            chat_id: ID чата
        """
        key = self._get_context_key(chat_id)
        self.redis_client.delete(key)

    def get_context_size(self, chat_id: int) -> int:
        """
        Получение размера контекста

        Args:
            chat_id: ID чата

        Returns:
            Количество сообщений в контексте
        """
        key = self._get_context_key(chat_id)
        return self.redis_client.llen(key)

    def trim_context(self, chat_id: int, max_size: int) -> None:
        """
        Обрезка контекста до максимального размера

        Args:
            chat_id: ID чата
            max_size: Максимальный размер контекста
        """
        key = self._get_context_key(chat_id)
        self.redis_client.ltrim(key, 0, max_size - 1)

    def get_user_context(
        self, chat_id: int, user_id: int, limit: int = 20
    ) -> list[ChatMessage]:
        """
        Получение контекста сообщений конкретного пользователя

        Args:
            chat_id: ID чата
            user_id: ID пользователя
            limit: Максимальное количество сообщений

        Returns:
            Список сообщений пользователя из контекста
        """
        key = self._get_user_context_key(chat_id, user_id)

        # Получение сообщений из Redis
        messages_data = self.redis_client.lrange(key, 0, limit - 1)

        messages = []
        for message_json in messages_data:
            try:
                message_data = json.loads(message_json)
                message = ChatMessage(
                    user_id=message_data["user_id"],
                    username=message_data.get("username"),
                    message=message_data["message"],
                    timestamp=datetime.fromisoformat(message_data["timestamp"]),
                    message_id=message_data["message_id"],
                )
                messages.append(message)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        # Возвращаем в хронологическом порядке (самые старые сначала)
        return list(reversed(messages))

    def add_user_message(
        self, chat_id: int, user_id: int, message: ChatMessage
    ) -> None:
        """
        Добавление сообщения в пользовательский контекст

        Args:
            chat_id: ID чата
            user_id: ID пользователя
            message: Сообщение для добавления
        """
        key = self._get_user_context_key(chat_id, user_id)

        # Сериализация сообщения
        message_data = {
            "user_id": message.user_id,
            "username": message.username,
            "message": message.message,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id,
        }

        # Добавление в список Redis
        self.redis_client.lpush(key, json.dumps(message_data))

        # Установка времени жизни ключа (24 часа)
        self.redis_client.expire(key, 24 * 60 * 60)

    def get_chat_users(self, chat_id: int) -> list[int]:
        """
        Получение списка пользователей в чате

        Args:
            chat_id: ID чата

        Returns:
            Список ID пользователей
        """
        # Получаем все ключи пользовательских контекстов для данного чата
        pattern = f"{self.user_context_key_prefix}:{chat_id}:*"
        keys = self.redis_client.scan_iter(match=pattern)

        user_ids = []
        for key in keys:
            # Извлекаем user_id из ключа
            parts = key.split(":")
            if len(parts) == 3:
                try:
                    user_ids.append(int(parts[2]))
                except ValueError:
                    continue

        return user_ids
