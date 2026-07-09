#user.py

import asyncio
import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger("userbot")

client: TelegramClient | None = None
bot_instance = None

dialogs_cache = []


# ─────────────────────────────
# INIT FROM MAIN BOT
# ─────────────────────────────

def init_bot(bot):
    global bot_instance
    bot_instance = bot


# ─────────────────────────────
# START CLIENT
# ─────────────────────────────

async def start_client():
    global client

    try:
        from main import API_ID, API_HASH, SESSION_FILE

        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session_string = f.read().strip()
        except FileNotFoundError:
            session_string = ""

        client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH
        )

        await client.connect()

        if not await client.is_user_authorized():
            logger.warning("⚠️ Userbot not authorized")
            return False

        logger.info("✅ Userbot started")
        return True

    except Exception as e:
        logger.error(f"❌ start_client error: {e}")
        return False


# ─────────────────────────────
# RESTART CLIENT
# ─────────────────────────────

async def restart_client(session_string: str):
    global client

    try:
        if client:
            await client.disconnect()

        from main import API_ID, API_HASH

        client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH
        )

        await client.connect()

        logger.info("🔄 Userbot restarted")

        return True

    except Exception as e:
        logger.error(f"❌ restart_client error: {e}")
        return False


# ─────────────────────────────
# SEND TO USER (USERBOT)
# ─────────────────────────────

async def send_to_user(user_id: int, text: str) -> bool:
    global client

    try:
        if not client:
            return False

        await client.send_message(user_id, text)
        return True

    except Exception as e:
        logger.warning(f"send_to_user failed: {e}")
        return False


# ─────────────────────────────
# GET ALL CHATS
# ─────────────────────────────

async def fetch_all_chats(limit: int = 200):
    global client, dialogs_cache

    if not client:
        return []

    dialogs_cache = []

    async for dialog in client.iter_dialogs(limit=limit):
        entity = dialog.entity

        chat_data = {
            "id": dialog.id,
            "title": getattr(entity, "title", None)
            or getattr(entity, "username", None)
            or getattr(entity, "first_name", "Unknown"),
            "type": str(type(entity).__name__),
            "is_user": dialog.is_user,
            "is_group": dialog.is_group,
            "is_channel": dialog.is_channel
        }

        dialogs_cache.append(chat_data)

    return dialogs_cache


# ─────────────────────────────
# GET FORMATTED CHAT LIST
# ─────────────────────────────

async def get_all_chats():
    chats = await fetch_all_chats()

    formatted = []

    for c in chats:
        name = c["title"]
        cid = c["id"]

        formatted.append(
            f"{'👤' if c['is_user'] else '👥' if c['is_group'] else '📢'} "
            f"{name}\nID: {cid}"
        )

    return formatted


# ─────────────────────────────
# GET CHAT BY ID (future use)
# ─────────────────────────────

def get_chat_by_id(chat_id: int):
    for c in dialogs_cache:
        if c["id"] == chat_id:
            return c
    return None


# ─────────────────────────────
# SAFE WRAPPER
# ─────────────────────────────

async def safe_get_chats():
    try:
        return await get_all_chats()
    except Exception as e:
        logger.error(f"safe_get_chats error: {e}")
        return []
