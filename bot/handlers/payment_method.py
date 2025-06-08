from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.filters import Command
from sqlalchemy import select
from db.models import Bank, PaymentMethod
from db.db import get_session
from bot.states import SetPaymentMethodState
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from uuid import uuid4
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.inline import method_menu, cancel_keyboard, menu, bank_menu

from db.services.payment import activate_payment_method_by_id, get_or_create_paymentMethod
from utils.decorators import admin_only

router = Router()


@router.message(F.text == 'Реквезиты')
@router.message(Command("getMethods"))
@admin_only()
async def get_methods(message: Message, session: AsyncSession):
    result = await session.execute(select(Bank))
    banks = result.scalars().all()

    if not banks:
        await message.answer("Нет доступных банков.")
        return

    builder = InlineKeyboardBuilder()
    for bank in banks:
        builder.button(text=bank.name, callback_data=f"get_methods_{bank.id}")
    builder.adjust(1)

    await message.answer("Выберите банк, чтобы посмотреть его методы оплаты:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("get_methods_"))
@admin_only()
async def show_methods(callback: CallbackQuery, session: AsyncSession):
    bank_id = int(callback.data.split("_")[-1])

    result = await session.execute(
        select(PaymentMethod).where(PaymentMethod.bank_id == bank_id, PaymentMethod.is_active == True)
    )
    methods = result.scalars().all()

    if not methods:
        await callback.message.answer("У этого банка нет активных методов оплаты.", reply_markup=method_menu)
        return

    for method in methods:
        text = (
            f"<b>Название:</b> {method.title}\n"
            f"<b>Тип:</b> {method.type or '-'}\n"
            f"<b>Счёт/Карта:</b> {method.account_number or '-'}\n"
            f"<b>Телефон:</b> {method.phone_number or '-'}\n"
            f"<b>Имя владельца:</b> {method.holder_name or '-'}\n"
            f"<b>Активен :</b> {method.is_active or '-'}"
        )
        if method.qr_photo and os.path.exists(method.qr_photo):
            photo = FSInputFile(method.qr_photo)
            await callback.message.answer_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=method_menu)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=method_menu)


@router.message(F.text == 'Создание реквезита')
@router.message(Command("setMethod"))
async def start_add_method(message: Message, state: FSMContext, session: AsyncSession):
    result = await session.execute(select(Bank))
    banks = result.scalars().all()

    if not banks:
        await message.answer("Нет доступных банков. Сначала добавьте банк.", reply_markup=bank_menu)
        return

    builder = InlineKeyboardBuilder()
    for bank in banks:
        builder.button(text=bank.name, callback_data=f"select_bank_{bank.id}")
    builder.adjust(1)

    await message.answer("Выберите банк для добавления метода оплаты:", reply_markup=builder.as_markup())
    await state.set_state(SetPaymentMethodState.choosing_bank)

@router.callback_query(F.data.startswith("select_bank_"))
async def bank_selected(callback: CallbackQuery, state: FSMContext):
    bank_id = int(callback.data.split("_")[-1])
    await state.update_data(bank_id=bank_id)
    await callback.message.answer("Введите название метода оплаты:", reply_markup=cancel_keyboard)
    await state.set_state(SetPaymentMethodState.title)

@router.message(SetPaymentMethodState.title)
async def set_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите тип метода (например, Карта, Электронный кошелёк):", reply_markup=cancel_keyboard)
    await state.set_state(SetPaymentMethodState.type)

@router.message(SetPaymentMethodState.type)
async def set_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer("Введите номер счёта/карты:", reply_markup=cancel_keyboard)
    await state.set_state(SetPaymentMethodState.account_number)

@router.message(SetPaymentMethodState.account_number)
async def set_account_number(message: Message, state: FSMContext):
    await state.update_data(account_number=message.text)
    await message.answer("Введите номер телефона:", reply_markup=cancel_keyboard)
    await state.set_state(SetPaymentMethodState.phone_number)

@router.message(SetPaymentMethodState.phone_number)
async def set_phone_number(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Введите имя владельца:", reply_markup=cancel_keyboard)
    await state.set_state(SetPaymentMethodState.holder_name)

@router.message(SetPaymentMethodState.holder_name)
async def set_holder_name(message: Message, state: FSMContext):
    await state.update_data(holder_name=message.text)
    await message.answer("Отправьте QR-код (фото):", reply_markup=cancel_keyboard)
    await state.set_state(SetPaymentMethodState.qr_photo)

@router.message(SetPaymentMethodState.qr_photo, F.photo)
async def set_qr_photo(message: Message, state: FSMContext, session: AsyncSession):
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    path = f"media/qr/{uuid4().hex}.jpg"
    await message.bot.download_file(file.file_path, path)

    await state.update_data(qr_photo=path)

    data = await state.get_data()

    method = await get_or_create_paymentMethod(
        session=session,
        title=data["title"],
        type=data["type"],
        account_number=data["account_number"],
        phone_number=data["phone_number"],
        holder_name=data["holder_name"],
        qr_photo=path,
        is_active=True,
        bank_id=data["bank_id"],
    )

    session.add(method)
    await session.commit()

    await message.answer("Метод оплаты успешно добавлен!", reply_markup=method_menu)
    await state.clear()

@router.message(SetPaymentMethodState.qr_photo)
async def no_photo(message: Message):
    await message.answer("Пожалуйста, отправьте именно изображение (QR-код).", reply_markup=cancel_keyboard)



@router.message(F.text == 'Активация реквезита')
@router.message(Command("activateMethod"))
@admin_only()
async def cmd_activate_method(message: Message, session: AsyncSession):
    result = await session.execute(select(Bank))
    banks = result.scalars().all()

    if not banks:
        await message.answer("Нет доступных банков.", reply_markup=bank_menu)
        return

    builder = InlineKeyboardBuilder()
    for bank in banks:
        builder.button(text=bank.name, callback_data=f"activate_bank_{bank.id}")
    builder.adjust(1)

    await message.answer("Выберите банк:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("activate_bank_"))
@admin_only()
async def activate_bank_callback(callback: CallbackQuery, session: AsyncSession):
    bank_id = int(callback.data.split("_")[-1])
    result = await session.execute(
        select(PaymentMethod).where(PaymentMethod.bank_id == bank_id)
    )
    methods = result.scalars().all()

    if not methods:
        await callback.message.answer("У этого банка нет методов оплаты.", reply_markup=method_menu)
        return

    builder = InlineKeyboardBuilder()
    for method in methods:
        status = "✅" if method.is_active else "❌"
        text = f"{status} {method.title} (ID: {method.id})"
        builder.button(text=text, callback_data=f"activate_method_{method.id}")
    builder.adjust(1)

    await callback.message.answer("Выберите метод оплаты для активации:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("activate_method_"))
@admin_only()
async def activate_method_callback(callback: CallbackQuery, session: AsyncSession):
    method_id = int(callback.data.split("_")[-1])
    activated_method = await activate_payment_method_by_id(session, method_id)
    if not activated_method:
        await callback.message.answer("Метод оплаты не найден.")
        return

    await callback.message.answer(f"Метод оплаты <b>{activated_method.title}</b> успешно активирован!", parse_mode="HTML")
    await callback.answer() 

@router.message(F.text == 'Удаление реквезита')
@router.message(Command("delete_method"))
@admin_only()
async def delete_method_start(message: Message, session: AsyncSession):
    result = await session.execute(select(PaymentMethod))
    methods = result.scalars().all()

    if not methods:
        await message.answer("Нет доступных методов оплаты для удаления.", reply_markup=method_menu)
        return

    builder = InlineKeyboardBuilder()
    for method in methods:
        text = f"{method.title} ({method.account_number})"
        builder.button(text=text, callback_data=f"delete_method_{method.id}")
    builder.adjust(1)

    await message.answer("Выберите метод оплаты для удаления:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("delete_method_"))
@admin_only()
async def delete_method_confirm(callback: CallbackQuery, session: AsyncSession):
    method_id = int(callback.data.split("_")[-1])

    result = await session.execute(select(PaymentMethod).where(PaymentMethod.id == method_id))
    method = result.scalar_one_or_none()

    if not method:
        await callback.message.answer("Метод оплаты не найден.", reply_markup=cancel_keyboard)
        await callback.answer()
        return

    await session.delete(method)
    await session.commit()

    await callback.message.answer(f"Метод оплаты '{method.title}' успешно удалён.", reply_markup=method_menu)
    await callback.answer()
