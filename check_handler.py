import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler,  ConversationHandler, CallbackContext
from config import COOKIES
from dostups import *
import logging
from database import *
# Initialize the database
init_db()

# Constants for conversation states
NICKNAMES = range(1)
logger = logging.getLogger()

async def check_start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    roles = get_user_role(user_id)  # Assume get_user_role returns a string with the user's role
    user = update.message.from_user

    # Check the user's role
    if roles in ['sled', 'tech', 'admin', 'developer']:
        await update.message.reply_text(
            'Введите никнеймы (каждый новый ник на новой строке):',
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"Пользователь {user.username} ({user.id}) нажал на кнопку проверки привязок")
        return NICKNAMES  # Return state where the user can enter nicknames

    # If no suitable roles found, send access denied message
    await update.message.reply_text('Отказано в доступе')
    return ConversationHandler.END

async def get_player_id(nick, aserver) -> int:
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # only if necessary
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(service=service, options=options)
    url = f"https://rodina.logsparser.info/accounts?server_number={aserver}&name={nick}+"

    try:
        driver.get(url)
        for cookie in COOKIES:
            driver.add_cookie(cookie)
        driver.get(url)
        time.sleep(10)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        rows = list(soup.find_all('tr'))

        log_lines = []
        for row in rows:
            cells = row.find_all('td')[:-9]
            if cells:
                log_lines.append(' '.join(cell.get_text().strip() for cell in cells))

        if log_lines:
            first_row = log_lines[0]
            player_id = first_row.split()[0]
            return player_id
        return None
    finally:
        driver.quit()

async def check_nicknames(update: Update, context: CallbackContext) -> int:
    nicks = update.message.text.split('\n')
    nicks = [nick.strip() for nick in nicks]
    user_id = update.message.from_user.id
    aserver = get_server(user_id)
    for nick in nicks:
        checking_message = await update.message.reply_text(f'Начинаю проверку привязок для никнейма: {nick}')
        user = update.message.from_user
        logger.info(f"Пользователь {user.username} ({user.id}) начал проверку привязок {nick}")
        try:
            player_id = await get_player_id(nick, aserver)
            if not player_id:
                await checking_message.edit_text(f'Не удалось найти ID для никнейма {nick}')
                continue

            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # only if necessary
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')

            driver = webdriver.Chrome(service=service, options=options)
            url = f"https://rodina.logsparser.info/?server_number={aserver}&type%5B%5D=mail&type%5B%5D=password&type%5B%5D=vk_attach&type%5B%5D=vk_detach&type%5B%5D=googleauth_attach&type%5B%5D=googleauth_detach&sort=desc&player={player_id}&limit=1000"

            driver.get(url)
            for cookie in COOKIES:
                driver.add_cookie(cookie)
            driver.get(url)
            time.sleep(10)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            rows = list(soup.find_all('tr'))

            log_lines = []
            for row in rows:
                cells = row.find_all('td')[:-2]
                if cells:
                    log_lines.append(' '.join(cell.get_text().strip() for cell in cells))

            account_status = parse_account_activities(log_lines)
            result_message = (f"Привязки для никнейма {nick}({player_id}):\n"
                              f"Google Authenticator: {account_status['Google Authenticator']}\n"
                              f"ВКонтакте: {account_status['ВКонтакте']}\n"
                              f"Mail Address: {account_status['Mail Address']}\n"
                              f"Последнее изменение пароля: {account_status['Last Password Change']}")
            await checking_message.edit_text(result_message)
        except Exception as e:
            await checking_message.edit_text(f'Произошла ошибка при проверке привязок для никнейма {nick}: {e}')
        finally:
            driver.quit()
        user = update.message.from_user
        logger.info(f"Пользователь {user.username} ({user.id}) закончил проверку привязок {nick}")
    await update.message.reply_text('Выгрузка закончена.')
    from main import start
    await start(update, context)
    return ConversationHandler.END

def parse_account_activities(log_lines):
    account_status = {
        "Google Authenticator": "не привязан",
        "ВКонтакте": "не привязан",
        "Mail Address": "не привязан",
        "Last Password Change": "Пароль не изменялся"
    }

    for line in reversed(log_lines):
        if "привязал к своему аккаунту защиту Google Authenticator" in line:
            account_status["Google Authenticator"] = "привязан"
        elif "привязал к своему аккаунту страницу ВКонтакте" in line:
            vk_page = line.split(" страницу ВКонтакте ")[-1]
            account_status["ВКонтакте"] = vk_page.strip()
        elif "изменил почту" in line:
            new_email = line.split(" на ")[-1]
            account_status["Mail Address"] = new_email.strip()
        elif "изменил пароль на" in line:
            date_time = line.split("изменил пароль на")[0].strip()
            account_status["Last Password Change"] = date_time

    return account_status

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def get_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Проверить привязки🔗$'), check_start)],
        states={
            NICKNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_nicknames)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
