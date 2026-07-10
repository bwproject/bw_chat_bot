# handlers.py (не удалять)

from aiogram import F
from aiogram.types import Message
from aiogram import Dispatcher, Bot
from aiogram.filters import Command

import asyncio
import os
import logging


ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

AUTO_REPLY_DELAY = int(
    os.getenv("AUTO_REPLY_DELAY", "300")
)

AUTO_REPLY_TEXT = os.getenv(
    "AUTO_REPLY_TEXT",
    "Сейчас мы не в сети."
)


pending_messages = {}
admin_replied = {}

logger = logging.getLogger("business_bot")



def register_handlers(dp: Dispatcher, bot: Bot):


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
            "business_connection_id":
                message.business_connection_id
        }


        logger.info(
            f"📩 BUSINESS MSG {user_id}: {text}"
        )


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
                bot,
                user_id,
                message.chat.id,
                message.business_connection_id
            )
        )



async def auto_reply_task(
        bot,
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
        chat_id,
        AUTO_REPLY_TEXT,
        business_connection_id=
            business_connection_id
    )
