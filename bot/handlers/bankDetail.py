from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select
from db.db import get_session
from utils.decorators import admin_only
from utils.logger import logger
from db.services.bank import fetch_banks
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from db.models import Bank, PaymentMethod
from bot.states import SetBankState
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.inline import cancel_keyboard, bank_menu
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command('getBanks'))
@router.message(F.text == 'Банки')
@admin_only()
async def handle_get_banks(message: types.Message, session: AsyncSession):
    banks = await fetch_banks(session)
    bank_names = "\n".join([bank.name for bank in banks])
    await message.answer(f"Список банков:\n<b>{bank_names}</b>", reply_markup=bank_menu)

@router.message(F.text == 'Создание банка')
@router.message(Command("setBank"))
@admin_only()
async def start_set_bank(message: Message, session: AsyncSession, state: FSMContext):
    await message.answer("Введите название нового банка:", reply_markup=cancel_keyboard)
    await state.set_state(SetBankState.name)

@router.message(SetBankState.name)
async def save_bank_name(message: Message, session: AsyncSession, state: FSMContext):
    name = message.text.strip()

    result = await session.execute(select(Bank).where(Bank.name == name))
    existing_bank = result.scalar()

    if existing_bank:
        await message.answer(f"Банк с названием «{name}» уже существует.", reply_markup=cancel_keyboard)
    else:
        new_bank = Bank(name=name)
        session.add(new_bank)
        try:
            await session.commit()
            await message.answer(f"Банк «{name}» успешно добавлен.", reply_markup=bank_menu)
        except IntegrityError:
            await session.rollback()
            await message.answer(f"Ошибка: не удалось добавить банк. Попробуйте снова.", reply_markup=cancel_keyboard)

    await state.clear()


@router.message(F.text == 'Удаление банка')
@router.message(Command("delete_bank"))
@admin_only()
async def delete_bank_start(message: Message, session: AsyncSession):
    result = await session.execute(select(Bank))
    banks = result.scalars().all()

    if not banks:
        await message.answer("Нет доступных банков для удаления.", reply_markup=cancel_keyboard)
        return

    builder = InlineKeyboardBuilder()
    for bank in banks:
        builder.button(text=bank.name, callback_data=f"delete_bank_{bank.id}")
    builder.adjust(1)

    await message.answer("Выберите банк для удаления:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("delete_bank_"))
@admin_only()
async def delete_bank_confirm(callback: CallbackQuery, session: AsyncSession):
    bank_id = int(callback.data.split("_")[-1])

    # Проверка на связанные реквизиты (если нужны)
    result = await session.execute(select(PaymentMethod).where(PaymentMethod.bank_id == bank_id))
    methods = result.scalars().all()

    if methods:
        await callback.message.answer("Нельзя удалить банк с существующими методами оплаты. Сначала удалите методы.", reply_markup=cancel_keyboard)
        await callback.answer()  # закрыть "часики"
        return

    result = await session.execute(select(Bank).where(Bank.id == bank_id))
    bank = result.scalar_one_or_none()

    if not bank:
        await callback.message.answer("Банк не найден.", reply_markup=cancel_keyboard)
        await callback.answer()
        return

    await session.delete(bank)
    await session.commit()

    await callback.message.answer(f"Банк '{bank.name}' успешно удалён.", reply_markup=bank_menu)
    await callback.answer()