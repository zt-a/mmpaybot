from aiogram import Router, types, F
from aiogram.filters import CommandStart
from utils.logger import logger
from bot.keyboards.inline import menu
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import SUPPORT, BOT_NAME
from db.services.user import get_or_create_user
from sqlalchemy.ext.asyncio import AsyncSession


router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    logger.info(f"User {message.from_user.id} started the bot.")
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

    await message.answer(
        f"<b>👋 Добро пожаловать в <u>{BOT_NAME}</u>!</b>, {user.full_name or user.username or 'пользователь'}!\n\n"
        "💼 <i>У нас вы можете легко пополнить или вывести средства.</i>\n\n"
        "🔽 <b>Выберите действие ниже</b> — просто нажмите на кнопку 👇\n\n"
        f'🛟 Поддержка: <a href="https://t.me/{SUPPORT}">@{SUPPORT}</a>',
        reply_markup=menu,
        parse_mode="HTML",
    )



@router.message(F.text == "❌ Отменить")
@router.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        logger.info(f"User {message.from_user.id} canceled an action.")
        await message.answer(
            "❌ <b>Действие отменено.</b>", parse_mode="HTML", reply_markup=menu
        )
    except Exception as e:
        logger.error(f"Ошибка при отмене действия: {e}")



@router.message(F.text == "🏠 Главное меню")
@router.message(Command("menu"))
async def main_menu(message: types.Message, session: AsyncSession, state: FSMContext):
    logger.info(f"User {message.from_user.id} returned to main menu.")
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
    await state.clear()
    await message.answer(
        "<b>🏠 Добро пожаловать в <u>Главное меню</u></b>\n\n"
        "📲 Выберите одно из действий ниже, нажав на кнопку ⬇️\n\n"
        f'🛟 Поддержка: <a href="https://t.me/{SUPPORT}">@{SUPPORT}</a>',
        reply_markup=menu,
        parse_mode="HTML",
    )

