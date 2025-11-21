from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from tg_bot_chat.services.ai_service import AIService, AIResponse
from tg_bot_chat.services.context_manager import ChatMessage
from datetime import datetime

@pytest.fixture
def ai_service(mock_settings, mock_ai_client):
    # Arrange
    with patch("tg_bot_chat.services.ai_service.AsyncOpenAI", return_value=mock_ai_client):
        service = AIService(mock_settings.ai, mock_settings.bot)
        # Force set client because __init__ creates a new one
        service.client = mock_ai_client
        return service

@pytest.mark.asyncio
async def test_generate_response_success(ai_service, mock_ai_client):
    # Arrange
    context = [
        ChatMessage(
            user_id=1, 
            username="user", 
            message="hi", 
            timestamp=datetime.now(), 
            message_id=1
        )
    ]
    current_message = "how are you?"
    
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="I am fine"))]
    mock_response.usage.total_tokens = 50
    mock_ai_client.chat.completions.create.return_value = mock_response

    # Act
    response = await ai_service.generate_response(context, current_message)

    # Assert
    assert isinstance(response, AIResponse)
    assert response.content == "I am fine"
    assert response.tokens_used == 50
    mock_ai_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_error(ai_service, mock_ai_client):
    # Arrange
    context = []
    current_message = "test"
    mock_ai_client.chat.completions.create.side_effect = Exception("API Error")

    # Act
    response = await ai_service.generate_response(context, current_message)

    # Assert
    assert "Произошла ошибка" in response.content

def test_should_respond_to_message_mention(ai_service):
    # Arrange
    message = "hello @test_bot"
    bot_username = "test_bot"

    # Act
    result = ai_service.should_respond_to_message(message, bot_username)

    # Assert
    assert result is True

def test_should_respond_to_message_trigger_word(ai_service):
    # Arrange
    message = "hey bot help me"
    # trigger words in mock_settings are ["test", "bot"]

    # Act
    result = ai_service.should_respond_to_message(message, bot_username="other_bot")

    # Assert
    assert result is True

def test_should_respond_to_message_no_trigger(ai_service):
    # Arrange
    message = "just random text"
    
    # Act
    result = ai_service.should_respond_to_message(message, bot_username="test_bot")

    # Assert
    assert result is False

@pytest.mark.asyncio
async def test_generate_response_with_user_context(ai_service, mock_ai_client):
    # Arrange
    context = []
    user_context = [
        ChatMessage(
            user_id=1,
            username="user",
            message="my context",
            timestamp=datetime.now(),
            message_id=1
        )
    ]
    current_message = "hello"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="response"))]
    mock_ai_client.chat.completions.create.return_value = mock_response

    # Act
    await ai_service.generate_response(context, current_message, user_context=user_context)

    # Assert
    call_args = mock_ai_client.chat.completions.create.call_args
    messages = call_args[1]['messages']
    system_msg = messages[0]['content']
    assert "Relevant user history" in system_msg
    assert "my context" in system_msg

