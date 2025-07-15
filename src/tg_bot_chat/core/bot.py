"""
Основной класс Telegram бота
"""

import logging
import asyncio
from typing import NoReturn

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from ..config.settings import Settings, get_settings
from ..handlers.message_handler import MessageHandler as BotMessageHandler


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Основной класс Telegram бота"""
    
    def __init__(self, settings: Settings):
        """
        Инициализация бота
        
        Args:
            settings: Настройки приложения
        """
        self.settings = settings
        self.application = Application.builder().token(settings.telegram.bot_token).build()
        self.message_handler = BotMessageHandler(settings)
        
        # Настройка обработчиков
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Настройка обработчиков сообщений и команд"""
        
        # Обработчики команд
        self.application.add_handler(
            CommandHandler("start", self.message_handler.handle_start_command)
        )
        self.application.add_handler(
            CommandHandler("clear", self.message_handler.handle_clear_command)
        )
        self.application.add_handler(
            CommandHandler("status", self.message_handler.handle_status_command)
        )
        
        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.message_handler.handle_message
            )
        )
        
        logger.info("Handlers configured successfully")
    
    async def start(self) -> NoReturn:
        """
        Запуск бота
        
        Raises:
            Exception: При ошибке запуска
        """
        try:
            logger.info("Starting Telegram bot...")
            logger.info(f"Bot username: {self.settings.telegram.bot_username}")
            logger.info(f"AI model: {self.settings.ai.model} ({self.settings.ai.provider})")
            logger.info(f"Context window size: {self.settings.bot.context_window_size}")
            
            # Запуск приложения (v21+ API)
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Bot started successfully and polling for updates")
            
            # Ожидание завершения (v21+ API)
            # Бот будет работать до получения сигнала остановки
            await asyncio.sleep(float('inf'))
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            # Остановка приложения
            await self.application.stop()
            logger.info("Bot stopped")
    
    async def stop(self) -> None:
        """Остановка бота"""
        try:
            if self.application.updater.running:
                await self.application.updater.stop()
                logger.info("Bot updater stopped")
            await self.application.stop()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")


async def main() -> None:
    """Основная функция запуска бота"""
    try:
        # Загрузка настроек
        settings = get_settings()
        
        # Создание и запуск бота
        bot = TelegramBot(settings)
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 