from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from database import is_slot_available  # Добавляем импорт0
from slot_service import check_slot_availability

def get_week_days():
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    days = []
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    
    for i in range(6):
        day_date = (next_monday + timedelta(days=i)).strftime('%Y-%m-%d')
        days.append({
            "name": day_names[i],
            "date": day_date
        })
    return days

async def main_menu(user_id: int):
    from database import get_user_appointment  # Локальный импорт
    has_appointment = await get_user_appointment(user_id)
    buttons = [
        [InlineKeyboardButton(text="📅 Записи на неделе", callback_data="week_appointments")],
        [InlineKeyboardButton(text="ℹ️ Обо мне", callback_data="about_me")],
        [InlineKeyboardButton(text="💖 Поддержать автора", callback_data="support_author")]
    ]
    if has_appointment:
        buttons.append([InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def days_keyboard():
    days = get_week_days()
    keyboard = []
    for day in days:
        keyboard.append([InlineKeyboardButton(
            text=day["name"], 
            callback_data=f"day_{day['date']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def times_keyboard(date: str, day_name: str):
    times = ["13:00", "15:00", "17:00", "19:00"]
    keyboard = []
    
    for time in times:
        is_available = await check_slot_availability(date, time)

async def times_keyboard(date: str, day_name: str):
    times = ["13:00", "15:00", "17:00", "19:00"]
    keyboard = []
    
    for time in times:
        is_available = await is_slot_available(date, time)  # Теперь функция доступна
        text = f"{time} {'❌' if not is_available else '✅'}"
        callback = "unavailable" if not is_available else f"appoint_{date}_{time}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_days"),
        InlineKeyboardButton(text="На главную", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")]
    ])

