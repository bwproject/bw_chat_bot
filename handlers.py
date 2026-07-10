# handlers.py (не удалять)

from aiogram import F
from aiogram.types import Message
from aiogram import Dispatcher, Bot

import asyncio
import os
import json
import logging

from pathlib import Path


ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

AUTO_REPLY_DELAY = int(
    os.getenv("AUTO_REPLY_DELAY", "300")
)

AUTO_REPLY_TEXT = os.getenv(
    "AUTO_REPLY_TEXT",
    "Сейчас мы не в сети."
)


logger = logging.getLogger("business_bot")


# =====================================
# Storage
# =====================================

DATA_FILE = Path(
    "data/business_messages.json"
)


pending_messages = {}
admin_replied = {}



def load_data():

    DATA_FILE.parent.mkdir(
        exist_ok=True
    )


    if not DATA_FILE.exists():

        DATA_FILE.write_text(
            json.dumps(
                {
                    "pending_messages": {},
                    "admin_replied": {}
                },
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )


    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def save_data():

    DATA_FILE.parent.mkdir(
        exist_ok=True
    )


    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "pending_messages": pending_messages,
                "admin_replied": admin_replied
            },
            f,
            ensure_ascii=False,
            indent=4
        )



storage = load_data()


pending_messages.update(
    storage.get(
        "pending_messages",
        {}
    )
)


admin_replied.update(
    storage.get(
        "admin_replied",
        {}
    )
)



# =====================================
# Handlers
# =====================================

def register_handlers(
        dp: Dispatcher,
        bot: Bot
):


    # =================================
    # Новое сообщение от клиента
    # =================================

    @dp.business_message()
    async def business_message_handler(
            message: Message
    ):


        user_id = message.from_user.id


        pending_messages[str(user_id)] = {

            "chat_id": message.chat.id,

            "business_connection_id":
                message.business_connection_id
        }


        save_data()



        text = (

            message.text

            or message.caption

            or "[MEDIA]"

        )



        admin_text = f"""📩 Новое сообщение

👤 {message.from_user.full_name}

🆔 <a href="tg://user?id={user_id}">{user_id}</a>

{text}"""



        logger.info(
            f"📩 BUSINESS MSG {user_id}: {text}"
        )



        # Фото

        if message.photo:

            await bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=admin_text,
                parse_mode="HTML"
            )


        # Видео

        elif message.video:

            await bot.send_video(
                ADMIN_ID,
                message.video.file_id,
                caption=admin_text,
                parse_mode="HTML"
            )


        # Голосовое

        elif message.voice:

            await bot.send_voice(
                ADMIN_ID,
                message.voice.file_id,
                caption=admin_text,
                parse_mode="HTML"
            )


        # Аудио

        elif message.audio:

            await bot.send_audio(
                ADMIN_ID,
                message.audio.file_id,
                caption=admin_text,
                parse_mode="HTML"
            )


        # Документ

        elif message.document:

            await bot.send_document(
                ADMIN_ID,
                message.document.file_id,
                caption=admin_text,
                parse_mode="HTML"
            )


        # Стикер

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


        # Текст

        else:

            await bot.send_message(
                ADMIN_ID,
                admin_text,
                parse_mode="HTML"
            )



        asyncio.create_task(

            auto_reply_task(

                bot,

                user_id,

                message.chat.id,

                message.business_connection_id

            )

        )



    # =================================
    # Ответ администратора
    # =================================

    @dp.message(
        F.from_user.id == ADMIN_ID
    )
    async def admin_reply(
            message: Message
    ):


        if not message.reply_to_message:

            return



        original = (

            message.reply_to_message.text

            or message.reply_to_message.caption

            or ""

        )



        if "🆔" not in original:

            return



        try:

            user_id = int(

                original
                .split("🆔 ")[1]
                .split("\n")[0]

            )

        except Exception:

            return



        user_key = str(user_id)



        if user_key not in pending_messages:


            await message.reply(
                "❌ Пользователь не найден"
            )

            return



        admin_replied[user_key] = True

        save_data()



        data = pending_messages[user_key]



        await send_message_to_user(
            bot,
            message,
            data
        )


        await message.reply(
            "✅ Ответ отправлен"
        )



# =====================================
# Отправка сообщения клиенту
# =====================================

async def send_message_to_user(
        bot: Bot,
        message: Message,
        data: dict
):


    kwargs = {

        "chat_id":
            data["chat_id"],

        "business_connection_id":
            data["business_connection_id"]

    }



    if message.photo:


        await bot.send_photo(
            photo=message.photo[-1].file_id,
            caption=message.caption,
            **kwargs
        )



    elif message.video:


        await bot.send_video(
            video=message.video.file_id,
            caption=message.caption,
            **kwargs
        )



    elif message.voice:


        await bot.send_voice(
            voice=message.voice.file_id,
            **kwargs
        )



    elif message.audio:


        await bot.send_audio(
            audio=message.audio.file_id,
            caption=message.caption,
            **kwargs
        )



    elif message.document:


        await bot.send_document(
            document=message.document.file_id,
            caption=message.caption,
            **kwargs
        )



    elif message.sticker:


        await bot.send_sticker(
            sticker=message.sticker.file_id,
            **kwargs
        )



    else:


        await bot.send_message(
            text=message.text,
            **kwargs
        )



# =====================================
# Автоответ
# =====================================

async def auto_reply_task(
        bot: Bot,
        user_id: int,
        chat_id: int,
        business_connection_id: str
):


    await asyncio.sleep(
        AUTO_REPLY_DELAY
    )



    if str(user_id) in admin_replied:

        return



    await bot.send_message(

        chat_id,

        AUTO_REPLY_TEXT,

        business_connection_id=
            business_connection_id

    )



    logger.info(
        f"🤖 Auto reply sent: {user_id}"
    )