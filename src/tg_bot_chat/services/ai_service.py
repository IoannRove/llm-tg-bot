"""
Сервис для работы с OpenAI API
"""

from openai import AsyncOpenAI
from dataclasses import dataclass

from ..config.settings import AIConfig, BotConfig
from .context_manager import ChatMessage


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
    
    def __init__(self, ai_config: AIConfig, bot_config: BotConfig):
        """
        Инициализация AI сервиса
        
        Args:
            ai_config: Конфигурация AI провайдера
            bot_config: Конфигурация бота
        """
        # Создание асинхронного клиента с кастомным base_url для DeepSeek
        client_kwargs = {"api_key": ai_config.api_key}
        if ai_config.base_url:
            client_kwargs["base_url"] = ai_config.base_url
            
        self.client = AsyncOpenAI(**client_kwargs)
        self.model = ai_config.model
        self.provider = ai_config.provider
        self.base_prompt = bot_config.base_prompt
    
    def _format_context_messages(self, context: list[ChatMessage], bot_username: str | None = None) -> list[dict]:
        """
        Форматирование контекста для OpenAI API
        
        Args:
            context: Контекст сообщений
            bot_username: Имя пользователя бота для фильтрации
            
        Returns:
            Форматированные сообщения для API
        """
        messages = [
            {
                "role": "system",
                "content": f"{self.base_prompt}\n\nIMPORTANT: When responding, do NOT include your username in your response. Simply provide a natural response without identifying yourself by name."
            }
        ]
        
        for msg in context:
            # Проверяем, является ли сообщение от бота
            is_bot_message = (
                bot_username and 
                msg.username and 
                msg.username.lower() == bot_username.lower().strip('@')
            )
            
            if is_bot_message:
                # Сообщения бота форматируем как assistant без username
                messages.append({
                    "role": "assistant",
                    "content": msg.message
                })
            else:
                # Сообщения пользователей форматируем с username
                username = msg.username or f"user_{msg.user_id}"
                content = f"{username}: {msg.message}"
                messages.append({
                    "role": "user",
                    "content": content
                })
        
        return messages
    
    async def generate_response(
        self, 
        context: list[ChatMessage], 
        current_message: str,
        mentioned_username: str | None = None
    ) -> AIResponse:
        """
        Генерация ответа на основе контекста
        
        Args:
            context: Контекст предыдущих сообщений
            current_message: Текущее сообщение
            mentioned_username: Имя упомянутого пользователя (бота)
            
        Returns:
            Ответ от AI модели
        """
        try:
            # Формирование сообщений для API
            messages = self._format_context_messages(context, mentioned_username)
            
            # Добавление текущего сообщения (без упоминания username бота)
            messages.append({
                "role": "user", 
                "content": current_message
            })
            
            # Вызов OpenAI API (v1.0+ синтаксис)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Извлечение ответа
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            return AIResponse(
                content=content or "Извините, не могу сформировать ответ.",
                tokens_used=tokens_used,
                model_used=self.model
            )
            
        except Exception as e:
            return AIResponse(
                content=f"Произошла ошибка при обработке запроса: {str(e)}"
            )
    
    def should_respond_to_message(self, message: str, bot_username: str | None = None) -> bool:
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
        
        # Проверяем ключевые слова для активации
        trigger_words = ["бот", "bot", "помощь", "help", "вопрос", "question", "вика"]
        
        for word in trigger_words:
            if word in message_lower:
                return True
        
        return False
