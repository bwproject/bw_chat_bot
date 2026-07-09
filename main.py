#main.py

import sys
import os
import asyncio
import logging
import re

from dotenv import load_dotenv

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

load_dotenv()


from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramNetworkError
from aiogram.client.session.aiohttp import AiohttpSession


from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError


from proxsybot import init_proxy, proxy_watcher


from user import (
    start_client,
    restart_client,
    init_bot,
    send_to_user,
    get_all_chats
)


from settings_manager import settings_manager


from keyboards import (
    settings_kb,
    user_card_kb
)


# =====================================================
# CONFIG
# =====================================================

USE_PROXY = True


TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(
    os.getenv("ADMIN_ID") or 0
)


API_ID = int(
    os.getenv("API_ID") or 0
)


API_HASH = os.getenv("API_HASH")


AUTO_REPLY_DELAY = int(
    os.getenv("AUTO_REPLY_DELAY", "300")
)


AUTO_REPLY_TEXT = os.getenv(
    "AUTO_REPLY_TEXT",
    "Сейчас мы не в сети."
)


SESSION_FILE = "session.session"



# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "business_bot"
)



# =====================================================
# GLOBALS
# =====================================================

dp = Dispatcher()


bot = None


pending_messages = {}


admin_replied = {}


login_sessions = {}


# пользователи, для которых отключили автоответ
auto_reply_disabled = set()



# =====================================================
# CREATE BOT
# =====================================================

async def create_bot():

    proxy = None


    if USE_PROXY:

        try:

            proxy = await init_proxy()

        except Exception as e:

            logger.error(
                f"Proxy error: {e}"
            )


    if proxy:

        session = AiohttpSession(
            proxy=proxy
        )

        logger.info(
            f"🌍 Proxy enabled: {proxy}"
        )

    else:

        session = AiohttpSession()

        logger.info(
            "🌍 Proxy disabled"
        )


    return Bot(
        token=TOKEN,
        session=session
    )



# =====================================================
# WEBHOOK
# =====================================================

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



# =====================================================
# BUSINESS MESSAGE
# =====================================================

@dp.business_message()
async def business_message_handler(
    message: Message
):

    user_id = message.from_user.id

    chat_id = message.chat.id



    if settings_manager.is_user_ignored(user_id):

        return


    if settings_manager.is_chat_ignored(chat_id):

        return



    text = (

        message.text

        or message.caption

        or "[MEDIA]"

    )



    pending_messages[user_id] = {

        "chat_id": chat_id,

        "business_connection_id":
            message.business_connection_id

    }



    logger.info(
        f"📩 BUSINESS {user_id}: {text}"
    )



    if settings_manager.get("business"):


        await bot.send_message(

            ADMIN_ID,

            f"""
📩 Новое сообщение

👤 {message.from_user.full_name}

🆔 <a href="tg://user?id={user_id}">
{user_id}
</a>

{text}
""",

            parse_mode="HTML",

            reply_markup=user_card_kb(
                user_id,
                chat_id
            )

        )



    asyncio.create_task(

        auto_reply_task(

            user_id,

            chat_id,

            message.business_connection_id

        )

    )
# =====================================================
# AUTO REPLY
# =====================================================

async def auto_reply_task(
    user_id,
    chat_id,
    business_connection_id
):

    await asyncio.sleep(
        AUTO_REPLY_DELAY
    )


    # отключение автоответа кнопкой
    if user_id in auto_reply_disabled:

        auto_reply_disabled.discard(
            user_id
        )

        return



    # админ уже ответил
    if user_id in admin_replied:

        admin_replied.pop(
            user_id,
            None
        )

        return



    if not settings_manager.get(
        "auto_reply"
    ):

        return



    await bot.send_message(

        chat_id,

        AUTO_REPLY_TEXT,

        business_connection_id=
            business_connection_id

    )



# =====================================================
# SETTINGS
# =====================================================

@dp.message(
    Command("settings"),
    F.from_user.id == ADMIN_ID
)
async def settings_cmd(
    message: Message
):

    await message.answer(

        "⚙ Настройки уведомлений",

        reply_markup=settings_kb(
            settings_manager.all()
        )

    )



# =====================================================
# ALL CHAT
# =====================================================

@dp.message(
    Command("allchat"),
    F.from_user.id == ADMIN_ID
)
async def allchat_cmd(
    message: Message
):

    chats = await get_all_chats()



    if not chats:

        return await message.answer(
            "❌ Чаты не найдены"
        )



    text = "\n\n".join(
        chats[:50]
    )



    await message.answer(

        f"👥 Все чаты:\n\n{text}"

    )



# =====================================================
# CALLBACKS
# =====================================================

@dp.callback_query()
async def callbacks(
    call: CallbackQuery
):

    data = call.data



    # ---------------------------------
    # SETTINGS TOGGLE
    # ---------------------------------

    if data.startswith(
        "toggle_"
    ):

        key = data.replace(
            "toggle_",
            ""
        )


        settings_manager.toggle(
            key
        )


        await call.message.edit_reply_markup(

            reply_markup=settings_kb(

                settings_manager.all()

            )

        )


        await call.answer(
            "Обновлено"
        )

        return



    # ---------------------------------
    # DISABLE AUTO REPLY
    # ---------------------------------

    if data.startswith(
        "stop_autoreply:"
    ):

        uid = int(
            data.split(":")[1]
        )


        auto_reply_disabled.add(
            uid
        )


        await call.answer(
            "⛔ Автоответ отключён"
        )


        return



    # ---------------------------------
    # IGNORE USER
    # ---------------------------------

    if data.startswith(
        "ignore_user:"
    ):

        uid = int(
            data.split(":")[1]
        )


        settings_manager.ignore_user(
            uid
        )


        await call.answer(
            "🙈 Пользователь скрыт"
        )


        return



    # ---------------------------------
    # IGNORE CHAT
    # ---------------------------------

    if data.startswith(
        "ignore_chat:"
    ):

        cid = int(
            data.split(":")[1]
        )


        settings_manager.ignore_chat(
            cid
        )


        await call.answer(
            "🚫 Чат скрыт"
        )


        return



    # ---------------------------------
    # REFRESH SETTINGS
    # ---------------------------------

    if data == "refresh_settings":


        await call.message.edit_reply_markup(

            reply_markup=settings_kb(

                settings_manager.all()

            )

        )


        await call.answer(
            "🔄 Обновлено"
        )


        return



    # ---------------------------------
    # ALL CHATS BUTTON
    # ---------------------------------

    if data == "all_chats":

        chats = await get_all_chats()


        text = "\n\n".join(
            chats[:50]
        )


        await call.message.edit_text(

            "👥 Все чаты\n\n" + text

        )


        await call.answer()

        return



    # ---------------------------------
    # IGNORED MENU
    # ---------------------------------

    if data == "ignored_menu":


        ignored = settings_manager.all_ignored()


        text = (
            "🙈 Игнорируемые:\n\n"
            f"👤 Пользователи: "
            f"{len(ignored['users'])}\n"
            f"💬 Чаты: "
            f"{len(ignored['chats'])}"
        )


        await call.message.edit_text(
            text
        )


        await call.answer()

        return
# =====================================================
# ADMIN REPLY SYSTEM
# =====================================================

@dp.message(
    F.from_user.id == ADMIN_ID
)
async def admin_flow(
    message: Message
):

    # если это не ответ на сообщение бота
    if not message.reply_to_message:

        return



    text = (
        message.reply_to_message.text
        or ""
    )



    if "🆔" not in text:

        return



    try:

        user_id = int(
            text.split("🆔")[1]
            .split("\n")[0]
            .strip()
        )

    except Exception:

        return



    # отменяем автоответ
    admin_replied[user_id] = True



    # пробуем отправить через userbot
    if await send_to_user(
        user_id,
        message.text
    ):

        await message.reply(
            "✅ USERBOT"
        )

        return



    # отправка через Business
    if user_id in pending_messages:


        data = pending_messages[user_id]


        await bot.send_message(

            data["chat_id"],

            message.text,

            business_connection_id=
                data["business_connection_id"]

        )


        await message.reply(
            "✅ BUSINESS"
        )



# =====================================================
# LOGIN USERBOT
# =====================================================

@dp.message(
    Command("loginbot"),
    F.from_user.id == ADMIN_ID
)
async def loginbot(
    message: Message
):

    login_sessions[ADMIN_ID] = {

        "step": "phone"

    }


    await message.reply(
        "📱 Отправь номер телефона"
    )



# =====================================================
# LOGIN FLOW
# =====================================================

@dp.message(
    F.from_user.id == ADMIN_ID
)
async def login_flow(
    message: Message
):

    if ADMIN_ID not in login_sessions:

        return



    data = login_sessions[ADMIN_ID]



    # -----------------------------
    # PHONE
    # -----------------------------

    if data["step"] == "phone":


        client = TelegramClient(

            StringSession(),

            API_ID,

            API_HASH

        )


        await client.connect()



        sent = await client.send_code_request(

            message.text.strip()

        )



        login_sessions[ADMIN_ID] = {

            "step": "code",

            "phone":
                message.text.strip(),

            "client":
                client,

            "hash":
                sent.phone_code_hash

        }



        await message.reply(
            "📨 Код отправлен"
        )

        return



    # -----------------------------
    # CODE
    # -----------------------------

    if data["step"] == "code":


        client = data["client"]



        try:

            await client.sign_in(

                phone=data["phone"],

                code=message.text.strip(),

                phone_code_hash=data["hash"]

            )


        except SessionPasswordNeededError:


            data["step"] = "password"


            await message.reply(
                "🔐 Введи пароль 2FA"
            )


            return



        session = client.session.save()



        with open(
            SESSION_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(session)



        await restart_client(
            session
        )



        await client.disconnect()



        login_sessions.pop(
            ADMIN_ID,
            None
        )



        await message.reply(
            "✅ Userbot подключен"
        )


        return



    # -----------------------------
    # PASSWORD
    # -----------------------------

    if data["step"] == "password":


        client = data["client"]



        await client.sign_in(

            password=
                message.text.strip()

        )



        session = client.session.save()



        with open(
            SESSION_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(session)



        await restart_client(
            session
        )



        await client.disconnect()



        login_sessions.pop(
            ADMIN_ID,
            None
        )



        await message.reply(
            "✅ Userbot подключен"
        )



# =====================================================
# START
# =====================================================

async def main():

    global bot



    if USE_PROXY:

        asyncio.create_task(
            proxy_watcher()
        )



    bot = await create_bot()



    init_bot(
        bot
    )



    logger.info(
        "🚀 Starting Business Bot"
    )



    result = await start_client()



    logger.info(
        f"Userbot result: {result}"
    )



    await safe_delete_webhook()



    await dp.start_polling(
        bot
    )



# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
