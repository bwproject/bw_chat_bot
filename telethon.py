# Telethon.py (не удалять)

import os
import logging

from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


logger = logging.getLogger("business_bot")


ADMIN_ID = int(
    os.getenv("ADMIN_ID") or 0
)

API_ID = int(
    os.getenv("API_ID") or 0
)

API_HASH = os.getenv(
    "API_HASH"
)


SESSION_FILE = "session.session"


client = TelegramClient(
    SESSION_FILE,
    API_ID,
    API_HASH
)


login_state = {}



# =====================================
# Запуск Telethon
# =====================================

async def start_client():

    await client.connect()


    if await client.is_user_authorized():

        logger.info(
            "✅ Telethon session loaded"
        )

        return True


    logger.info(
        "⚠️ Telethon not authorized"
    )

    return False



# =====================================
# Регистрация команд
# =====================================

def register_handlers(dp: Dispatcher):


    @dp.message(
        Command("login")
    )
    async def login(message: Message):

        if message.from_user.id != ADMIN_ID:
            return


        await client.connect()


        login_state[ADMIN_ID] = {
            "step": "phone"
        }


        await message.reply(
            "📱 Отправь номер телефона"
        )



    @dp.message(
        Command("newchat")
    )
    async def newchat(message: Message):

        if message.from_user.id != ADMIN_ID:
            return


        if not await client.is_user_authorized():

            return await message.reply(
                "❌ Telethon не авторизован\n"
                "Используй /login"
            )


        args = message.text.split(
            maxsplit=2
        )


        if len(args) < 3:

            return await message.reply(
                "Использование:\n"
                "/newchat @username текст"
            )


        username = args[1]
        text = args[2]


        await client.send_message(
            username,
            text
        )


        await message.reply(
            "✅ Сообщение отправлено"
        )



    @dp.message(
        F.from_user.id == ADMIN_ID
    )
    async def login_process(
            message: Message
    ):


        if ADMIN_ID not in login_state:

            return


        step = login_state[ADMIN_ID]["step"]



        # PHONE

        if step == "phone":


            sent = await client.send_code_request(
                message.text
            )


            login_state[ADMIN_ID] = {

                "step": "code",

                "phone": message.text,

                "hash":
                    sent.phone_code_hash
            }


            return await message.reply(
                "📨 Код отправлен"
            )



        # CODE

        if step == "code":

            try:

                await client.sign_in(

                    phone=
                        login_state[ADMIN_ID]["phone"],

                    code=
                        message.text,

                    phone_code_hash=
                        login_state[ADMIN_ID]["hash"]

                )


            except SessionPasswordNeededError:


                login_state[ADMIN_ID]["step"] = (
                    "password"
                )


                return await message.reply(
                    "🔐 Введи пароль 2FA"
                )


            login_state.pop(
                ADMIN_ID
            )


            return await message.reply(
                "✅ Авторизация успешна\n"
                "session.session сохранён"
            )



        # PASSWORD

        if step == "password":


            await client.sign_in(
                password=message.text
            )


            login_state.pop(
                ADMIN_ID
            )


            await message.reply(
                "✅ Авторизация с 2FA успешна"
            )