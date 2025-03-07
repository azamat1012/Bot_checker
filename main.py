import requests
from time import sleep
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import environ

logger = logging.getLogger(__name__)


def get_checks(context: CallbackContext):
    URL = "https://dvmn.org/api/long_polling/"
    params = {}
    chat_id = context.job.context

    while True:
        try:
            response = requests.get(URL, DEVMAN_TOKEN, params)
            response.raise_for_status()
            fetched_checks = response.json()
            logger.debug(f"Response: {fetched_checks}")
            if fetched_checks["status"] == "found":
                logger.info(f"Новая попытка: {fetched_checks['new_attempts']}")
                for attempt in fetched_checks["new_attempts"]:
                    message = (
                        f"У Вас проверили работу «{attempt['lesson_title']}» {attempt['lesson_url']}\n\n"
                        f"{'Преподавателю все понравилось, можно приступать к следующему уроку!'
                            if not attempt['is_negative'] else 'К сожалению, в работе нашлись ошибки'}\n"
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
    update.message.reply_text("Начинаю поиск новых проверок!")

    if not context.chat_data.get("polling_started"):
        context.job_queue.run_repeating(
            get_checks, interval=1, first=0, context=chat_id)
        context.chat_data["polling_started"] = True
    else:
        update.message.reply_text("Проверка уже запущена!")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    DEVMAN_TOKEN

    if not DEVMAN_TOKEN:
        logger.error(
            "DEVMAN_API не был найден. Пожалуйста, напишите DEVMAN_API в .env")
        exit(1)
    if not TG_BOT_TOKEN:
        logger.error(
            "TG_BOT_TOKEN токен не был найден. Пожалуйста, напишите TG_BOT_TOKEN в .env")
        exit(1)

    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    logger.info("Bot is starting")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    env = environ.Env(
        DEBUG=(bool, False)
    )
    environ.Env.read_env()
    DEVMAN_TOKEN = env("DEVMAN_TOKEN")
    TG_BOT_TOKEN = env("TG_BOT_TOKEN")
    main()
