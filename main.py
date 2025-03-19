import requests
from time import sleep
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import environ
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)


class LogHandler(logging.Handler):
    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception as e:
            print(f"Бот упал с ошибкой: {e}")


def get_checks(context: CallbackContext, devman_token):
    url = "https://dvmn.org/api/long_polling/"
    params = {}
    chat_id = context.job.context

    while True:
        try:
            response = requests.get(
                url, headers={"Authorization": f"Token {devman_token}"}, params=params)
            response.raise_for_status()
            fetched_checks = response.json()
            logger.debug(f"Response: {fetched_checks}")
            if fetched_checks["status"] == "found":
                logger.info(f"Новая попытка: {fetched_checks['new_attempts']}")
                for attempt in fetched_checks["new_attempts"]:
                    message = (
                        f"У Вас проверили работу «{attempt['lesson_title']}» {attempt['lesson_url']}\n\n"
                        f"""{'Преподавателю все понравилось, можно приступать к следующему уроку!'
                            if not attempt['is_negative'] else 'К сожалению, в работе нашлись ошибки'}\n"""
                    )
                    context.bot.send_message(chat_id=chat_id, text=message)
                params["timestamp"] = fetched_checks["last_attempt_timestamp"]
            elif fetched_checks["status"] == "timeout":
                params["timestamp"] = fetched_checks["timestamp_to_request"]
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError) as error:
            logger.error(f"Error: {error}")
            sleep(5)
            continue
        except Exception as e:
            logger.error(f"Error: {e}")
            sleep(5)
            continue


def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    devman_token = context.bot_data["devman_token"]
    update.message.reply_text(
        f"Начинаю поиск новых проверок!")
    logger.info(f"Бот запущен пользователен {chat_id}") 

    if not context.chat_data.get("polling_started"):
        context.job_queue.run_repeating(
            lambda x: get_checks(x, devman_token), interval=1, first=0, context=chat_id)
        context.chat_data["polling_started"] = True
    else:
        update.message.reply_text("Проверка уже запущена!")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    load_dotenv()
    devman_token = os.getenv("DEVMAN_TOKEN")
    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    admin_chat_id = os.getenv("ADMIN_CHAT_ID") 

    if not devman_token:
        logger.error("DEVMAN_TOKEN не найден в .env")
        return
    if not tg_bot_token:
        logger.error("TG_BOT_TOKEN не найден в .env")
        return
    if not admin_chat_id:
        logger.error("ADMIN_CHAT_ID не найден в .env")
        return
        
    updater = Updater(tg_bot_token, use_context=True)
    updater.dispatcher.bot_data["devman_token"] = devman_token
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    
    telegram_handler = TelegramLogHandler(updater.bot, admin_chat_id)
    telegram_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)
    logger.info("Бот начинается")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
