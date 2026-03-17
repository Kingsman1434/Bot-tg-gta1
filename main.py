
from telegram import  ReplyKeyboardMarkup,  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler,  CallbackQueryHandler
from report_handler import date_from_report, date_to_report, nicknames_report
from invite_handler import *
from online_handler import (
    check_start as online_check_start,
    date_from as online_date_from,
    date_to as online_date_to,
    nicknames as online_nicknames,
    )
from trade_handler import (
    check_start as trade_check_start,
    date_from as trade_date_from,
    date_to as trade_date_to,
    nicknames as trade_nicknames,
    )
from check_handler import get_conversation_handler
from account_handler import accountc_handler,  NICKNAMES
from database import init_db, add_user,  update_user_role, get_all_users, delete_user
import sqlite3
from config import *
from accountban_handler import accountcc_handler, account_start as acc_start
from uval_handler import *
from gospay_handler import check_start as gos_start, date_from_gos, date_to_gos, get_fraction, FRACTION
import logging
from get_log import send_file

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)
# Пример логирования
logger = logging.getLogger()



DATE_FROM, DATE_TO, NICKNAMES, SERVER, NICKNAME, DELETE_USER , ROLE_USER_ID, ROLE_NEW_ROLE, TELEGRAM_USER  = range(9)

async def log_button_press(update: Update, context: CallbackContext) -> None:

    user = update.message.from_user
    logger.info(f"Пользователь {user.username} ({user.id}) Нажал на кнопку: {update.message.text}")

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Операция отменена.")
    user = update.message.from_user
    logger.info(f"Пользователь {user.username} ({user.id}) Отменил действие")
    return ConversationHandler.END

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

    if role == "sled":
        reply_keyboard = [
            ["Проверить онлайн⏰", "Проверить привязки🔗", "Для следящих☠️"],
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    elif role == "admin":
        reply_keyboard = [
            ["Работа с аккаунтами🤖", "Для следящих☠️"],
            ["Проверка кандидатов1️⃣3️⃣", "Управление аккаунтами🔐"],
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    elif role == "tech":
        reply_keyboard = [
            ["Работа с аккаунтами🤖", "Для следящих☠️"],
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    elif role == "developer":
        reply_keyboard = [
            ["Работа с аккаунтами🤖", "Для следящих☠️"],
            ["Управление аккаунтами🔧", "Проверка кандидатов1️⃣3️⃣"],
            ["Выгрузка логов📖"],

        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )
    elif role == "registered" or not role:
        reply_keyboard = [["/start"]]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )
    if role != 'registered':
        await update.message.reply_text(
            "Выберите действие:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Ждите одобрения", reply_markup=reply_markup
        )



async def register_start(update: Update, context: CallbackContext) -> int:
    await log_button_press(update, context)
    user_id = update.message.from_user.id
    role = get_user_role(user_id)

    if role == "registered":
        await update.message.reply_text(
            "Вы уже зарегистрированы и ожидаете подтверждения."
        )
        await start(update, context)
        return ConversationHandler.END

    if role is not None and role != 'removed':
        await update.message.reply_text(
            "Ваша заявка уже отправлена на регистрацию. Ожидайте подтверждения."
        )
        await start(update, context)
        return ConversationHandler.END

    elif role in ['sled', 'tech', 'admin', 'developer']:
        await update.message.reply_text(f"Вы уже зарегестрированы и имеете доступ {role}")

    elif role == 'removed' and role is not None:
        await start(update, context)
        return ConversationHandler.END



    await update.message.reply_text("Напишите ваш Nick_name:")
    return NICKNAME

async def register_nickname(update: Update, context: CallbackContext) -> int:
    await log_button_press(update, context)
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    if role == "registered":
        await update.message.reply_text(
            "Вы уже зарегистрированы и ожидаете подтверждения."
        )
        await start(update, context)
        return ConversationHandler.END

    nickname = update.message.text
    context.user_data["nickname"] = nickname
    await update.message.reply_text("Сервер от 1 до 7:")
    return SERVER

async def register_server(update: Update, context: CallbackContext) -> int:
    await log_button_press(update, context)
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    telegram_id = update.message.from_user.username
    if role == "registered":
        await update.message.reply_text(
            "Вы уже зарегистрированы и ожидаете подтверждения."
        )
        await start(update, context)
        return ConversationHandler.END

    server = update.message.text
    nickname = context.user_data.get("nickname")
    try:
        add_user(user_id, telegram_id, nickname, "registered", int(server))
        logging.info(f"Пользователь {nickname} ожидает подстверждения")
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            f"Ваш ник:{nickname},Заявка подана на сервер:{server}"
        )

    await start(update, context)
    return ConversationHandler.END

async def sled_button(update: Update, context: CallbackContext) -> int:
    await log_button_press(update, context)
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    if role in ['sled', 'tech', 'admin', 'developer']:
        reply_keyboard = [
            ["Увольнения с фракции✏️", "Принятие во фракцию🚪", "Снятие денег с фракции💶"],
            ["/cancel", "Назад"],
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        await update.message.reply_text(
            "Выберите действие:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Отказано в доступе")
        await start(update, context)
        return ConversationHandler.END

async def for_adm_acc_button(update: Update, context: CallbackContext) -> int:
    await log_button_press(update, context)
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    if role in ['admin', 'developer']:
        reply_keyboard = [
            ["Список заявок🗒", "Список пользователей👩‍👩‍👦‍👦", "Изменить доступ🔐"],
            ["Назад"],
        ]
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=False, resize_keyboard=True
            )
        )
    else:
        await update.message.reply_text("Отказано в доступе")
        await start(update, context)
        return ConversationHandler.END

async def for_account_button(update: Update, context: CallbackContext) -> int:
    await log_button_press(update, context)
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    if role in ['tech', 'admin', 'developer']:
        reply_keyboard = [
            ["Выгрузка репорта📖", "Проверить онлайн⏰"],
            ["Проверить привязки🔗", "Проверить передачи🤑"],
            ["Проверить твинки🤡"],
            ["/cancel", "Назад"],
        ]
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=False, resize_keyboard=True
            )
        )
    else:
        await update.message.reply_text("Отказано в доступе")
        await start(update, context)
        return ConversationHandler.END
async def manage_accounts(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    if role == 'developer':
        reply_keyboard = [
        ["Список заявок🗒", "Удалить пользователя🚫", "Список пользователей👨‍👨‍👧‍👦"],
        ["Изменить доступ🔐"],
        ["Назад"],
        ]
    else:
        update_user_role(user_id, 'removed')
        await update.message.reply_text('Ваш аккаунт удалён за попытку слива')

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        ),
    )


async def list_pending_users(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    pending_users = get_all_users()  # Fetch users with 'registered' status
    pending_users = [user for user in pending_users if user[3] == "registered"]

    if not pending_users:
        await update.message.reply_text("Нет ожидающих заявок.")
        logger.info(f"Пользователь {user_id} запросил список ожидающих заявок. Ожидающих заявок нет.")
        return

    buttons = []
    for user in pending_users:
        buttons.append([
            InlineKeyboardButton(f"Одобрить {user[0]}", callback_data=f"approve_{user[0]}"),
            InlineKeyboardButton(f"Отказать {user[0]}", callback_data=f"reject_{user[0]}")
        ])

    reply_markup = InlineKeyboardMarkup(buttons)

    user_info = "\n\n".join([f"User ID: {user[0]}\nNickname: {user[1]}\nServer: {user[3]}" for user in pending_users])
    await update.message.reply_text(user_info, reply_markup=reply_markup)
    logger.info(f"Пользователь {user_id} запросил список ожидающих заявок. Найдено {len(pending_users)} заявок.")


async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Answer callback query to stop the loading circle

    query_data = query.data
    query_parts = query_data.split('_')
    admin_id = query.from_user.id

    logger.debug(f"Пользователь {admin_id} инициировал действие: {query_data}")

    if len(query_parts) != 2:
        logger.error(f"Неверный формат callback_data: {query_data}")
        await query.answer("Произошла ошибка: неверный формат данных.")
        return

    action, user_id_str = query_parts
    try:
        user_id = int(user_id_str)
    except ValueError:
        logger.error(f"Неверный ID пользователя: {user_id_str}")
        await query.answer("Произошла ошибка: неверный ID пользователя.")
        return

    user_role = get_user_role(query.from_user.id)
    if user_role != "admin" and user_role != "developer":
        await query.answer("У вас нет прав для этого действия.")
        logger.warning(
            f"Пользователь {admin_id} попытался выполнить {action} для пользователя {user_id} без необходимых прав.")
        return

    if action == "approve":
        update_user_role(user_id, "sled")
        await query.answer(f"Пользователь {user_id} одобрен.")
        logger.info(f"Пользователь {admin_id} одобрил пользователя {user_id}.")
    elif action == "reject":
        update_user_role(user_id, "removed")
        await query.answer(f"Пользователь {user_id} отклонён.")
        logger.info(f"Пользователь {admin_id} отклонил пользователя {user_id}.")
    else:
        await query.answer("Неизвестное действие.")
        logger.error(f"Пользователь {admin_id} инициировал неизвестное действие: {query_data}")
        return

    pending_users = get_all_users()
    pending_users = [user for user in pending_users if user[3] == "registered"]

    if pending_users:
        buttons = []
        for user in pending_users:
            buttons.append([
                InlineKeyboardButton(f"Одобрить {user[0]}", callback_data=f"approve_{user[0]}"),
                InlineKeyboardButton(f"Отказать {user[0]}", callback_data=f"reject_{user[0]}")
            ])
        reply_markup = InlineKeyboardMarkup(buttons)
        user_info = "\n\n".join(
            [f"User ID: {user[0]}\nTG Nickname: {user[1]}\nNickname: {user[2]}\nServer: {user[4]}" for user in pending_users])

        if query.message.text != user_info:
            await query.edit_message_text(user_info, reply_markup=reply_markup)
    else:
        await query.edit_message_text("Нет ожидающих заявок.")
    logger.info(f"Обновлён список ожидающих заявок пользователем {admin_id}.")

# Аналогично добавьте логирование для других функций
# Например, для функции change_role_start:
async def change_role_start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    user_role = get_user_role(user_id)
    if user_role not in ["admin", "developer"]:
        await update.message.reply_text("У вас нет прав для изменения роли пользователей.")
        logger.warning(f"Пользователь {user_id} попытался изменить роль пользователя без необходимых прав.")
        return ConversationHandler.END

    await update.message.reply_text("Введите ID пользователя для изменения роли:")
    logger.info(f"Пользователь {user_id} начал процесс изменения роли.")
    return ROLE_USER_ID

async def change_role_user_id(update: Update, context: CallbackContext) -> int:
    user_id = update.message.text
    context.user_data['change_role_user_id'] = user_id
    await update.message.reply_text(f"ID пользователя: {user_id}. Введите новую роль:")
    return ROLE_NEW_ROLE


async def change_role_new_role(update: Update, context: CallbackContext) -> int:
    new_role = update.message.text
    user_id = context.user_data.get('change_role_user_id')
    current_user_id = update.message.from_user.id
    # Проверка роли администраторов перед обновлением роли пользователя
    admin_role = get_user_role(update.message.from_user.id)

    if new_role == "developer" or new_role == "admin":
        # Если текущий пользователь админ и хочет выдать роль developer другому пользователю
        if admin_role == "admin":
            # Удаляем текущего админа
            update_user_role(update.message.from_user.id, "removed")
            await update.message.reply_text(
                "Ваш статус был удалён за попытку дать роль developer другому пользователю.")
            return ConversationHandler.END

        # Если текущий пользователь админ и хочет выдать роль developer другому пользователю
        # Мы также удаляем пользователя, которому хотели дать роль
        if get_user_role(int(user_id)) == "developer":
            update_user_role(int(user_id), "removed")
            await update.message.reply_text(f"Пользователь {user_id} был удалён за попытку принять роль developer.")
            await start(update, context)
            return ConversationHandler.END
    if admin_role == 'admin' and  get_user_role(int(user_id)) == "developer":
        update_user_role(int(current_user_id), "removed")
        await update.message.reply_text(f"Ваш аккаунт был удалён за попытку изменения роли developer.")
        await start(update, context)
        return ConversationHandler.END


    try:
        user_id = int(user_id)
        update_user_role(user_id, new_role)
        user = update.message.from_user

        logger.info(f"Пользователь {user.username} ({user.id}) Изменил роль пользователю {user_id} на {new_role}")
        await update.message.reply_text(f"Роль пользователя {user_id} изменена на {new_role}.")
    except ValueError:
        await update.message.reply_text("Некорректный ID пользователя.")

    return ConversationHandler.END





async def delete_user_start(update: Update, context: CallbackContext) -> int:
    if get_user_role(update.message.from_user.id) != "developer":
        await update.message.reply_text("У вас нет прав для удаления пользователей.")
        return ConversationHandler.END

    await update.message.reply_text("Введите ID пользователя для удаления:")
    return DELETE_USER


async def delete_user_main(update: Update, context: CallbackContext) -> int:
    user_id = update.message.text

    try:
        user_id = int(user_id)
        delete_user(user_id)
        logger.info(f"Пользователь {user_id} Удалён")
        await update.message.reply_text(f"Пользователь {user_id} удален.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при удалении пользователя: {e}")

    return ConversationHandler.END


async def list_users(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    roles = get_user_role(user_id)
    user = update.message.from_user
    if roles == 'developer':
        users = get_all_users()
        logger.info(f"Пользователь {user.username} ({user.id}) Запросил список пользователей")
        response = "Список пользователей:\n"
        for user in users:
            response += f"ID: {user[0]}, Telegram: {user[1]}, Nick_Name: {user[2]}, Dostup: {user[3]}, Server:{user[4]}\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Отказано в доступе")

async def list_users_admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    roles = get_user_role(user_id)
    user = update.message.from_user
    if roles == 'developer'  or roles == 'admin':
        users = get_all_users()
        logger.info(f"Пользователь {user.username} ({user.id}) Запросил список пользователей")
        response = "Список пользователей:\n"
        for user in users:
            response += f"ID: {user[0]}, Nick_Name: {user[2]}, Dostup: {user[3]}, Server:{user[4]}\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Отказано в доступе")






async def back_to_main(update: Update, context: CallbackContext) -> None:
    await log_button_press(update, context)
    await start(update, context)


def main() -> None:
    init_db()

    application = Application.builder().token(API_KEY).build()

    report_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Выгрузка репорта📖$") & admin_d, date_from_report)],
        states={
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_from_report)],
            DATE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_to_report)],
            NICKNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, nicknames_report)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    invite_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Принятие во фракцию🚪$") , date_from_invites)],
        states={
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_from_invites)],
            DATE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_to_invites)],
            NICKNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, nicknames_invites)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    uval_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Увольнения с фракции✏️$"), date_from_uval)],
        states={
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_from_uval)],
            DATE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_to_uval)],
            NICKNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, nicknames_uval)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    online_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Проверить онлайн⏰$"), online_check_start)],
        states={
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, online_date_from)],
            DATE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, online_date_to)],
            NICKNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, online_nicknames)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    trade_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Проверить передачи🤑$'), trade_check_start)],
        states={
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_date_from)],
            DATE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_date_to)],
            NICKNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_nicknames)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    gospay_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Снятие денег с фракции💶$'), gos_start)],
        states={
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_from_gos)],
            DATE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_to_gos)],
            FRACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fraction)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    register_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_nickname)],
            SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_server)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    delete_user_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Удалить пользователя🚫$") , delete_user_start)],
        states={
            DELETE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_user_main)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    set_dostup = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Изменить доступ🔐$"), change_role_start)],
        states={
            ROLE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_role_user_id)],
            ROLE_NEW_ROLE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, change_role_new_role)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


    check_handler = get_conversation_handler()
    account_handler = accountc_handler()
    accban_handler = accountcc_handler()

    application.add_handler(accban_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Управление аккаунтами🔧$"), manage_accounts))
    application.add_handler(MessageHandler(filters.Regex("^Управление аккаунтами🔐$"), for_adm_acc_button))
    application.add_handler(MessageHandler(filters.Regex("^Список пользователей👨‍👨‍👧‍👦$"), list_users))
    application.add_handler(MessageHandler(filters.Regex("^Список пользователей👩‍👩‍👦‍👦$"), list_users_admin))
    application.add_handler(register_handler)
    application.add_handler(MessageHandler(filters.Regex("^Назад$"), back_to_main))
    application.add_handler(MessageHandler(filters.Regex("^Для следящих☠️$"), sled_button))
    application.add_handler(MessageHandler(filters.Regex("^Работа с аккаунтами🤖$"), for_account_button))
    application.add_handler(MessageHandler(filters.Regex('^Проверка кандидатов1️⃣3️⃣$'), acc_start))
    application.add_handler(MessageHandler(filters.Regex('^Выгрузка логов📖$'), send_file))
    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Список заявок🗒$"), list_pending_users)],
        states={},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    application.add_handler(CallbackQueryHandler(button_callback))

    application.add_handler(delete_user_handler)
    application.add_handler(invite_handler)
    application.add_handler(uval_handler)
    application.add_handler(report_handler)
    application.add_handler(online_handler)
    application.add_handler(trade_handler)
    application.add_handler(check_handler)
    application.add_handler(account_handler)
    application.add_handler(accban_handler)
    application.add_handler(set_dostup)
    application.add_handler(gospay_handler)

    application.run_polling()


if __name__ == "__main__":
    main()

