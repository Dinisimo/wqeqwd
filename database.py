import aiosqlite
from datetime import datetime
import logging
from config import ADMIN_ID

logger = logging.getLogger(__name__)
DB_NAME = 'appointments.db'

async def init_db():
    """Инициализация базы данных с автоматической миграцией"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Включаем поддержку внешних ключей
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Проверка существования таблицы
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            logger.info("Создание таблиц...")
            await create_tables(db)
            return
        
        # Проверка структуры таблицы
        cursor = await db.execute("PRAGMA table_info(appointments)")
        columns = await cursor.fetchall()
        column_names = {col[1] for col in columns}
        required_columns = {'user_id', 'username', 'full_name', 'date', 'day', 'time'}
        
        if not required_columns.issubset(column_names):
            logger.warning("Обнаружена устаревшая структура таблицы, выполняется миграция...")
            await migrate_database(db)

async def migrate_database(db):
    """Миграция базы данных на новую структуру"""
    try:
        # Создаем временную таблицу с новой структурой
        await db.execute('''
            CREATE TABLE IF NOT EXISTS new_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                date TEXT NOT NULL,
                day TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Переносим данные
        await db.execute('''
            INSERT INTO new_appointments (id, user_id, date, day, time, created_at)
            SELECT id, user_id, date, day, time, created_at FROM appointments
        ''')
        
        # Удаляем старую таблицу и переименовываем новую
        await db.execute('DROP TABLE appointments')
        await db.execute('ALTER TABLE new_appointments RENAME TO appointments')
        await db.commit()
        logger.info("Миграция БД успешно завершена")
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка миграции БД: {e}")
        raise

async def create_tables(db):
    """Создание таблиц с правильной структурой"""
    await db.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            date TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    await db.commit()

async def add_appointment(user_id: int, username: str, full_name: str, date: str, day: str, time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO appointments (user_id, username, full_name, date, day, time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username or "", full_name or "", date, day, time))
        await db.commit()

async def cancel_appointment(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM appointments WHERE user_id = ?', (user_id,))
        await db.commit()

async def get_user_appointment(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT date, day, time FROM appointments 
            WHERE user_id = ?
        ''', (user_id,))
        return await cursor.fetchone()

async def is_slot_available(date: str, time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT * FROM appointments 
            WHERE date = ? AND time = ?
        ''', (date, time))
        return await cursor.fetchone() is None

async def delete_expired_appointments():
    now = datetime.now()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            DELETE FROM appointments 
            WHERE datetime(date || ' ' || time) < datetime(?)
        ''', (now.strftime('%Y-%m-%d %H:%M'),))
        await db.commit()

