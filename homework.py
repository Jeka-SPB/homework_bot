import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('YP_TOKEN')
TELEGRAM_TOKEN = os.getenv('TEL_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s - %(name)s'
)


def send_message(bot, message):
    """Вызывается из def main(). Бот отправляет сообщение."""
    try:
        logging.info('Bot sent message successfully')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error(f'Message not sent {error}')


def get_api_answer(current_timestamp) -> dict:
    """Вызывается из def main(). Запрос к АПИ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework.status_code == 200:
        logging.info('API receive')
        print(homework.json())
        return homework.json()
    if homework.status_code != 200:
        logging.error('server is not available')
        raise Exception('server is not available')


def check_response(response):
    """Вызывается из def main(). Проверяет АПИ на корректность."""
    if not isinstance(response, dict):
        logging.warning('dict not received')
        raise TypeError('dict not found')
    if not isinstance(response['homeworks'], list):
        logging.warning('list not received')
        raise TypeError('list not found')
    if isinstance(response, dict):
        logging.info('keys received')
        return response['homeworks']


def parse_status(homework):
    """Вызывается из def main(). Парсит результат АПИ."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}" - {verdict}'


def check_tokens() -> bool:
    """Проверяет обязательное наличие переменных окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical(
            'Проверить наличие переменных PRACTICUM_TOKEN,\
            TELEGRAM_TOKEN, \
            TELEGRAM_CHAT_ID'
        )
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_key_homeworks = check_response(response)
            parse_homeworks = parse_status(check_key_homeworks)
            send_message(bot, parse_homeworks)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
