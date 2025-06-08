from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Bank

async def get_bank_keyboard(session: AsyncSession) -> InlineKeyboardMarkup:
    result = await session.scalars(select(Bank).order_by(Bank.name))
    banks = result.all()

    buttons = []
    for bank in banks:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏦 {bank.name}",
                callback_data=f"bank_{bank.name.lower()}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_buttons(user_id: int, action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить", callback_data=f"approve_{action}:{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"decline_{action}:{user_id}"
                ),
            ]
        ]
    )


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📥 Пополнить"),
            KeyboardButton(text="📤 Вывести"),
        ],
        [
            KeyboardButton(text="❌ Отменить"),
            KeyboardButton(text="🏠 Главное меню"),
        ],
    ],
    resize_keyboard=True,
)


bank_menu = ReplyKeyboardMarkup(
    keyboard=[
        [  
            KeyboardButton(text='Банки'),
            KeyboardButton(text='Создание банка'),
        ],
        [
            KeyboardButton(text='Удаление банка'),
            KeyboardButton(text='❌ Отменить'),
        ],
        [
            KeyboardButton(text="🏠 Главное меню"),
            KeyboardButton(text="Вход в админку"),
            
        ]
    ],
    resize_keyboard=True,
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Банки'),
            KeyboardButton(text='Реквезиты'),
        ],
        [
            KeyboardButton(text="Баланс"),
            KeyboardButton(text="Вход в админку"),
        ],
        [
            KeyboardButton(text="Выход с админки"),
            KeyboardButton(text='Удаление админа')
        ],
        [
            KeyboardButton(text="Автопополнение включить"),
            KeyboardButton(text='Автопополнение выключить')
        ],
        [
            KeyboardButton(text="Автовывод включить"),
            KeyboardButton(text='Автовывод выключить')
        ]
        
    ],
    resize_keyboard=True,
)

method_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Реквезиты'),
            KeyboardButton(text='Создание реквезита'),
            
        ],
        [
            KeyboardButton(text='Активация реквезита'),
            KeyboardButton(text="Удаление реквезита"),
        ],
        [
            KeyboardButton(text="❌ Отменить"),
            KeyboardButton(text="Вход в админку"),
        ],
    ],
    resize_keyboard=True,
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='❌ Отменить'),
        ],
        [
            KeyboardButton(text="Вход в админку"),
            KeyboardButton(text="🏠 Главное меню"),
        ]
    ],
    resize_keyboard=True,
)
