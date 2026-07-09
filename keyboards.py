from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ─────────────────────────────
# SETTINGS MENU
# ─────────────────────────────

def settings_kb(settings):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"Business: {'🟢' if settings['business'] else '🔴'}",
                callback_data="toggle_business"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Userbot: {'🟢' if settings['userbot'] else '🔴'}",
                callback_data="toggle_userbot"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Auto reply: {'🟢' if settings['auto_reply'] else '🔴'}",
                callback_data="toggle_auto_reply"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"New chats: {'🟢' if settings['new_chats'] else '🔴'}",
                callback_data="toggle_new_chats"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Debug: {'🟢' if settings['debug'] else '🔴'}",
                callback_data="toggle_debug"
            )
        ],
        [
            InlineKeyboardButton(text="👥 Все чаты", callback_data="all_chats"),
            InlineKeyboardButton(text="🙈 Игнор", callback_data="ignored_menu")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_settings")
        ]
    ])


# ─────────────────────────────
# CHAT ACTIONS (from /allchat)
# ─────────────────────────────

def chat_kb(chat_id: int, user_id: int = None):
    buttons = []

    if user_id:
        buttons.append([
            InlineKeyboardButton(
                text="🙈 Игнор пользователя",
                callback_data=f"ignore_user:{user_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🚫 Игнор чат",
            callback_data=f"ignore_chat:{chat_id}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─────────────────────────────
# USER CARD (incoming message)
# ─────────────────────────────

def user_card_kb(user_id: int, chat_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Ответить",
                callback_data=f"reply:{user_id}:{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⛔ Отключить автоответ",
                callback_data=f"stop_autoreply:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🙈 Не уведомлять",
                callback_data=f"ignore_user:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚫 Игнор чат",
                callback_data=f"ignore_chat:{chat_id}"
            )
        ]
    ])