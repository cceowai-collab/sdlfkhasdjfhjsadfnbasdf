from aiogram import Bot, Dispatcher
from config import TOKEN
import asyncio
from routers.handlers import router
from aiogram.client.session.aiohttp import AiohttpSession

dp = Dispatcher()

async def main():
    # Используем HTTP прокси (порт 10809)
    session = AiohttpSession(proxy="http://127.0.0.1:10809")

    bot = Bot(TOKEN, session=session)
    dp.include_router(router)
    await dp.start_polling(bot)


asyncio.run(main())