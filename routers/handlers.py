# routers/handlers.py
import asyncio
import tracemalloc
from aiogram import Router, F
from aiogram.types import FSInputFile, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from config import photo_path, ADMIN, photo_payment_path , photo_wait_path
from keyboards.keyboards import *
from backend.snos import *
from backend.database import *
from backend.buySub import *
from backend.subscription import channel_subscription_required, force_check_subscription

tracemalloc.start()
router = Router()
photo = FSInputFile(photo_path)

# Фото для оплаты/покупки
photo_payment = FSInputFile(photo_payment_path)


class States(StatesGroup):
    VIOLATIONLINK = State()
    GIVESUBID = State()
    GIVESUBDAYS = State()
    CLOSESUB = State()


@router.message(CommandStart())
async def start(message: Message):
    """Команда /start - проверяет подписку на канал"""
    user_id = message.from_user.id
    await checkUser(userid=user_id)

    # Проверяем подписку на канал
    is_subscribed = await force_check_subscription(message.bot, user_id)

    # Получаем статус подписки из БД
    sub_status = await checkSubStatus(userid=user_id)
    if sub_status:
        date = await subDate(userid=user_id)
        status = f'Активна до {date}'
    else:
        status = 'Неактивна'

    # Статус подписки на канал
    channel_status = '✅ Подписан' if is_subscribed else '❌ Не подписан'

    markup = markupAdmin if user_id == ADMIN else markupUser

    await message.answer_photo(
        photo=photo,
        caption=f"<b>💼 Мой профиль\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"🆔 ID профиля: {user_id}\n"
                f"📢 Канал: {channel_status}\n"
                f"💎 Подписка: {status}\n➖➖➖➖➖➖➖➖➖➖➖➖</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )


@router.callback_query(F.data == 'check_subscription')
async def check_subscription(callback: CallbackQuery):
    """Проверка подписки по кнопке"""
    user_id = callback.from_user.id
    is_subscribed = await force_check_subscription(callback.bot, user_id)

    if is_subscribed:
        await callback.answer("✅ Вы подписаны на канал!", show_alert=True)
        await callback.message.delete()
        # Обновляем статус в БД через прямой запрос
        try:
            import aiosqlite
            from backend.database import DATABASE_PATH
            async with aiosqlite.connect(DATABASE_PATH) as con:
                await con.execute("UPDATE users SET sub = ? WHERE userid = ?", (True, user_id))
                await con.commit()
                print(f"Subscription status updated for {user_id}")
        except Exception as e:
            print(f"Error updating subscription: {e}")
        # Перезапускаем /start
        await start(callback.message)
    else:
        await callback.answer("❌ Вы не подписаны на канал! Подпишитесь и нажмите кнопку снова.", show_alert=True)


@router.callback_query(F.data == 'snos')
@channel_subscription_required()
async def handler_snos(callback: CallbackQuery, state: FSMContext):
    """Обработчик СНОСА - доступ только для подписанных на канал"""
    user_id = callback.from_user.id

    await callback.answer()
    await callback.message.delete()

    # Проверяем платную подписку
    check_status = await checkSubStatus(userid=user_id)

    if check_status:
        if await checkSubDate(userid=user_id):
            await callback.message.answer(
                "<b>📝 Отправьте жертву.\nПринимаются - Username,ссылка на чат\тгк, ссылка на бота</b>",
                parse_mode=ParseMode.HTML
            )
            await state.set_state(States.VIOLATIONLINK)
        else:
            await callback.message.answer(
                "<b>❌ У вас отсутствует подписка</b>",
                parse_mode=ParseMode.HTML
            )
    else:
        await callback.message.answer(
            "<b>❌ У вас отсутствует подписка</b>",
            parse_mode=ParseMode.HTML
        )


# routers/handlers.py - найдите функцию get_violation_link и исправьте

@router.message(States.VIOLATIONLINK)
async def get_violation_link(message: Message, state: FSMContext):
    """Получение ссылки на нарушение"""
    await state.clear()
    link = message.text.strip()

    # Проверяем ссылку
    if 't.me/' not in link:
        await message.answer(
            "❌ <b>Неверный формат ссылки!</b>\n\n"
            "Отправьте ссылку в формате:\n"
            "<code>https://t.me/username/123</code>",
            parse_mode=ParseMode.HTML
        )
        await state.set_state(States.VIOLATIONLINK)
        return

    start_msg = await message.answer(

        "<b>😶‍🌫️ Начинаю подачу жалоб...</b>\n\n⏳ Ожидайте, процесс может занять до 40 секунд",
        parse_mode=ParseMode.HTML
    )

    # Отправляем жалобы
    result = await report(link)

    await start_msg.delete()

    # Отправляем отчет пользователю
    await message.answer(
        f"<b>📄 Отчет:\n{result}</b>",
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == 'adminpanel')
async def handler_admin(callback: CallbackQuery):
    """Админ панель - доступ только для админа"""
    if callback.from_user.id != ADMIN:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "<b>🚀 Выберите действие</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=markupAdminPanel
    )


@router.callback_query(F.data == 'giveSub')
async def handler_give_sub(callback: CallbackQuery, state: FSMContext):
    """Выдача подписки админом"""
    if callback.from_user.id != ADMIN:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "<b>📝 Отправьте ID пользователя</b>",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(States.GIVESUBID)


@router.message(States.GIVESUBID)
async def give_id(message: Message, state: FSMContext):
    """Получение ID для выдачи подписки"""
    user_id = message.text.strip()
    await state.update_data(userid=user_id)
    await message.answer(
        "<b>📝 Отправьте количество дней подписки</b>",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(States.GIVESUBDAYS)


@router.message(States.GIVESUBDAYS)
async def give_days(message: Message, state: FSMContext):
    """Выдача подписки"""
    data = await state.get_data()
    user_id = data.get('userid')
    days = message.text.strip()
    await giveSub(user_id, days)
    await state.clear()
    await message.answer(
        f'<b>✅ Подписка пользователю {user_id} выдана</b>',
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == 'closeSub')
async def handler_close_sub(callback: CallbackQuery, state: FSMContext):
    """Закрытие подписки админом"""
    if callback.from_user.id != ADMIN:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "<b>📝 Отправьте ID пользователя</b>",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(States.CLOSESUB)


# routers/handlers.py - добавьте проверку перед отправкой

@router.message(States.VIOLATIONLINK)
async def get_violation_link(message: Message, state: FSMContext):
    """Получение ссылки на нарушение"""
    await state.clear()
    link = message.text.strip()

    # Проверяем формат ссылки
    if 't.me/' not in link:
        await message.answer(
            "❌ <b>Неверный формат ссылки!</b>\n\n"
            "Отправьте ссылку в формате:\n"
            "<code>https://t.me/username/123</code>\n\n"
            "Где:\n"
            "• <b>username</b> - имя канала или пользователя\n"
            "• <b>123</b> - ID сообщения (число)",
            parse_mode=ParseMode.HTML
        )
        await state.set_state(States.VIOLATIONLINK)
        return

    # Проверяем, что ID сообщения - число
    try:
        parts = link.split('/')
        message_id = int(parts[-1])
        if message_id <= 0:
            raise ValueError("ID должен быть положительным числом")
    except (ValueError, IndexError):
        await message.answer(
            "❌ <b>Неверный ID сообщения!</b>\n\n"
            "ID сообщения должен быть числом.\n"
            "Пример: <code>https://t.me/username/123</code>",
            parse_mode=ParseMode.HTML
        )
        await state.set_state(States.VIOLATIONLINK)
        return

    start_msg = await message.answer_photo(
        photo=photo_wait_path,
        caption="<b>😶‍🌫️ Начинаю подачу жалоб</b>",
        parse_mode=ParseMode.HTML
    )
    result = await report(link)
    await start_msg.delete()
    await message.answer(
        f"<b>📄 Отчет:\n{result}</b>",
        parse_mode=ParseMode.HTML
    )
    await message.bot.send_photo(
        ADMIN,
        photo=photo,
        caption=f"<b>📄 Отчет о жалобе от пользователя {message.from_user.id}:\n{result}</b>",
        parse_mode=ParseMode.HTML
    )

@router.message(States.CLOSESUB)
async def close_subscription(message: Message, state: FSMContext):
    """Закрытие подписки"""
    await state.clear()
    user_id = message.text.strip()
    if await checkSubStatus(user_id):
        await closeSub(user_id)
        await message.answer(
            f"<b>Подписка пользователя {user_id} закрыта</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(
            f"<b>❌ У пользователя {user_id} отсутствует подписка</b>",
            parse_mode=ParseMode.HTML
        )


@router.callback_query(F.data == 'buySub')
async def buy_sub_menu(callback: CallbackQuery):
    """Меню покупки подписки - использует фото для оплаты"""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo_payment,  # 👈 Фото для оплаты
        caption="<b>💎 Выберите время подписки</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=markupBuySub
    )


@router.callback_query(F.data == 'BuySub1')
async def buy_sub_1(callback: CallbackQuery):
    """Покупка подписки 1$"""
    await callback.answer()
    await callback.message.delete()
    userid = callback.from_user.id
    invoice_url, invoice_id = await createCheck(userid=userid, amount=1.0)
    await callback.message.answer(
        f"<b>🧾 Оплатите чек {invoice_url} в течение 2 минут</b>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(120)
    payment_status = await check_payment(user_id=userid, days=7, invoice_id=invoice_id)
    if payment_status:
        await callback.message.answer(
            "<b>✅ Оплата прошла успешно, подписка выдана</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.answer(
            "<b>❌ Оплата не прошла в течение 2 минут</b>",
            parse_mode=ParseMode.HTML
        )


@router.callback_query(F.data == 'BuySub3')
async def buy_sub_3(callback: CallbackQuery):
    """Покупка подписки 3$"""
    await callback.answer()
    await callback.message.delete()
    userid = callback.from_user.id
    invoice_url, invoice_id = await createCheck(userid=userid, amount=3.0)
    await callback.message.answer(
        f"<b>🧾 Оплатите чек {invoice_url} в течение 2 минут</b>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(120)
    payment_status = await check_payment(user_id=userid, days=30, invoice_id=invoice_id)
    if payment_status:
        await callback.message.answer(
            "<b>✅ Оплата прошла успешно, подписка выдана</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.answer(
            "<b>❌ Оплата не прошла в течение 2 минут</b>",
            parse_mode=ParseMode.HTML
        )


@router.callback_query(F.data == 'BuySub6')
async def buy_sub_6(callback: CallbackQuery):
    """Покупка подписки 6$"""
    await callback.answer()
    await callback.message.delete()
    userid = callback.from_user.id
    invoice_url, invoice_id = await createCheck(userid=userid, amount=6.0)
    await callback.message.answer(
        f"<b>🧾 Оплатите чек {invoice_url} в течение 2 минут</b>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(120)
    payment_status = await check_payment(user_id=userid, days=365, invoice_id=invoice_id)
    if payment_status:
        await callback.message.answer(
            "<b>✅ Оплата прошла успешно, подписка выдана</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.answer(
            "<b>❌ Оплата не прошла в течение 2 минут</b>",
            parse_mode=ParseMode.HTML
        )


@router.callback_query(F.data == 'BuySub10')
async def buy_sub_10(callback: CallbackQuery):
    """Покупка подписки 10$"""
    await callback.answer()
    await callback.message.delete()
    userid = callback.from_user.id
    invoice_url, invoice_id = await createCheck(userid=userid, amount=10.0)
    await callback.message.answer(
        f"<b>🧾 Оплатите чек {invoice_url} в течение 2 минут</b>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(120)
    payment_status = await check_payment(user_id=userid, days=10000, invoice_id=invoice_id)
    if payment_status:
        await callback.message.answer(
            "<b>✅ Оплата прошла успешно, подписка выдана</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.answer(
            "<b>❌ Оплата не прошла в течение 2 минут</b>",
            parse_mode=ParseMode.HTML
        )
