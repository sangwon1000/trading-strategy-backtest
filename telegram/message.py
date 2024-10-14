import requests
import logging
import traceback
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN_1 = os.getenv('TOKEN_1')
CHAT_ID_1 = os.getenv('CHAT_ID_1')

TOKEN_0 = os.getenv('TOKEN_0')
CHAT_ID_0 = os.getenv('CHAT_ID_0')

def send_success_message(operation):
    message = f"{operation} success"
    TOKEN_1 = TOKEN_1
    CHAT_ID_1 = CHAT_ID_1        
    url = f"https://api.telegram.org/bot{TOKEN_1}/sendMessage?chat_id={CHAT_ID_1}&text={message}"
    res = requests.get(url).json() # this sends the message
    logging.info("Success Message sent")

def send_fail_message(operation):
    message = f"{operation} failed, {traceback.format_exc()}"
    TOKEN_0 = TOKEN_0
    CHAT_ID_0 = CHAT_ID_0
    url_0 = f"https://api.telegram.org/bot{TOKEN_0}/sendMessage?chat_id={CHAT_ID_0}&text={message}"
    res = requests.get(url_0).json() # this sends the message
    logging.info(traceback.format_exc())
    logging.info("Fail Message sent")