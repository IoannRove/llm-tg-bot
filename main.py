#!/usr/bin/env python3
"""
Точка входа для Telegram бота с контекстом чата
"""

import asyncio
import sys
from src.tg_bot_chat.core.bot import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1) 