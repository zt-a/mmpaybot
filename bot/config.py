from dotenv import load_dotenv
import os

load_dotenv() 

TOKEN = str(os.getenv('TOKEN'))
ADMIN_ID = str(os.getenv('ADMIN_ID'))
MAX_AMOUNT = int(os.getenv('MAX_AMOUNT'))
MIN_AMOUNT = int(os.getenv('MIN_AMOUNT'))
SUPPORT = str(os.getenv('SUPPORT'))

DB_USER = str(os.getenv('DB_USER'))
DB_PASS = str(os.getenv('DB_PASS'))
DB_HOST = str(os.getenv('DB_HOST'))
DB_PORT = str(os.getenv('DB_PORT'))
DB_NAME = str(os.getenv('DB_NAME'))