from database import is_slot_available
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def generate_times_keyboard(date, day_name):
    times = ["13:00", "15:00", "17:00", "19:00"]
    keyboard = []
    
    for time in times:
        is_available = await is_slot_available(date, time)
        text = f"{time} {'❌' if not is_available else '✅'}"
        callback = "unavailable" if not is_available else f"appoint_{date}_{time}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_days"),
        InlineKeyboardButton(text="На главную", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)