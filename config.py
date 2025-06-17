import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # Преобразуем в число
TIMEZONE = 'Europe/Moscow'  # Добавляем временную зону