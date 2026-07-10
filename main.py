#main.py (не удалять)

# ─── Включение / отключение прокси ───────────
USE_PROXY = True   # True = использовать прокси
                   # False = запуск без прокси

import sys
import os
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


# ─────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("business_bot")


dp = Dispatcher()

bot = None

import telegram_userbot

telegram_userbot.register_handlers(dp)

# ─────────────────────────────
async def create_bot():

    proxy = None

    if USE_PROXY:

        try:
            proxy = await init_proxy()

        except Exception as e:
            logger.error(
                f"❌ Proxy init error: {e}"
            )


    if proxy:

        session = AiohttpSession(
            proxy=proxy
        )

        logger.info(
            f"🌍 Aiogram proxy ENABLED: {proxy}"
        )

    else:

        session = AiohttpSession()

        logger.info(
            "🌍 Aiogram no proxy"
        )


    return Bot(
        token=TOKEN,
        session=session
    )



# ─────────────────────────────
async def safe_delete_webhook():

    for i in range(3):

        try:

            await bot.delete_webhook(
                drop_pending_updates=True
            )

            logger.info(
                "✅ Webhook deleted"
            )

            return


        except TelegramNetworkError as e:

            logger.warning(
                f"Webhook retry {i+1}: {e}"
            )

            await asyncio.sleep(3)



# ─────────────────────────────
async def main():

    global bot


    if USE_PROXY:

        asyncio.create_task(
            proxy_watcher()
        )


    bot = await create_bot()


    # Подключаем бизнес-логику
    import handlers

    handlers.register_handlers(
        dp,
        bot
    )


    await safe_delete_webhook()


    logger.info(
        "🚀 Business bot started"
    )


    await dp.start_polling(
        bot
    )



# ─────────────────────────────
if __name__ == "__main__":

    asyncio.run(main())
