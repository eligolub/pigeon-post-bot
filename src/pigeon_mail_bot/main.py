import asyncio
import logging

from aiogram import Bot, Dispatcher

from .app import build_app
from .logging_config import setup_logging
from .settings import get_settings


async def main() -> None:
    setup_logging()
    log = logging.getLogger("pigeon_mail_bot")

    settings = get_settings()
    bot, dp = build_app(settings)

    log.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
