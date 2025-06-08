from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from bot.states import AuthStates
from config import ADMIN_COMMAND
from db.db import get_session
from db.models import Admin
from db.services.user import UserCRUD
from utils.decorators import admin_only
from utils.hash import verify_hash
from bot.keyboards.inline import admin_menu, cancel_keyboard, menu

router = Router()

@router.message(Command(ADMIN_COMMAND))
async def admin_entry(message: Message, state: FSMContext, session: AsyncSession):
    stmt = select(Admin).where(Admin.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()

    if admin:
        await message.answer("Добро пожаловать, админ!", reply_markup=admin_menu)
    else:
        await message.answer("🔐 Введите пароль для входа в админку (хеш):")
        await state.set_state(AuthStates.wait_for_password)


@router.message(AuthStates.wait_for_password)
async def process_admin_password(message: Message, state: FSMContext, session: AsyncSession):
    user_hash = message.text.strip()

    if verify_hash(user_hash):
        from db.models import User

        user = await UserCRUD.get_or_create(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )


        admin = Admin(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            user_id=user.id,
            status='inactive'
        )
        session.add(admin)
        await session.commit()

        await message.answer("✅ Вы добавлены как администратор! Для активации и входа напишите /login_admin", reply_markup=admin_menu)
    else:
        await message.answer("❌ Неверный пароль. Попробуйте снова или отмените.", reply_markup=cancel_keyboard)
        return
    await state.clear()
    
@router.message(F.text == 'Вход в админку')
@router.message(Command("login_admin"))
async def admin_login(message: Message, session: AsyncSession):
    result = await session.execute(select(Admin).filter(Admin.telegram_id == message.from_user.id))
    admin = result.scalars().first()
    if admin:
        # Деактивируем всех других админов
        await session.execute(
            update(Admin)
            .where(Admin.telegram_id != message.from_user.id, Admin.status == "active")
            .values(status="inactive")
        )
        # Активируем текущего
        admin.status = "active"
        await session.commit()
        await message.answer("Вы успешно вошли в админ-панель (статус 'активен').", reply_markup=admin_menu)
    else:
        await message.answer("Вы не зарегистрированы как админ.", reply_markup=cancel_keyboard)



@router.message(F.text == 'Выход с админки')
@router.message(Command("logout_admin"))
@admin_only()
async def admin_logout(message: Message, session: AsyncSession):
    result = await session.execute(select(Admin).filter(Admin.telegram_id == message.from_user.id))
    admin = result.scalars().first()
    if admin:
        admin.status = 'inactive'
        await session.commit()
        await message.answer("Вы успешно вышли из админ-панели (статус 'неактивен').", reply_markup=menu)
    else:
        await message.answer("Вы не зарегистрированы как админ.", reply_markup=menu)
            
@router.message(Command('remove_admin'))
@router.message(F.text == "Удаление админа")
@admin_only()
async def remove_admin(message: Message, session: AsyncSession):
    
    result = await session.execute(select(Admin).filter(Admin.telegram_id == message.from_user.id))
    admin = result.scalars().first()
    if admin:
        await session.delete(admin)
        await session.commit()
        await message.answer("Ваша запись админа удалена.", reply_markup=menu)
    else:
        await message.answer("Вы не зарегистрированы как админ.", reply_markup=menu)
