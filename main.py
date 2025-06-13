import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers import router
from database import init_db
from config import ADMIN_ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    bot_info = await bot.get_me()
    logger.info(f"Бот @{bot_info.username} запущен!")
    print(f"✅ Бот @{bot_info.username} готов к работе")
    print(f"🆔 ID: {bot_info.id}")
    print(f"👋 Имя: {bot_info.first_name}")

async def main():
    try:
        # Инициализация базы данных
        await init_db()
        
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()
        dp.include_router(router)
        
        dp.startup.register(on_startup)
        logger.info("Запускаем бота...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        if 'bot' in locals():
            await bot.session.close()
            logger.info("Бот остановлен")

print(f"ADMIN_ID: {ADMIN_ID}")

if __name__ == '__main__':
    asyncio.run(main())