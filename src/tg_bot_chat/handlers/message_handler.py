"""
Обработчик сообщений для Telegram бота
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from ..config.settings import Settings
from ..services.ai_service import AIService
from ..services.context_manager import ChatMessage, ContextManager

logger = logging.getLogger(__name__)


class MessageHandler:
    """Обработчик сообщений Telegram"""

    def __init__(self, settings: Settings):
        """
        Инициализация обработчика сообщений

        Args:
            settings: Настройки приложения
        """
        self.settings = settings
        self.context_manager = ContextManager(settings.redis)
        self.ai_service = AIService(settings.ai, settings.bot)

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обработка входящего сообщения

        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.message or not update.message.text:
            return

        message = update.message
        chat_id = message.chat_id
        user_id = message.from_user.id

        # Создание объекта сообщения
        chat_message = ChatMessage(
            user_id=user_id,
            username=message.from_user.username,
            message=message.text,
            timestamp=datetime.now(),
            message_id=message.message_id,
        )

        # Добавление сообщения в общий контекст чата
        self.context_manager.add_message(chat_id, chat_message)

        # Добавление сообщения в пользовательский контекст
        self.context_manager.add_user_message(chat_id, user_id, chat_message)

        # Обрезка контекста до максимального размера
        self.context_manager.trim_context(
            chat_id, self.settings.bot.context_window_size
        )

        # Проверка, нужно ли отвечать на сообщение
        should_respond = self.ai_service.should_respond_to_message(
            message.text, self.settings.telegram.bot_username
        )

        if should_respond:
            await self._generate_and_send_response(
                chat_id, user_id, message.text, context
            )

    async def _generate_and_send_response(
        self,
        chat_id: int,
        user_id: int,
        message_text: str,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """
        Генерация и отправка ответа

        Args:
            chat_id: ID чата
            user_id: ID пользователя
            message_text: Текст сообщения
            context: Контекст обработчика
        """
        try:
            # Получение общего контекста чата
            chat_context = self.context_manager.get_context(
                chat_id, self.settings.bot.context_window_size
            )

            # Получение контекста пользователя
            user_context = self.context_manager.get_user_context(
                chat_id, user_id, limit=20
            )

            # Генерация ответа с учетом общего контекста чата и контекста пользователя
            ai_response = await self.ai_service.generate_response(
                chat_context,
                message_text,
                self.settings.telegram.bot_username,
                user_context,
            )

            # Отправка ответа
            await context.bot.send_message(
                chat_id=chat_id, text=ai_response.content, reply_to_message_id=None
            )

            # Добавление ответа бота в общий контекст
            bot_message = ChatMessage(
                user_id=context.bot.id,
                username=self.settings.telegram.bot_username,
                message=ai_response.content,
                timestamp=datetime.now(),
                message_id=0,  # Будет обновлено после отправки
            )

            self.context_manager.add_message(chat_id, bot_message)

            # Добавление ответа бота в пользовательский контекст
            self.context_manager.add_user_message(chat_id, user_id, bot_message)

            # Логирование с указанием пользователя
            logger.info(
                f"Responded to user {user_id} in chat {chat_id} with {ai_response.tokens_used} tokens"
            )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Извините, произошла ошибка при обработке вашего сообщения.",
            )

    async def handle_start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обработка команды /start

        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.message:
            return

        trigger_words_list = (
            ", ".join(self.settings.bot.trigger_words)
            if self.settings.bot.trigger_words
            else "не заданы"
        )

        welcome_message = f"""
Привет! Я бот с контекстом чата.

Я могу:
• Отвечать на сообщения когда меня упоминают
• Поддерживать контекст разговора для каждого пользователя
• Отвечать на ключевые слова: {trigger_words_list}

Текущие настройки:
• Размер контекста: {self.settings.bot.context_window_size} сообщений
• Модель: {self.settings.ai.model} ({self.settings.ai.provider})

Просто упомяните меня в сообщении или используйте ключевые слова!
        """

        await update.message.reply_text(welcome_message)

    async def handle_clear_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обработка команды /clear для очистки контекста

        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.message:
            return

        chat_id = update.message.chat_id
        self.context_manager.clear_context(chat_id)

        await update.message.reply_text(
            "Контекст чата очищен! Начинаем с чистого листа."
        )

    async def handle_status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обработка команды /status для показа статуса контекста

        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.message:
            return

        chat_id = update.message.chat_id
        context_size = self.context_manager.get_context_size(chat_id)

        status_message = f"""
📊 Статус контекста чата:

• Сообщений в контексте: {context_size}
• Максимальный размер: {self.settings.bot.context_window_size}
• Модель: {self.settings.ai.model} ({self.settings.ai.provider})
• Базовый промпт: {self.settings.bot.base_prompt[:100]}...

Команды:
/start - Приветствие
/clear - Очистить контекст
/status - Показать статус
        """

        await update.message.reply_text(status_message)
