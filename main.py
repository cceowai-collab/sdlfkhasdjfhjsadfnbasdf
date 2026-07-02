# main.py
from aiogram import Bot, Dispatcher
from config import TOKEN
import asyncio
from routers.handlers import router
from backend.database import createDatabase  # 👈 Используем createDatabase вместо init_db

async def main():
    # Создаем базу данных
    await createDatabase()
    
    # Запускаем бота без прокси
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
