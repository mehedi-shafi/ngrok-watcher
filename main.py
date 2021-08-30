import logging
import warnings
from logging.handlers import TimedRotatingFileHandler
from time import time
import telegram
import json
import os
import ntpath
import sys
import requests
from datetime import datetime

with open('conf.json', 'r') as file:
    config = json.load(file)

def get_logger(file_name):
    warnings.filterwarnings("ignore")
    script_path = os.path.dirname(os.path.abspath(file_name))
    head, script_name = ntpath.split(script_path)

    LOG_DIRECTORY = os.path.join(script_path, 'logs')
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    LOG_FILE = os.path.join(LOG_DIRECTORY, f'{script_name}.log')
    FORMATTER = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    def get_console_handler():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(FORMATTER)
        return console_handler

    def get_file_handler():
        file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
        file_handler.setFormatter(FORMATTER)
        return file_handler

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # better to have too much log than not enough
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger


logger = get_logger(__file__)


def send_message(message_body):
    logger.info('Telegram bot initializing')
    bot = telegram.Bot(token=config['token'])
    logger.info('Bot initialized')

    logger.info(f'Sending message: {message_body}')
    bot.sendMessage(chat_id=config['chat_id'], text=message_body)
    logger.info(f'Message sent')


def generate_dynamic_url_message(dynamic_url):
    message = f'''
    Ngrok Dynamic URL has been changed.
    New Url: {dynamic_url}
    '''
    return message

def get_current_config():
    file_path = config['config_file']
    if not os.path.exists(file_path):
        with open(file_path, 'w+') as file:
            json.dump({}, file)
        return {}

    with open(file_path, 'r') as file:
        return json.load(file)

def update_config():
    current_config = get_current_config()

    response = requests.get('http://localhost:4040/api/tunnels').json()

    if current_config == {} or current_config['tunnels'][0]['public_url'] != response['tunnels'][0]['public_url']:
        logger.info('Configuration file changed')

        logger.info('Dumping latest configuration to file')
        with open(config['config_file'], 'w+') as file:
            json.dump(response, file)

        logger.info('Dumping latest configuration completed')
        logger.info('Sending updated URL to telegram')
        send_message(generate_dynamic_url_message(response['tunnels'][0]['public_url']))


if __name__ == '__main__':
    logger.info(f'Checking for dynamic url update on {datetime.now()}') 

    update_config()


    logger.info('Finished')

