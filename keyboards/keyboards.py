from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT
from config import WORK
markupUser = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💣 Снос', callback_data='snos'),
         InlineKeyboardButton(text='👨‍💻 Поддержка', url=SUPPORT)],
        [InlineKeyboardButton(text="😁Работы", url=WORK)],
        [InlineKeyboardButton(text='💎 Купить подписку', callback_data='buySub')]

    ]
)

markupAdmin = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💣 Снос', callback_data='snos')],
        [InlineKeyboardButton(text="👨‍💻 Поддержка", url=SUPPORT)],
        [InlineKeyboardButton(text="😁Работы", url=WORK)],
        [InlineKeyboardButton(text='💎 Купить подписку', callback_data='buySub')],
        [InlineKeyboardButton(text='⚙️ Админ панель', callback_data='adminpanel')]
    ]
)

markupBuySub = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💎 Неделя - 1$', callback_data='BuySub1'),
         InlineKeyboardButton(text='💎 Месяц - 3$', callback_data='BuySub3')],
        [InlineKeyboardButton(text='💎 Год - 6$', callback_data='BuySub6'),
         InlineKeyboardButton(text='💎 Навсегда - 10$', callback_data='BuySub10')],
        [InlineKeyboardButton(text='💎 Stars|NFT|Card', url=SUPPORT)]
    ]
)

markupAdminPanel = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='✅ Выдать подписку', callback_data='giveSub'),
         InlineKeyboardButton(text='❌ Забрать подписку', callback_data='closeSub')]
    ]
)
