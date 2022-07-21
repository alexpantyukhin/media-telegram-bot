"""Settings for the app"""
import os

TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN') or ''

DESTINATION_PATH = os.getenv('DESTINATION_PATH') or ''
BUFFER_PATH = os.getenv('BUFFER_PATH') or ''
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH') or ''

EXPECT_SETTINGS = int(os.getenv('EXPECT_SETTINGS') or 60)

ALLOWED_ACCESS_IDS = os.getenv('ALLOWED_ACCESS_IDS') or ''
