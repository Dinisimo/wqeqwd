import aiosqlite
from datetime import datetime
import logging
import pytz
from config import ADMIN_ID, TIMEZONE

logger = logging.getLogger(__name__)
DB_NAME = 'appointments.db'

async def init_db():
    """Инициализация базы данных с автоматической миграцией"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            logger.info("Создание таблиц...")
            await create_tables(db)
            return
        
        cursor = await db.execute("PRAGMA table_info(appointments)")
        columns = await cursor.fetchall()
        column_names = {col[1] for col in columns}
        required_columns = {'user_id', 'username', 'full_name', 'date', 'day', 'time'}
        
        if not required_columns.issubset(column_names):
            logger.warning("Обнаружена устаревшая структура таблицы, выполняется миграция...")
            await migrate_database(db)

async def migrate_database(db):
    try:
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
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS blocked_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                reason TEXT,
                blocked_by INTEGER NOT NULL,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        await db.execute('''
            INSERT INTO new_appointments (id, user_id, date, day, time, created_at)
            SELECT id, user_id, date, day, time, created_at FROM appointments
        ''')
        
        await db.execute('DROP TABLE appointments')
        await db.execute('ALTER TABLE new_appointments RENAME TO appointments')
        await db.commit()
        logger.info("Миграция БД успешно завершена")
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка миграции БД: {e}")
        raise

async def create_tables(db):
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
    await db.execute('''
        CREATE TABLE IF NOT EXISTS blocked_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            reason TEXT,
            blocked_by INTEGER NOT NULL,
            blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        # Проверяем блокировку
        cursor = await db.execute('''
            SELECT * FROM blocked_slots 
            WHERE date = ? AND time = ?
        ''', (date, time))
        if await cursor.fetchone() is not None:
            return False
            
        # Проверяем занятость
        cursor = await db.execute('''
            SELECT * FROM appointments 
            WHERE date = ? AND time = ?
        ''', (date, time))
        return await cursor.fetchone() is None

async def block_slot(date: str, time: str, admin_id: int, reason: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO blocked_slots (date, time, reason, blocked_by)
            VALUES (?, ?, ?, ?)
        ''', (date, time, reason or "", admin_id))
        await db.commit()

async def unblock_slot(date: str, time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            DELETE FROM blocked_slots 
            WHERE date = ? AND time = ?
        ''', (date, time))
        await db.commit()

async def get_blocked_slots():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT date, time, reason, blocked_by FROM blocked_slots
        ''')
        return await cursor.fetchall()

async def delete_expired_appointments():
    now = datetime.now(pytz.timezone(TIMEZONE))
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            DELETE FROM appointments 
            WHERE datetime(date || ' ' || time) < datetime(?)
        ''', (now.strftime('%Y-%m-%d %H:%M'),))
        await db.commit()

async def init_db():
    """Инициализация базы данных с автоматической миграцией"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Проверяем существование всех таблиц
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in await cursor.fetchall()}
        
        # Если ни одной таблицы нет, создаем все с нуля
        if not existing_tables:
            logger.info("Создание таблиц с нуля...")
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
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blocked_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    reason TEXT,
                    blocked_by INTEGER NOT NULL,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            await db.commit()
            return
        
        # Если есть таблица appointments, но нет blocked_slots
        if 'appointments' in existing_tables and 'blocked_slots' not in existing_tables:
            logger.info("Создание таблицы blocked_slots...")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blocked_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    reason TEXT,
                    blocked_by INTEGER NOT NULL,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            await db.commit()
        
        # Проверяем структуру таблицы appointments
        cursor = await db.execute("PRAGMA table_info(appointments)")
        columns = await cursor.fetchall()
        column_names = {col[1] for col in columns}
        required_columns = {'user_id', 'username', 'full_name', 'date', 'day', 'time'}
        
        if not required_columns.issubset(column_names):
            logger.warning("Обнаружена устаревшая структура таблицы appointments, выполняется миграция...")
            await migrate_database(db)