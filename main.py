# main.py

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



from proxsybot import (
    init_proxy,
    proxy_watcher
)



from user import (
    start_client,
    restart_client,
    init_bot,
    send_to_user,
    send_media_to_user,
    download_telegram_file,
    delete_temp_file,
    create_new_chat
)



# ─────────────────────────────

TOKEN = os.getenv(
    "BOT_TOKEN"
)


ADMIN_ID = int(
    os.getenv("ADMIN_ID") or 0
)


API_ID = int(
    os.getenv("API_ID") or 0
)


API_HASH = os.getenv(
    "API_HASH"
)



AUTO_REPLY_DELAY = int(
    os.getenv(
        "AUTO_REPLY_DELAY",
        "300"
    )
)



AUTO_REPLY_TEXT = os.getenv(
    "AUTO_REPLY_TEXT",
    "Сейчас мы не в сети."
)



SESSION_FILE = "session.session"



logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "business_bot"
)



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

            logger.error(
                f"❌ Proxy init error: {e}"
            )

            proxy = None



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
@dp.business_message()
async def business_message_handler(
    message: Message
):

    user_id = message.from_user.id


    text = (
        message.text
        or message.caption
        or "[MEDIA]"
    )


    pending_messages[user_id] = {

        "chat_id": message.chat.id,

        "business_connection_id":
            message.business_connection_id,

        "last_message":
            message
    }



    logger.info(
        f"📩 BUSINESS MSG {user_id}: {text}"
    )



    admin_text = f"""📩 Новое сообщение

👤 {message.from_user.full_name}

🆔 <a href="tg://user?id={user_id}">
{user_id}
</a>

{text}
"""



    # 📷 Фото

    if message.photo:


        await bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=admin_text,
            parse_mode="HTML"
        )



    # 🎥 Видео

    elif message.video:


        await bot.send_video(
            ADMIN_ID,
            message.video.file_id,
            caption=admin_text,
            parse_mode="HTML"
        )



    # 🎤 Голосовое

    elif message.voice:


        await bot.send_voice(
            ADMIN_ID,
            message.voice.file_id,
            caption=admin_text,
            parse_mode="HTML"
        )



    # ⭕ Кружок

    elif message.video_note:


        await bot.send_video_note(
            ADMIN_ID,
            message.video_note.file_id
        )


        await bot.send_message(
            ADMIN_ID,
            admin_text,
            parse_mode="HTML"
        )



    # 📄 Документ

    elif message.document:


        await bot.send_document(
            ADMIN_ID,
            message.document.file_id,
            caption=admin_text,
            parse_mode="HTML"
        )



    # 🎵 Аудио

    elif message.audio:


        await bot.send_audio(
            ADMIN_ID,
            message.audio.file_id,
            caption=admin_text,
            parse_mode="HTML"
        )



    # 🎭 Стикер

    elif message.sticker:


        await bot.send_sticker(
            ADMIN_ID,
            message.sticker.file_id
        )


        await bot.send_message(
            ADMIN_ID,
            admin_text,
            parse_mode="HTML"
        )



    # 📝 Обычный текст

    else:


        await bot.send_message(
            ADMIN_ID,
            admin_text,
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
async def auto_reply_task(
    user_id,
    chat_id,
    business_connection_id
):


    await asyncio.sleep(
        AUTO_REPLY_DELAY
    )


    if user_id in admin_replied:

        return



    await bot.send_message(
        chat_id=chat_id,
        text=AUTO_REPLY_TEXT,
        business_connection_id=
            business_connection_id
    )
# ─────────────────────────────
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
        "📱 Введите номер:"
    )



# ─────────────────────────────
@dp.message(
    F.from_user.id == ADMIN_ID
)
async def admin_flow(
    message: Message
):


    # ───────── LOGIN FLOW

    if ADMIN_ID in login_sessions:


        data = login_sessions[ADMIN_ID]



        # PHONE

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


            return await message.reply(
                "📨 Код отправлен"
            )



        # CODE

        if data["step"] == "code":


            client = data.get(
                "client"
            )


            if not client:

                return await message.reply(
                    "❌ client lost"
                )



            try:


                await client.sign_in(
                    phone=data["phone"],

                    code=message.text.strip(),

                    phone_code_hash=data["hash"]
                )



            except SessionPasswordNeededError:


                data["step"] = "password"


                return await message.reply(
                    "🔐 2FA пароль"
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



            return await message.reply(
                "✅ OK"
            )



        # PASSWORD

        if data["step"] == "password":


            client = data.get(
                "client"
            )


            await client.sign_in(
                password=message.text.strip()
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



            return await message.reply(
                "✅ OK"
            )



    # ───────── REPLY MODE


    if not message.reply_to_message:

        return



    reply_text = (
        message.reply_to_message.text
        or message.reply_to_message.caption
        or ""
    )



    if "🆔" not in reply_text:

        return



    user_id = int(
        reply_text
        .split("🆔 ")[1]
        .split("\n")[0]
        .replace("<", "")
        .replace(">", "")
    )



    admin_replied[user_id] = True



    # ───── USERBOT TEXT


    if message.text:


        if await send_to_user(
            user_id,
            message.text
        ):


            return await message.reply(
                "✅ USERBOT"
            )



    # ───── MEDIA → USERBOT


    media_file_id = None



    if message.photo:

        media_file_id = (
            message.photo[-1].file_id
        )


    elif message.video:

        media_file_id = (
            message.video.file_id
        )


    elif message.voice:

        media_file_id = (
            message.voice.file_id
        )


    elif message.document:

        media_file_id = (
            message.document.file_id
        )


    elif message.audio:

        media_file_id = (
            message.audio.file_id
        )



    if media_file_id:


        path = await download_telegram_file(
            bot,
            media_file_id
        )



        if path:


            try:


                if await send_media_to_user(
                    user_id,
                    path,
                    message.caption
                ):


                    return await message.reply(
                        "✅ USERBOT MEDIA"
                    )


            finally:


                await delete_temp_file(
                    path
                )



    # ───── BUSINESS REPLY


    if user_id in pending_messages:


        data = pending_messages[user_id]



        # TEXT

        if message.text:


            await bot.send_message(
                data["chat_id"],
                message.text,

                business_connection_id=
                    data["business_connection_id"]
            )



        # MEDIA


        elif media_file_id:


            path = await download_telegram_file(
                bot,
                media_file_id
            )



            if path:


                try:


                    await bot.send_document(
                        data["chat_id"],
                        document=message.document.file_id
                        if message.document
                        else media_file_id,

                        caption=message.caption,

                        business_connection_id=
                            data["business_connection_id"]
                    )


                finally:


                    await delete_temp_file(
                        path
                    )



        return await message.reply(
            "✅ BUSINESS"
        )



# ─────────────────────────────
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
        "🚀 Starting MTProto userbot..."
    )



    ok = await start_client()



    logger.info(
        f"MTProto start result: {ok}"
    )



    await safe_delete_webhook()



    await dp.start_polling(
        bot
    )



# ─────────────────────────────
if __name__ == "__main__":

    asyncio.run(
        main()
    )