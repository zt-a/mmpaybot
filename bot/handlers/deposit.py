from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from config import ADMIN_ID, AUTO_DEPOSIT
from bot.states import DepositStates
from bot.keyboards.inline import get_admin_buttons, get_bank_keyboard
from db.models import Admin, Bank, PaymentMethod, DepositRequest, User
from db.services.admin import get_active_admin
from db.services.deposit import update_deposit_status
from db.services.user import get_or_create_user
from utils.logger import logger
from aiogram.filters import Command
from aiogram.types import FSInputFile
from config import MAX_AMOUNT, MIN_AMOUNT, SUPPORT, ADMIN_ID
from core.api.cashdesk_api import deposit_user, find_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.services.deposit import create_deposit  
from db.db import async_session
import re, os

router = Router()

command = 'deposit'
@router.message(F.text == "📥 Пополнить")
@router.message(Command(command))
async def deposit_start(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        user = await get_or_create_user(
            session, 
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        await message.answer("⚠️ Произошла ошибка при инициализации. Попробуйте позже.")
        return
    admin_telegram_id = await get_active_admin(session)
    if not admin_telegram_id:
        await message.answer("❌ Нет активного администратора. Попробуйте позже.")
        return
    logger.info(f"User {message.from_user.id} started deposit process.")
    caption = (
        "<b>📥 <u>Пополнение счёта</u></b>\n\n"
        "💳 Пожалуйста, введите <b>номер счёта</b> или <b>ID</b>, на который вы хотите пополнить баланс.\n\n"
        "📌 Убедитесь в правильности данных перед продолжением."
    )
    try:
        photo = FSInputFile("bot/img/login_img.jpg")
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
    except FileNotFoundError:
        logger.warning("Image img/login_img.jpg not found.")
        await message.answer(caption, parse_mode="HTML")
    await state.set_state(DepositStates.waiting_for_account)

@router.message(DepositStates.waiting_for_account)
async def deposit_account(message: types.Message, state: FSMContext):
    
    if not message.text.isdigit() or len(message.text) != 9:
        await message.answer(
            "❌ ID должен содержать только 9 цифр.\n"
            "Пожалуйста, введите корректный ID пользователя."
        )
        return

    user_id = int(message.text)
    user = await find_user(user_id)

    if not user or user.get('UserId') == 0:
        await message.answer(
            "❌ Пользователь с таким ID не найден.\n"
            "Пожалуйста, проверьте номер и введите снова."
        )
        return  

    await state.update_data(account=str(user_id))
    await message.answer(f"{user.get('UserId')}: {user.get('Name', 'Имя не указано')}")
    await message.answer(
        f"💸 <b>Введите сумму для пополнения (от {MIN_AMOUNT} до {MAX_AMOUNT} сом):</b>",
        parse_mode="HTML",
    )
    await state.set_state(DepositStates.waiting_for_amount)




@router.message(DepositStates.waiting_for_amount)
async def deposit_amount(message: types.Message, state: FSMContext, session: AsyncSession):
    if (
        not message.text.isdigit()
        or int(message.text) < MIN_AMOUNT
        or int(message.text) > MAX_AMOUNT
    ):
        logger.warning(
            f"User {message.from_user.id} entered invalid deposit amount: {message.text}"
        )
        await message.answer(
            f"⚠️ Введите корректную сумму (число от {MIN_AMOUNT} до {MAX_AMOUNT}).",
            parse_mode="HTML",
        )
        return

    await state.update_data(amount=message.text)
    logger.info(
        f"User {message.from_user.id} entered deposit amount: {message.text}"
    )


    keyboard = await get_bank_keyboard(session)
    await message.answer(
        "🏦 <b>Выберите банк для пополнения:</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(DepositStates.waiting_for_bank_choice)

@router.callback_query(DepositStates.waiting_for_bank_choice)
async def handle_bank_choice(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await call.answer()
    bank_name = call.data.replace("bank_", "")

    data = await state.get_data()
    amount = int(data["amount"])

    bank = await session.scalar(
        select(Bank).where(func.lower(Bank.name) == bank_name.lower())
    )
    if not bank:
        await call.message.answer("⚠️ Банк не найден в базе.")
        return

    payment_method = await session.scalar(
        select(PaymentMethod)
        .where(PaymentMethod.bank_id == bank.id, PaymentMethod.is_active == True)
        .limit(1)
    )
    if not payment_method:
        await call.message.answer("⚠️ Для выбранного банка нет активного реквизита.")
        return

    await state.update_data(payment_method_id=payment_method.id)

    caption = (
        f"<b>📲 Реквизиты для оплаты через {bank.name} ({payment_method.title})</b>\n\n"
        f"👤 <b>Получатель:</b> <code>{data.get('account') or 'не указан'}</code>\n"
        f"📞 <b>Телефон:</b> +996 <code>{payment_method.phone_number or 'не указан'}</code>\n"
        f"💳 <b>Номер счёта:</b> <code>{payment_method.account_number or 'не указан'}</code>\n"
        # f"🔗 <b>Ссылка на оплату:</b> {payment_method.payment_url or 'не указана'}\n"
        # f"📝 <b>Комментарий:</b> {payment_method.comment or 'нет'}\n"
    )


    try:
        photo = FSInputFile(payment_method.qr_photo)
        await call.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
    except FileNotFoundError:
        logger.warning(f"Image {payment_method.qr_photo} not found.")
        await call.message.answer(caption, parse_mode="HTML")

    await call.message.answer(
        "📷 <b>Пожалуйста, отправьте скриншот или фото чека:</b>",
        parse_mode="HTML",
    )
    await state.set_state(DepositStates.waiting_for_receipt)


@router.message(DepositStates.waiting_for_receipt, F.photo)
async def deposit_receipt(message: types.Message, state: FSMContext, bot, session: AsyncSession):
    from db.services.admin import get_active_admin  # если ты вынес эту функцию

    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    user_id = message.from_user.id
    account_id = str(data.get("account"))
    amount = float(data.get("amount"))
    payment_method_id = int(data.get("payment_method_id"))

    user = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )
    db_user_id = user.id  # <-- этот id и надо передавать в create_deposit
    try:

        deposit = await create_deposit(
            session=session,
            user_id=db_user_id,  # правильный внешний ключ
            account_id=str(account_id),
            amount=amount,
            receipt_photo=photo_id,
            status='pending'
        )
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        return
    except Exception as e:
        logger.error(f"Error creating withdraw: {e}")
        await message.answer("❌ Произошла ошибка при создании заявки")
        return

    # Получаем активного админа
    admin_telegram_id = await get_active_admin(session)
    if not admin_telegram_id:
        await message.answer("❌ Нет активного администратора. Попробуйте позже.")
        return
    
    text = ""
    if AUTO_DEPOSIT:
        text = "❌ <b>Авто пополнение отключен, пополните счёт в ручную!</b>"
    text = (
        f"<b>📥 Новая заявка на пополнение</b>\n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.full_name} (ID: <code>{user_id}</code>)\n"
        f"🧾 <b>Счёт/ID:</b> <code>{deposit.account_id}</code>\n"
        f"💰 <b>Сумма:</b> {deposit.amount} сом\n"
        f"📌 <b>Заявка №{deposit.id}</b>\n\n"
        f"🔍 Проверьте чек и подтвердите.\n" + text
    )

    await bot.send_photo(
        chat_id=admin_telegram_id,
        photo=photo_id,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_admin_buttons(deposit.id, command),
    )

    await message.answer(
        "✅ <b>Заявка отправлена администратору!</b>\n⏳ Ожидайте подтверждения.\n🛟 SUPPORT: " + SUPPORT,
        parse_mode="HTML",
    )

    await state.clear()


@router.callback_query(F.data.startswith(f"approve_{command}:"))
async def approve_deposit(call: types.CallbackQuery, bot, session: AsyncSession):
    deposit_id = int(call.data.split(":")[1])
    logger.info(f"Admin approved deposit USER ID {deposit_id}")

    # Получаем заявку на пополнение
    query = select(DepositRequest).where(DepositRequest.id == deposit_id)
    result = await session.execute(query)
    deposit = result.scalar_one_or_none()

    if not deposit:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    # Получаем админа
    query = select(Admin).where(Admin.telegram_id == call.from_user.id)
    result = await session.execute(query)
    admin = result.scalar_one_or_none()

    if not admin:
        await call.answer("❌ Администратор не найден", show_alert=True)
        return

    admin_id = admin.id
    admin_telegram_id = await get_active_admin(session)

    # Зачисляем средства пользователю
    try:
        deposit_request = await deposit_user(user_id=deposit.account_id, summa=deposit.amount)
        await update_deposit_status(session, deposit.id, "approved", confirmed_by=admin_id)
        if deposit_request == {}:
            if admin_telegram_id:
                await bot.send_message(
                    chat_id=admin_telegram_id,
                    text="<b>Авто пополнение отключен, пополните счёт в ручную!</b>",
                    parse_mode="HTML",
                )
    except Exception as e:
        logger.error(f"Ошибка при зачислении средств: {e}")
        await call.answer("❌ Ошибка при зачислении средств", show_alert=True)
        return
    

    query = select(User).where(User.id == deposit.user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        await call.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text="✅ <b>Ваша заявка на пополнение подтверждена!</b>",
            parse_mode="HTML",
        )
        if admin_telegram_id:
            await bot.send_message(
                chat_id=admin_telegram_id,
                text="✅ <b>Заявка подтверждена!</b>",
                parse_mode="HTML",
            )

        caption = call.message.caption or ""
        await call.message.edit_caption(
            caption,
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка подтверждена ✅")
    except Exception as e:
        logger.error(f"Error sending approval: {e}")
        await call.answer(f"Ошибка: {e}", show_alert=True)
        
        
@router.callback_query(F.data.startswith(f"decline_{command}:"))
async def decline_deposit(call: types.CallbackQuery, bot, session: AsyncSession):
    deposit_id = int(call.data.split(":")[1])
    logger.info(f"Admin declined deposit ID {deposit_id}")

    query = select(DepositRequest).where(DepositRequest.id == deposit_id)
    result = await session.execute(query)
    deposit = result.scalar_one_or_none()

    if not deposit:
        await call.answer("Заявка не найдена", show_alert=True)
        return
    
    query = select(Admin).where(Admin.telegram_id == call.from_user.id)
    result = await session.execute(query)
    admin = result.scalar_one_or_none()

    if not admin:
        await call.answer("❌ Администратор не найден", show_alert=True)
        return

    admin_id = admin.id
    await update_deposit_status(session, deposit.id, "declined", confirmed_by=admin_id)

    query = select(User).where(User.id == deposit.user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        await call.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text="❌ <b>Ваша заявка на пополнение отклонена!</b>",
            parse_mode="HTML",
        )
        admin_telegram_id = await get_active_admin(session)
        if admin_telegram_id:
            await bot.send_message(
                chat_id=admin_telegram_id,
                text="❌ <b>Заявка отклонена!</b>",
                parse_mode="HTML",
            )
        caption = call.message.caption or ""
        await call.message.edit_caption(
            caption,
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка отклонена ❌")
    except Exception as e:
        logger.error(f"Error sending decline: {e}")
        await call.answer(f"Ошибка: {e}", show_alert=True)
