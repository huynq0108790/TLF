import os

from dotenv import load_dotenv

load_dotenv()  # Tải các biến môi trường từ file .env

class Config:
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')
