from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE
from database import is_slot_available

def get_week_days():
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz)
    current_weekday = today.weekday()  # 0-понедельник, 6-воскресенье
    
    days = []
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    
    # Начинаем с сегодняшнего дня или ближайшего понедельника
    start_date = today - timedelta(days=current_weekday)
    
    for i in range(6):  # Понедельник-Суббота
        day_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        day_name = day_names[i]
        
        # Если день сегодняшний, добавляем пометку
        if i == current_weekday:
            day_name += " (сегодня)"
        # Если день прошел, пропускаем
        elif (start_date + timedelta(days=i)).date() < today.date():
            continue
            
        days.append({
            "name": day_name,
            "date": day_date
        })
    
    return days

async def main_menu(user_id: int):
    from database import get_user_appointment
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
        is_available = await is_slot_available(date, time)
        if is_available:
            text = f"{time} ✅"
            callback = f"appoint_{date}_{time}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
    
    if not keyboard:
        keyboard.append([InlineKeyboardButton(text="Нет доступных слотов", callback_data="no_slots")])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_days"),
        InlineKeyboardButton(text="На главную", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")]
    ])