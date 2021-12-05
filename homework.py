import json
import logging
import os
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('YP_TOKEN')
TELEGRAM_TOKEN = os.getenv('TEL_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 7200
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=10000,
    backupCount=1
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Вызывается из def main(). Бот отправляет сообщение."""
    try:
        logger.info('Bot sent message successfully')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Message not sent {error}')


def get_api_answer(current_timestamp) -> dict:
    """Вызывается из def main(). Запрос к АПИ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if homework.status_code == HTTPStatus.OK:
            logger.info('Url available')
            return homework.json()
    except requests.exceptions.RequestException as error:
        logger.error(f'URL not available {error}')
    except json.decoder.JSONDecodeError as error:
        logger.error(f'Json format not available {error}')
    if homework.status_code != HTTPStatus.OK:
        logger.error('server is not available')
        raise Exception('server is not available')


def check_response(response):
    """Вызывается из def main(). Проверяет АПИ на корректность."""
    if not isinstance(response, dict):
        logger.warning('type not dict')
        raise TypeError('type not dict')
    if 'homeworks' not in response:
        logger.warning('key not found')
        raise KeyError('key not found')
    if not isinstance(response['homeworks'], list):
        logger.warning('list not received')
        raise TypeError('list not found')
    if len(response) >= 0:
        logger.info('simple accepted')
        return response['homeworks']


def parse_status(homework):
    """Вызывается из def main(). Парсит результат АПИ."""
    if len(homework) == 0:
        logger.info('homework not checked')
        raise IndexError('homework not checked')
    homework = homework[0]
    if 'homework_name' not in homework:
        logger.error('homework_name not key')
        raise KeyError('key not found')
    if 'status' not in homework:
        logger.error('homework_name accepted')
        raise KeyError('key not found')
    homework_name = homework['homework_name']
    logger.info('homework_name accepted')
    homework_status = homework['status']
    logger.info('homework_status accepted')
    try:
        HOMEWORK_STATUSES
    except NameError:
        logger.error('HOMEWORK_STATUSES not found')
        raise NameError('HOMEWORK_STATUSES add')
    if len(HOMEWORK_STATUSES) <= 0:
        raise Exception('dict HOMEWORK_STATUSES empty')
    if not isinstance(HOMEWORK_STATUSES, dict):
        logger.warning('type not dict')
        raise TypeError('type not dict')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        logger.info('verdict accepted')
    logger.info('messange accepted')
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
            if check_tokens() is True:
                response = get_api_answer(current_timestamp)
                check_key_homeworks = check_response(response)
                parse_homeworks = parse_status(check_key_homeworks)
                send_message(bot, parse_homeworks)
                current_timestamp = int(time.time())
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Program crash: {error}'
            send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
