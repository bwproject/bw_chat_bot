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
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from proxsybot import init_proxy, proxy_watcher
# ─────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
API_ID = int(os.getenv("API_ID") or 0)
API_HASH = os.getenv("API_HASH")
AUTO_REPLY_DELAY = int(os.getenv("AUTO_REPLY_DELAY", "300"))
AUTO_REPLY_TEXT = os.getenv(
    "AUTO_REPLY_TEXT",
    "Сейчас мы не в сети."
)
SESSION_FILE = "session.session"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("business_bot")
dp = Dispatcher()
pending_messages = {}
admin_replied = {}
login_sessions = {}
bot = None
# ─────────────────────────────
async def create_bot():
    proxy = None
    if USE_PROXY:
        try:
            proxy = await init_proxy()
        except Exception as e:
            logger.error(f"❌ Proxy init error: {e}")
            proxy = None
    # ───── AIOHTTP SESSION
    if proxy:
        session = AiohttpSession(proxy=proxy)
        logger.info(f"🌍 Aiogram proxy ENABLED: {proxy}")
    else:
        session = AiohttpSession()
        logger.info("🌍 Aiogram no proxy")
    return Bot(
        token=TOKEN,
        session=session
    )
# ─────────────────────────────
async def safe_delete_webhook():
    for i in range(3):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook deleted")
            return
        except TelegramNetworkError as e:
            logger.warning(f"Webhook retry {i+1}: {e}")
            await asyncio.sleep(3)
# ─────────────────────────────
@dp.business_message()
async def business_message_handler(message: Message):
    user_id = message.from_user.id
    text = (
        message.text
        or message.caption
        or "[MEDIA]"
    )
    pending_messages[user_id] = {
        "chat_id": message.chat.id,
        "business_connection_id": message.business_connection_id
    }
    logger.info(f"📩 BUSINESS MSG {user_id}: {text}")
    await bot.send_message(
        ADMIN_ID,
        f"""📩 Новое сообщение
👤 {message.from_user.full_name}
🆔 <a href="tg://user?id={user_id}">{user_id}</a>
{text}""",
        parse_mode="HTML"
    )
    asyncio.create_task(
        auto_reply_task(
            user_id,
            message.chat.id,
            message.business_connection_id
        )
    )
# ─────────────────────────────
async def auto_reply_task(user_id, chat_id, business_connection_id):
    await asyncio.sleep(AUTO_REPLY_DELAY)
    if user_id in admin_replied:
        return
    await bot.send_message(
        chat_id=chat_id,
        text=AUTO_REPLY_TEXT,
        business_connection_id=business_connection_id
    )
# ────────────── REPLY MODE
    if not message.reply_to_message:
        return
    text = message.reply_to_message.text or ""
    if "🆔" not in text:
        return
    user_id = int(
        text.split("🆔 ")[1].split("\n")[0]
    )
    admin_replied[user_id] = True
    if await send_to_user(user_id, message.text):
        return await message.reply("✅ USERBOT")

    if user_id in pending_messages:
        data = pending_messages[user_id]
        await bot.send_message(
            data["chat_id"],
            message.text,
            business_connection_id=data["business_connection_id"]
        )
        return await message.reply("✅ BUSINESS")

# ─────────────────────────────
async def main():
    global bot
    if USE_PROXY:
        asyncio.create_task(proxy_watcher())
    bot = await create_bot()
    init_bot(bot)
    logger.info("🚀 Starting MTProto userbot...")
    ok = await start_client()
    logger.info(f"MTProto start result: {ok}")
    await safe_delete_webhook()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
