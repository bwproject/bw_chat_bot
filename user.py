#user.py

import os
import logging

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("API_ID") or 0)
API_HASH = os.getenv("API_HASH")

SESSION_FILE = "bot2/session.session"

telegram_bot = None
client = None
reply_map = {}

# общий SOCKS5 прокси из main.py
proxy = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("userbot")


# ─────────────────────────────
def init_bot(bot):
    global telegram_bot
    telegram_bot = bot


# ─────────────────────────────
def set_proxy(value):

    global proxy

    proxy = value

    if proxy:
        logger.info(f"🌍 Userbot proxy ENABLED: {proxy}")
    else:
        logger.info("🌍 Userbot no proxy")


# ─────────────────────────────
def load_session():

    if not os.path.exists(SESSION_FILE):
        return None

    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


# ─────────────────────────────
def create_client(session_data=None):

    session = session_data or load_session()

    if not session:
        return None

    kwargs = {}

    # SOCKS5 из main.py
    if proxy:
        kwargs["proxy"] = proxy

    # StringSession или файл
    if ":" in session or len(session) > 80:

        return TelegramClient(
            StringSession(session),
            API_ID,
            API_HASH,
            **kwargs
        )

    return TelegramClient(
        session,
        API_ID,
        API_HASH,
        **kwargs
    )


# ─────────────────────────────
async def start_client(session_data=None):

    global client

    client = create_client(session_data)

    if not client:
        logger.error("❌ No session → userbot disabled")
        return False


    await client.connect()


    if not await client.is_user_authorized():

        logger.error("❌ Session not authorized")
        return False


    me = await client.get_me()

    logger.info(
        f"👤 Logged in: {me.first_name}"
    )


    # listener
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):

        if event.out:
            return


        sender = await event.get_sender()

        if not sender:
            return


        reply_map[sender.id] = event.chat_id


        text = event.raw_text or "[MEDIA]"


        if telegram_bot:

            try:

                await telegram_bot.send_message(
                    int(os.getenv("ADMIN_ID")),
                    f"📩 {sender.first_name}: {text}"
                )

            except Exception as e:

                logger.error(
                    f"Bot send error: {e}"
                )


    return True



# ─────────────────────────────
async def restart_client(session_data=None):

    global client


    try:

        if client:

            await client.disconnect()

            logger.info(
                "🔁 MTProto disconnected"
            )


    except Exception as e:

        logger.warning(
            f"disconnect error: {e}"
        )


    client = None


    return await start_client(session_data)



# ─────────────────────────────
async def send_to_user(user_id, text):

    if not client:
        return False


    if user_id not in reply_map:
        return False


    try:

        await client.send_message(
            reply_map[user_id],
            text
        )

        return True


    except Exception as e:

        logger.error(
            f"send_to_user error: {e}"
        )

        return False



# ─────────────────────────────
async def create_new_chat(username, text):

    if not client:
        return None


    if username.startswith("@"):

        username = username[1:]


    try:

        entity = await client.get_entity(username)

        await client.send_message(
            entity.id,
            text
        )

        return entity.id


    except Exception as e:

        logger.error(
            f"create_new_chat error: {e}"
        )

        return None
