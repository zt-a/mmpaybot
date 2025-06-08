from dotenv import load_dotenv
import os

load_dotenv()

# BOT
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = str(os.getenv('BOT_NAME'))
ADMIN_SECRET = str(os.getenv('ADMIN_SECRET'))
ADMIN_COMMAND = str(os.getenv('ADMIN_COMMAND'))
AUTO_DEPOSIT = bool(os.getenv('AUTO_DEPOSIT'))
AUTO_WITHDRAW = bool(os.getenv('AUTO_WITHDRAW'))

# API
API_URL = os.getenv("API_URL")
CASH_HASH = os.getenv("CASH_HASH")
CASH_PASS = os.getenv("CASH_PASS").strip()
CASH_LOGIN = os.getenv("CASH_LOGIN")
CASHDESK_ID = os.getenv("CASHDESK_ID")

# BOT_INFO
ADMIN_ID = str(os.getenv('ADMIN_ID'))
MAX_AMOUNT = int(os.getenv('MAX_AMOUNT'))
MIN_AMOUNT = int(os.getenv('MIN_AMOUNT'))
SUPPORT = str(os.getenv('SUPPORT'))

# DB
DB_URL = os.getenv("DB_URL")
DB_USER = str(os.getenv('DB_USER'))
DB_PASS = str(os.getenv('DB_PASS'))
DB_HOST = str(os.getenv('DB_HOST'))
DB_PORT = str(os.getenv('DB_PORT'))
DB_NAME = str(os.getenv('DB_NAME'))


def auto_PP(boolean: bool):
    AUTO_DEPOSIT = boolean
    return AUTO_DEPOSIT
    
def auto_VV(boolean: bool):
    AUTO_WITHDRAW = boolean
    return AUTO_WITHDRAW