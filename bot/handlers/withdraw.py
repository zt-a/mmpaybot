from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import select
from config import ADMIN_ID, AUTO_WITHDRAW
from bot.keyboards.inline import get_admin_buttons
from core.api.cashdesk_api import find_user, payout_user
from db.models import Admin, Bank, PaymentUser, User, WithdrawRequest
from db.services.admin import get_active_admin
from db.services.withdraw import create_withdraw, update_withdraw_status
from utils.logger import logger
from aiogram.types import FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from bot.states import WithdrawStates
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery



from config import SUPPORT, ADMIN_ID, MAX_AMOUNT

MIN_AMOUNT = 150


router = Router()

command = 'withdraw'

@router.message(F.text == "📤 Вывести")
@router.message(Command(command))
async def withdraw_start(message: types.Message, state: FSMContext, session: AsyncSession):
        # Получаем активного админа
    admin_telegram_id = await get_active_admin(session)
    if not admin_telegram_id:
        await message.answer("❌ Нет активного администратора. Попробуйте позже.")
        return
    logger.info(f"User {message.from_user.id} started deposit process.")
    caption = (
        "<b>📥 <u>Вывод счёта</u></b>\n\n"
        "💳 Пожалуйста, введите <b>номер счёта</b> или <b>ID</b>, из который вы хотите вывести баланс.\n\n"
        "📌 Убедитесь в правильности данных перед продолжением."
    )
    try:
        photo = FSInputFile("bot/img/login_img.jpg")
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
    except FileNotFoundError:
        logger.warning("Image img/login_img.jpg not found.")
        await message.answer(caption, parse_mode="HTML")
    await state.set_state(WithdrawStates.waiting_for_account)


@router.message(WithdrawStates.waiting_for_account)
async def withdraw_account(message: types.Message, state: FSMContext):
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
    await message.answer(
        f"{user.get('UserId')}: {user.get('Name', 'Имя не указано')}\n"\
        f"💸 <b>Введите сумму для вывода (от {MIN_AMOUNT} до {MAX_AMOUNT} сом):</b>",
        parse_mode="HTML",
    )
    await state.set_state(WithdrawStates.waiting_for_amount)


@router.message(WithdrawStates.waiting_for_amount)
async def withdraw_amount(message: types.Message, state: FSMContext, session: AsyncSession):
    if (
        not message.text.isdigit()
        or int(message.text) < MIN_AMOUNT
        or int(message.text) > MAX_AMOUNT
    ):
        logger.warning(
            f"User {message.from_user.id} entered invalid withdraw amount: {message.text}"
        )
        await message.answer(
            f"⚠️ Введите корректную сумму (от {MIN_AMOUNT} до {MAX_AMOUNT}).",
            parse_mode="HTML",
        )
        return

    amount = int(message.text)
    await state.update_data(amount=amount)
    logger.info(f"User {message.from_user.id} entered withdraw amount: {amount}")

    # Получаем список банков из БД
    result = await session.execute(select(Bank))
    banks = result.scalars().all()

    if banks:
        buttons = [
            InlineKeyboardButton(text=bank.name, callback_data=f"bank_{bank.id}")
            for bank in banks
        ]

        # Разбиваем на ряды по 2 кнопки
        keyboard_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Банки не найдены", callback_data="no_bank")]
            ]
        )

    await message.answer(
        "🏦 <b>Выберите банк для получения средств:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_for_bank)

@router.callback_query(WithdrawStates.waiting_for_bank, F.data.startswith("bank_"))
async def process_bank_selection(callback: CallbackQuery, state: FSMContext):
    bank_id = int(callback.data.split("_")[1])
    await state.update_data(bank_id=bank_id)

    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "📱 <b>Введите номер телефона, привязанный к банку:</b>\n"
        "📌 Пример: +996702388466",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_for_phone)

@router.message(WithdrawStates.waiting_for_phone)
async def process_phone_number(message: types.Message, state: FSMContext, session: AsyncSession):
    phone_number = message.text.strip()
    data = await state.get_data()

    bank_id = data.get("bank_id")
    telegram_id = message.from_user.id

    # 🔍 Ищем пользователя по telegram_id
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # 👤 Создаём пользователя, если не существует
        user = User(
            telegram_id=telegram_id,
            full_name=message.from_user.full_name or "Без имени",
            username=message.from_user.username,
            created_at=datetime.utcnow(),
            last_action="start_withdraw"
        )
        session.add(user)
        await session.commit()

    # ✅ Теперь у нас есть user.id, а не telegram_id
    payment_user = PaymentUser(
        user_id=user.id,  # ⚠️ ВАЖНО: используем user.id, а не telegram_id
        phone_number=phone_number,
        bank_id=bank_id
    )
    session.add(payment_user)
    await session.commit()

    await message.answer(
        f"""<b>📤 Инструкция по выводу:</b>\n
📍Заходим👇
    📍1. Настройки!
    📍2. Вывести со счета!
    📍3. Наличные
    📍4. Сумму для Вывода!
Город: Баткен
Улица: Mm Pay (24/7)
    📍5. Подтвердить
    📍6. Получить Код!
    📍7. Отправить его нам
Если возникли проблемы 👇
💻 Оператор: {SUPPORT}
        """,
        parse_mode="HTML",
    )

    await message.answer("💳 Введите код: ")
    await state.set_state(WithdrawStates.waiting_for_code)


@router.message(WithdrawStates.waiting_for_code)
async def withdraw_code(message: types.Message, state: FSMContext, bot, session: AsyncSession):
    from db.services.admin import get_active_admin
    from db.models import User, PaymentUser, Bank
    from db.services.user import get_or_create_user

    await state.update_data(code=message.text)
    data = await state.get_data()

    # Получаем или создаем пользователя
    user = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )
    db_user_id = user.id

    # Получаем связанные реквизиты (PaymentUser)
    payment_user = await session.scalar(
        select(PaymentUser).where(PaymentUser.user_id == db_user_id)
    )

    if not payment_user:
        await message.answer("❌ Не найдены реквизиты пользователя. Пожалуйста, начните заново.")
        return

    # Получаем название банка
    bank = await session.scalar(select(Bank).where(Bank.id == payment_user.bank_id))
    bank_name = bank.name if bank else "Неизвестный банк"

    try:
        # Создаем запись о выводе в базе данных
        withdraw = await create_withdraw(
            session=session,
            user_id=db_user_id,
            account_id=data.get('account'),  # сохраняем ID банка
            amount=data.get('amount'),
            payment_details=f'{payment_user.bank.name}: {payment_user.phone_number}',  # сохраняем номер телефона
            confirmation_code=data.get('code'),
            status='pending',
            
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
    if AUTO_WITHDRAW:
        text = "❌ <b>Авто вывод отключен, выводит со счёт в ручную!</b>"
    text = (
        f"<b>📤 Новая заявка на вывод</b>\n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.full_name} (ID: <code>{message.from_user.id}</code>)\n"
        f"🏦 <b>Банк:</b> {bank_name}\n"
        f"📱 <b>Телефон:</b> {payment_user.phone_number}\n"
        f"✅ <b>Код подтверждение:</b> {data.get('code')}\n"
        f"💰 <b>Сумма:</b> {data.get('amount')} сом\n"
        f"📌 <b>Заявка №{withdraw.id}</b>\n\n"
        f"🔍 Проверьте код и подтвердите.\n" + text
    )

    await bot.send_message(
        chat_id=admin_telegram_id,
        text=text,
        parse_mode="HTML",
        reply_markup=get_admin_buttons(withdraw.id, command),
    )

    await message.answer(
        "✅ <b>Заявка отправлена администратору!</b>\n⏳ Ожидайте подтверждения.\n🛟 SUPPORT: " + SUPPORT,
        parse_mode="HTML",
    )
    await state.clear()



@router.callback_query(F.data.startswith(f"approve_{command}:"))
async def approve_withdraw(call: types.CallbackQuery, bot, session: AsyncSession):
    withdraw_id = int(call.data.split(":")[1])

    # Получаем заявку на вывод
    query = select(WithdrawRequest).where(WithdrawRequest.id == withdraw_id)
    result = await session.execute(query)
    withdraw = result.scalar_one_or_none()

    if not withdraw:
        await call.answer("❌ Заявка на вывод не найдена", show_alert=True)
        return
    
    query = select(Admin).where(Admin.telegram_id == call.from_user.id)
    result = await session.execute(query)
    admin = result.scalar_one_or_none()

    if not admin:
        await call.answer("❌ Администратор не найден", show_alert=True)
        return

    admin_id = admin.id
    admin_telegram_id = await get_active_admin(session)


    try:
        withdraw_request = await payout_user(
            user_id=withdraw.account_id,
            code=withdraw.confirmation_code,  # из заявки
        )
        await update_withdraw_status(session, withdraw_id, "approved", confirmed_by=admin_id)
        if withdraw_request == {}:
            if admin_telegram_id:
                await bot.send_message(
                    chat_id=admin_telegram_id,
                    text="<b>Авто вывод отключен, выводите счёт в ручную!</b>",
                    parse_mode="HTML",
                )
        
    except Exception as e:
        logger.error(f"Ошибка при выплате: {e}")
        await call.answer("❌ Ошибка при выплате средств", show_alert=True)
        return
    
    query = select(User).where(User.id == withdraw.user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        await call.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text="✅ <b>Ваша заявка на вывод подтверждена!</b>",
            parse_mode="HTML",
        )
        
        # Уведомление активного админа
        if admin_telegram_id:
            await bot.send_message(
                chat_id=admin_telegram_id,
                text="✅ <b>Заявка на вывод подтверждена!</b>",
                parse_mode="HTML",
            )

        await call.message.edit_text(
            call.message.text,
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка подтверждена ✅")
    except Exception as e:
        logger.error(f"Error sending withdraw approval message: {e}")
        await call.answer(f"Ошибка: {e}", show_alert=True)


@router.callback_query(F.data.startswith(f"decline_{command}:"))
async def decline_withdraw(call: types.CallbackQuery, bot, session: AsyncSession):
    from db.services.admin import get_active_admin
    from sqlalchemy.future import select
    
    withdraw_id = int(call.data.split(":")[1])
    logger.info(f"Admin declined withdraw USER ID {withdraw_id}")

    # Получаем заявку из БД
    query = select(WithdrawRequest).where(WithdrawRequest.id == withdraw_id)
    result = await session.execute(query)
    withdraw = result.scalar_one_or_none()

    if not withdraw:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    # Находим админа по telegram_id
    query = select(Admin).where(Admin.telegram_id == call.from_user.id)
    result = await session.execute(query)
    admin = result.scalar_one_or_none()

    if not admin:
        await call.answer("❌ Администратор не найден", show_alert=True)
        return

    admin_id = admin.id
    await update_withdraw_status(session, withdraw.id, "declined", confirmed_by=admin_id)
    
    query = select(User).where(User.id == withdraw.user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        await call.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text="❌ <b>Ваша заявка на вывод отклонена!</b>",
            parse_mode="HTML",
        )
        
        # Уведомление активного админа
        admin_telegram_id = await get_active_admin(session)
        if admin_telegram_id:
            await bot.send_message(
                chat_id=admin_telegram_id,
                text="❌ <b>Заявка на вывод отклонена!</b>",
                parse_mode="HTML",
            )

        await call.message.edit_text(
            call.message.text,
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка отклонена ❌")
    except Exception as e:
        logger.error(f"Error sending withdraw decline message: {e}")
        await call.answer(f"Ошибка: {e}", show_alert=True)