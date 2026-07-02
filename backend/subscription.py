# backend/subscription.py
from functools import wraps
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from backend.database import checkUser
from config import CHANNEL_ID, CHANNEL_LINK


def channel_subscription_required():
    """Декоратор для проверки подписки на канал"""

    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            # Определяем user_id и способ ответа
            if isinstance(event, Message):
                user_id = event.from_user.id
                reply_func = event.answer
                bot = event.bot
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id
                reply_func = event.message.answer
                bot = event.bot
                await event.answer()
            else:
                return await func(event, *args, **kwargs)

            # Проверяем пользователя в БД
            await checkUser(userid=user_id)

            # Проверяем подписку на канал
            is_subscribed = await check_channel_subscription(bot, user_id)

            if not is_subscribed:
                try:
                    await reply_func(
                        f"❌ <b>Для использования этой функции необходимо подписаться на наш канал!</b>\n\n"
                        f"📢 <b>Наш канал:</b> {CHANNEL_LINK}\n\n"
                        f"После подписки нажмите кнопку «✅ Проверить подписку»",
                        parse_mode="HTML",
                        reply_markup=await get_subscription_check_keyboard()
                    )
                except TelegramBadRequest as e:
                    print(f"Error sending subscription message: {e}")
                return None

            # Подписка есть - выполняем функцию
            return await func(event, *args, **kwargs)

        return wrapper

    return decorator


async def check_channel_subscription(bot, user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        if "user not found" in str(e).lower():
            print(f"User {user_id} not found in channel")
        else:
            print(f"Subscription check error for {user_id}: {e}")
        return False


async def get_subscription_check_keyboard():
    """Возвращает клавиатуру для проверки подписки"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from config import CHANNEL_LINK

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_LINK)
            ],
            [
                InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")
            ]
        ]
    )


async def force_check_subscription(bot, user_id: int) -> bool:
    """Принудительная проверка подписки"""
    return await check_channel_subscription(bot, user_id)
