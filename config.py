import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
QNAP_HOST = os.getenv("QNAP_HOST", "http://192.168.0.198:8080")
QNAP_USERNAME = os.getenv("QNAP_USERNAME")
QNAP_PASSWORD = os.getenv("QNAP_PASSWORD")
QNAP_DOWNLOAD_PATH = os.getenv("QNAP_DOWNLOAD_PATH", "Download")
