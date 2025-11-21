# Telegram Bot with Chat Context

A Telegram bot that maintains chat context and responds when mentioned, built with Python 3.13, uv package manager, and Docker.

## Features

- 🤖 **Context-aware responses**: Maintains chat history and context
- 👤 **User-specific context tracking**: Tracks conversation history per user
- 🎯 **Smart mention detection**: Responds when mentioned or triggered by keywords
- 🔧 **Configurable trigger words**: Customize keywords that activate the bot via .env
- 🎪 **Customizable base prompt**: Configure bot personality and behavior
- 🔄 **Redis-based persistence**: Chat context stored in Redis
- 🐳 **Docker-ready**: Full containerization with Docker Compose
- 📊 **Status monitoring**: Built-in commands for context management
- 🚀 **Modern Python**: Built with Python 3.13 and uv package manager
- 🧠 **Multiple AI providers**: Supports OpenAI, DeepSeek, and OpenRouter
- 💬 **Multi-chat support**: Works in any chat where the bot is added

## Prerequisites

- Python 3.13+
- uv package manager
- Docker and Docker Compose (for containerized deployment)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- AI API Key (OpenAI or DeepSeek)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd tg-bot-chat
```

### 2. Environment Configuration

Copy and configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
AI_API_KEY=your_api_key_here

# AI Provider Configuration (choose one)
AI_PROVIDER=openai                    # OpenAI (default)
# AI_PROVIDER=deepseek               # DeepSeek direct
# AI_PROVIDER=openrouter             # OpenRouter (recommended for DeepSeek)

# Model Configuration
AI_MODEL=gpt-4o-mini                 # OpenAI model
# AI_MODEL=deepseek-chat             # DeepSeek direct
# AI_MODEL=deepseek/deepseek-chat    # DeepSeek via OpenRouter
# AI_MODEL=deepseek/deepseek-coder   # DeepSeek Coder via OpenRouter

# Trigger Words (comma-separated list)
TRIGGER_WORDS=бот,bot,помощь,help,вопрос,question,вика

# Optional (with defaults)
BOT_USERNAME=@your_bot_username
BASE_PROMPT=You are a helpful assistant in a Telegram chat. You maintain context and respond when mentioned.
CONTEXT_WINDOW_SIZE=50
```

### 3. Run with Docker (Recommended)

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### 4. Run Locally (Development)

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .

# Start Redis (required)
docker run -d -p 6379:6379 redis:7-alpine

# Run the bot
python main.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot information |
| `/status` | Show current context status and settings |
| `/clear` | Clear chat context (start fresh) |

## Bot Triggers

The bot responds to messages containing:

- Direct mentions of the bot username (e.g., `@your_bot_username`)
- Configurable trigger words (set in `.env` via `TRIGGER_WORDS`)
- Default keywords: `бот`, `bot`, `помощь`, `help`, `вопрос`, `question`, `вика`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | **Required** |
| `AI_API_KEY` | API key for AI provider | **Required** |
| `AI_PROVIDER` | AI provider (openai, deepseek, openrouter) | `openai` |
| `AI_MODEL` | AI model to use | `gpt-4o-mini` |
| `AI_BASE_URL` | Custom API base URL | Provider default |
| `REDIS_HOST` | Redis server host | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_PASSWORD` | Redis password | None |
| `REDIS_DB` | Redis database number | `0` |
| `BASE_PROMPT` | System prompt for AI | Default assistant prompt |
| `CONTEXT_WINDOW_SIZE` | Max messages in context | `50` |
| `BOT_USERNAME` | Bot username for mentions | Optional |

### Base Prompt Customization

Customize your bot's personality by modifying the `BASE_PROMPT` environment variable:

```env
BASE_PROMPT=You are a helpful programming assistant specializing in Python. You maintain context of our conversation and provide code examples when appropriate.
```

### Using DeepSeek via OpenRouter (Recommended)

To use DeepSeek through OpenRouter:

1. **Get an OpenRouter API key** from [openrouter.ai](https://openrouter.ai)
2. **Configure your `.env` file**:
   ```env
   AI_PROVIDER=openrouter
   AI_API_KEY=your_openrouter_api_key_here
   AI_MODEL=deepseek/deepseek-chat
   # or AI_MODEL=deepseek/deepseek-coder for coding tasks
   ```

**Why OpenRouter?**
- ✅ More reliable than direct DeepSeek API
- ✅ Better rate limiting and error handling
- ✅ Access to multiple models through one API
- ✅ Competitive pricing

### Multi-Chat Support

The bot works in **any chat** where it's added - no configuration needed! It will:
- Maintain separate context for each chat
- Respond to mentions and keywords in all chats
- Store context separately for each conversation

## Architecture

```
tg-bot-chat/
├── src/tg_bot_chat/
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── core/
│   │   └── bot.py              # Main bot application
│   ├── handlers/
│   │   └── message_handler.py  # Message processing
│   └── services/
│       ├── context_manager.py  # Chat context management
│       └── ai_service.py       # OpenAI integration
├── main.py                     # Application entry point
├── pyproject.toml              # Project configuration
├── Dockerfile                  # Container configuration
└── docker-compose.yml          # Multi-service orchestration
```

## Development

### Project Structure

- **Configuration**: Environment-based settings with validation
- **Context Management**: Redis-backed chat history with size limits
- **AI Integration**: OpenAI API with context-aware responses
- **Message Handling**: Telegram webhook processing with filters
- **Docker Support**: Full containerization with health checks

### Code Style

The project uses:
- Type hints throughout (following user rules: use `list` instead of `List`)
- Russian comments for attributes (following user rules)
- Dataclasses for configuration
- Async/await for all I/O operations

### Adding Features

1. **New Commands**: Add handlers in `MessageHandler` class
2. **Custom Triggers**: Modify `should_respond_to_message` in `AIService`
3. **Context Storage**: Extend `ContextManager` for new data types
4. **AI Models**: Update `OpenAIConfig` for different providers

## Troubleshooting

### Common Issues

1. **Bot Token Invalid**
   ```bash
   # Check token format
   echo $TELEGRAM_BOT_TOKEN | grep -E '^[0-9]+:[A-Za-z0-9_-]+$'
   ```

2. **Redis Connection Failed**
   ```bash
   # Test Redis connection
   docker-compose exec redis redis-cli ping
   ```

3. **OpenAI API Issues**
   ```bash
   # Verify API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

4. **Context Not Persisting**
   ```bash
   # Check Redis data
   docker-compose exec redis redis-cli keys "*"
   ```

### Logs

```bash
# View all logs
docker-compose logs

# Follow bot logs
docker-compose logs -f bot

# Follow Redis logs
docker-compose logs -f redis
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with details and logs 