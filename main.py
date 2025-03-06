import requests
import os
from time import sleep
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()
DEVMAN_API = os.getenv("DEVMAN_API")
TG_API = os.getenv("TG_API")

if not DEVMAN_API:
    logging.error(
        "DEVMAN_API не был найден. Пожалуйста, напишите DEVMAN_API в .env")
    exit(1)
if not TG_API:
    logging.error(
        "TG_API токен не был найден. Пожалуйста, напишите TG_API в .env")
    exit(1)


def fetch_reviews(url, token, params=None):
    headers = {"Authorization": f"Token {token}"}
    try:
        response = requests.get(url, headers=headers,
                                params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as error:
        logging.error(f"HTTP Error: {error}")
        raise
    except requests.exceptions.ReadTimeout as error:
        logging.error(f"Read Timeout: {error}")
        raise
    except requests.exceptions.ConnectionError as error:
        logging.error(f"Connection Error: {error}")
        raise


def search_changes(context: CallbackContext):
    URL = "https://dvmn.org/api/long_polling/"
    params = {}
    chat_id = context.job.context

    while True:
        try:
            data = fetch_reviews(URL, DEVMAN_API, params)
            logging.debug(f"Response: {data}")
            if data["status"] == "found":
                logging.info(f"Новая попытка: {data['new_attempts']}")
                for attempt in data["new_attempts"]:
                    message = (
                        f"У Вас проверили работу «{attempt['lesson_title']}» {attempt['lesson_url']}\n\n"
                        f"{'Преподавателю все понравилось, можно приступать к следующему уроку!' if not attempt['is_negative'] else 'К сожалению, в работе нашлись ошибки'}\n"
                    )
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=message)
                params["timestamp"] = data["last_attempt_timestamp"]
            elif data["status"] == "timeout":
                params["timestamp"] = data["timestamp_to_request"]
        except (requests.exceptions.HTTPError, requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as error:
            logging.error(f"Error: {error}")
            sleep(5)
            continue
        except Exception as e:
            logging.error(f"Error: {e}")
            sleep(5)
            continue


def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    update.message.reply_text(
        "Начинаю поиск новых проверок!")

    if not context.chat_data.get("polling_started"):
        context.job_queue.run_repeating(
            search_changes,
            interval=1,
            first=0,
            context=chat_id
        )
        context.chat_data["polling_started"] = True
    else:
        update.message.reply_text("Проверка уже запущена!")


def main():
    updater = Updater(TG_API, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    logging.info("Bot is starting")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
