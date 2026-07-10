# main.py

# ─── Включение / отключение прокси ───────────
USE_PROXY = True

import os
import sys
import asyncio
import logging

from dotenv import load_dotenv

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError

from proxsybot import init_proxy, proxy_watcher

from user import (
    start_client,
    init_bot
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("business_bot")

dp = Dispatcher()

bot = None


async def create_bot():

    proxy = None

    if USE_PROXY:
        try:
            proxy = await init_proxy()
        except Exception as e:
            logger.error(f"Proxy error: {e}")

    session = (
        AiohttpSession(proxy=proxy)
        if proxy
        else AiohttpSession()
    )

    return Bot(
        token=TOKEN,
        session=session
    )


async def safe_delete_webhook():

    for _ in range(3):

        try:
            await bot.delete_webhook(
                drop_pending_updates=True
            )
            return

        except TelegramNetworkError:
            await asyncio.sleep(3)


async def main():

    global bot

    if USE_PROXY:
        asyncio.create_task(proxy_watcher())

    bot = await create_bot()

    init_bot(bot)

    # регистрация всех роутеров
    from business import router as business_router
    from replies import router as replies_router
    from login import router as login_router

    dp.include_router(login_router)
    dp.include_router(business_router)
    dp.include_router(replies_router)

    logger.info("Starting MTProto...")

    await start_client()

    await safe_delete_webhook()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())