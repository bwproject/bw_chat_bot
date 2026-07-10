# handlers.py (не удалять)

from aiogram import F
from aiogram.types import Message
from aiogram import Dispatcher, Bot

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


    # =====================================
    # Новые сообщения Business аккаунта
    # =====================================

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



    # =====================================
    # Ответ администратора
    # =====================================

    @dp.message(F.from_user.id == ADMIN_ID)
    async def admin_reply(message: Message):

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

            logger.error(
                "❌ Не найден ID пользователя"
            )

            return



        if user_id not in pending_messages:

            await message.reply(
                "❌ Пользователь не найден"
            )

            return



        admin_replied[user_id] = True


        data = pending_messages[user_id]


        await bot.send_message(
            chat_id=data["chat_id"],
            text=message.text,
            business_connection_id=
                data["business_connection_id"]
        )


        await message.reply(
            "✅ Ответ отправлен"
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


    if user_id in admin_replied:

        return



    await bot.send_message(
        chat_id=chat_id,
        text=AUTO_REPLY_TEXT,
        business_connection_id=
            business_connection_id
    )


    logger.info(
        f"🤖 Auto reply sent to {user_id}"
    )