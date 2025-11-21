from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from tg_bot_chat.handlers.message_handler import MessageHandler
from tg_bot_chat.services.ai_service import AIResponse

@pytest.fixture
def message_handler(mock_settings, mock_redis):
    # Arrange
    with patch("tg_bot_chat.services.context_manager.redis.Redis", return_value=mock_redis):
        handler = MessageHandler(mock_settings)
        # Mock internal services to isolate handler logic
        handler.ai_service = MagicMock() # Use MagicMock as base, as it has mixed sync/async methods
        handler.ai_service.generate_response = AsyncMock() # Async method
        handler.ai_service.should_respond_to_message = MagicMock() # Sync method
        
        handler.context_manager = MagicMock()
        return handler

@pytest.mark.asyncio
async def test_handle_message_no_response_needed(message_handler):
    # Arrange
    update = MagicMock()
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    update.message.text = "just text"
    update.message.chat_id = 123
    update.message.from_user.id = 1
    update.message.from_user.username = "user"
    update.message.message_id = 100

    message_handler.ai_service.should_respond_to_message.return_value = False

    # Act
    await message_handler.handle_message(update, context)

    # Assert
    message_handler.context_manager.add_message.assert_called() # Should still save message
    message_handler.ai_service.generate_response.assert_not_called()

@pytest.mark.asyncio
async def test_handle_message_response_needed(message_handler):
    # Arrange
    update = MagicMock()
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    update.message.text = "hey bot"
    update.message.chat_id = 123
    update.message.from_user.id = 1
    update.message.from_user.username = "user"
    update.message.message_id = 100

    message_handler.ai_service.should_respond_to_message.return_value = True
    
    # Mock AI response
    ai_resp = AIResponse(content="Hello there", tokens_used=10, model_used="gpt-4")
    message_handler.ai_service.generate_response.return_value = ai_resp
    
    # Mock context return
    message_handler.context_manager.get_context.return_value = []
    message_handler.context_manager.get_user_context.return_value = []

    # Act
    await message_handler.handle_message(update, context)

    # Assert
    message_handler.ai_service.generate_response.assert_called_once()
    context.bot.send_message.assert_called_once_with(
        chat_id=123,
        text="Hello there",
        reply_to_message_id=None
    )
    # Verify bot response added to context
    # First call is user message, second call is bot response
    assert message_handler.context_manager.add_message.call_count == 2

@pytest.mark.asyncio
async def test_handle_start_command(message_handler):
    # Arrange
    update = MagicMock()
    context = MagicMock()
    update.message.reply_text = AsyncMock()

    # Act
    await message_handler.handle_start_command(update, context)

    # Assert
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Привет!" in call_args[0][0]

@pytest.mark.asyncio
async def test_handle_clear_command(message_handler):
    # Arrange
    update = MagicMock()
    context = MagicMock()
    update.message.chat_id = 123
    update.message.reply_text = AsyncMock()

    # Act
    await message_handler.handle_clear_command(update, context)

    # Assert
    message_handler.context_manager.clear_context.assert_called_once_with(123)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_status_command(message_handler):
    # Arrange
    update = MagicMock()
    context = MagicMock()
    update.message.chat_id = 123
    update.message.reply_text = AsyncMock()
    
    message_handler.context_manager.get_context_size.return_value = 5

    # Act
    await message_handler.handle_status_command(update, context)

    # Assert
    message_handler.context_manager.get_context_size.assert_called_once_with(123)
    update.message.reply_text.assert_called_once()

