
from telegram import  ReplyKeyboardMarkup
from config import *
from uval_handler import *


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    role = get_user_role(user_id)

    if not role:
        await update.message.reply_text(
            "Вы не зарегистрированы. Используйте /register для регистрации."
        )
        return
    elif role == "removed":
        await update.message.reply_text(
            "Ваш аккаунт был удалён, обратитесь к создателю для решения проблемы"
        )
        return

    reply_keyboard = [
        ["Работа с аккаунтами🤖", "Для следящих☠️"],
        ["Управление аккаунтами🔧"],
        ["Проверка кандидатов1️⃣3️⃣$"],
    ]

    # Настройка кнопок на основе роли
    if role == "sled":
        reply_keyboard = [
            ["Проверить онлайн⏰", "Проверить привязки🔗", "Для следящих☠️"],
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    elif role == "admin":
        reply_keyboard = [
            ["Работа с аккаунтами🤖", "Для следящих☠️"  ],
            ["Проверка кандидатов1️⃣3️⃣"],
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    elif role == "tech":
        reply_keyboard = [
            ["Работа с аккаунтами🤖", "Для следящих☠️"  ],
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    elif role == "developer":
        reply_keyboard = [
            ["Работа с аккаунтами🤖", "Для следящих☠️"],
            ["Управление аккаунтами🔧", "Проверка кандидатов1️⃣3️⃣"],

        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )
    elif role == "registered" or not role:
        reply_keyboard = [["/start"]]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    await update.message.reply_text(
        "Выберите действие:", reply_markup=reply_markup
    )