from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode, ContentType
from keyboards import *
from database import *
from config import ADMIN_ID
from datetime import datetime

router = Router()

# ========== Основные команды ==========
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я бот для записи на консультации. Выберите действие:",
        reply_markup=await main_menu(message.from_user.id)
    )

# ========== Система записи ==========
@router.callback_query(F.data == "week_appointments")
async def week_appointments(callback: CallbackQuery):
    await delete_expired_appointments()
    await callback.message.edit_text(
        "Выберите день недели:",
        reply_markup=await days_keyboard()
    )

@router.callback_query(F.data.startswith("day_"))
async def select_day(callback: CallbackQuery):
    date = callback.data.split("_")[1]
    day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
    await callback.message.edit_text(
        f"Выберите время для {day_name}:",
        reply_markup=await times_keyboard(date, day_name)
    )

@router.callback_query(F.data.startswith("appoint_"))
async def make_appointment(callback: CallbackQuery):
    user_id = callback.from_user.id
    existing = await get_user_appointment(user_id)
    if existing:
        await callback.answer(
            f"❌ У вас уже есть запись на {existing[1]} в {existing[2]}",
            show_alert=True
        )
        return
    
    _, date, time = callback.data.split('_')
    day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
    
    if not await is_slot_available(date, time):
        await callback.answer("Это время уже занято!", show_alert=True)
        return
        
    await add_appointment(
        user_id=user_id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
        date=date,
        day=day_name,
        time=time
    )
    
    # Уведомление пользователю
    await callback.message.answer(
        f"✅ Вы записаны на консультацию:\n"
        f"📅 {day_name}, {date}\n"
        f"⏰ {time}\n\n"
        f"Для отмены используйте /cancel",
        reply_markup=await main_menu(user_id)
    )
    
    # Уведомление админу
    if ADMIN_ID:
        await callback.bot.send_message(
            ADMIN_ID,
            f"📌 Новая запись:\n"
            f"👤 {callback.from_user.full_name} (@{callback.from_user.username})\n"
            f"📅 {day_name}, {date}\n"
            f"⏰ {time}\n"
            f"🆔 {user_id}"
        )
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=await times_keyboard(date, day_name)
    )

# ========== Отмена записи ==========
@router.message(Command("cancel"))
@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(update: Message | CallbackQuery):
    user_id = update.from_user.id
    if isinstance(update, CallbackQuery):
        message = update.message
        await update.answer()
    else:
        message = update
    
    appointment = await get_user_appointment(user_id)
    if not appointment:
        await message.answer("❌ У вас нет активных записей")
        return
    
    await cancel_appointment(user_id)
    await message.answer(
        f"❌ Запись на {appointment[1]} в {appointment[2]} отменена",
        reply_markup=await main_menu(user_id)
    )
    
    # Уведомление админу
    if ADMIN_ID:
        await message.bot.send_message(
            ADMIN_ID,
            f"❌ Отмена записи:\n"
            f"👤 {update.from_user.full_name}\n"
            f"🆔 {user_id}"
        )

# ========== Информация ==========
@router.callback_query(F.data == "about_me")
async def about_me(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ <b>Обо мне:</b>\n\n"
        "Мой таплинк https://taplink.cc/psereality\n\n"
        "📞 Контакты: @psy_birdy",
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_main()
    )

@router.callback_query(F.data == "support_author")
async def support_author(callback: CallbackQuery):
    await callback.message.edit_text(
        "💖 <b>Поддержать автора:</b>\n\n"
        "карта сбер: <code>2202202345909851</code>\n",
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_main()
    )

# ========== Навигация ==========
@router.callback_query(F.data == "back_to_main")
async def back_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=await main_menu(callback.from_user.id)
    )

@router.callback_query(F.data == "back_to_days")
async def back_days(callback: CallbackQuery):
    await delete_expired_appointments()
    await callback.message.edit_text(
        "Выберите день недели:",
        reply_markup=await days_keyboard()
    )

# ========== Обработка ошибок ==========
@router.callback_query(F.data == "unavailable")
async def unavailable(callback: CallbackQuery):
    await callback.answer("❌ Это время уже занято!", show_alert=True)

@router.callback_query()
async def unknown_callback(callback: CallbackQuery):
    await callback.answer("⚠️ Действие устарело. Обновите меню /start")

@router.message()
async def unknown_message(message: Message):
    await message.answer(
        "⚠️ Я не понимаю это сообщение.\n"
        "Используйте кнопки меню или команду /start",
        reply_markup=await main_menu(message.from_user.id)
    )

@router.message(Command("dbcheck"))
async def db_check(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("PRAGMA table_info(appointments)")
        columns = await cursor.fetchall()
        column_info = "\n".join([f"{col[1]} ({col[2]})" for col in columns])
        
        await message.answer(
            f"<b>Структура таблицы appointments:</b>\n"
            f"<code>{column_info}</code>\n\n"
            f"Всего колонок: {len(columns)}",
            parse_mode=ParseMode.HTML
        )
