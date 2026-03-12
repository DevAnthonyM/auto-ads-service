"""
Telegram Bot entry point.
"""

from loguru import logger
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import settings
from .handlers import start_handler, search_handler, latest_handler


def main():
    logger.info("=" * 50)
    logger.info("Auto-Ads Telegram Bot starting...")
    logger.info("=" * 50)

    if not settings.anthropic_api_key or settings.anthropic_api_key == "your-anthropic-api-key":
        logger.warning("No LLM API key configured — running in keyword-fallback mode")
        logger.info("LLM Mode: Keyword-based fallback (set ANTHROPIC_API_KEY for DeepSeek LLM)")
    else:
        logger.info("LLM Mode: DeepSeek API (Function Calling)")

    if not settings.telegram_bot_token or settings.telegram_bot_token == "your-telegram-bot-token":
        logger.error("TELEGRAM_BOT_TOKEN is not set — bot cannot start")
        return

    app = Application.builder().token(settings.telegram_bot_token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", start_handler))
    app.add_handler(CommandHandler("latest", latest_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    logger.info("Bot is now polling for messages...")
    # run_polling manages its own event loop — do NOT wrap in asyncio.run()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()