from mailbox import Message
from aiogram import F, Router
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import admin_menu
from core.api.cashdesk_api import get_balance
from utils.decorators import admin_only
from config import auto_PP, auto_VV

router = Router()


@admin_only()
@router.message(F.text == 'Баланс')
@router.message(Command('balance'))
async def getBalance(message: Message, session: AsyncSession):
    balance_data = await get_balance()  # передай session, если нужно
    balance = balance_data.get('Balance')
    limit = balance_data.get('Limit')
    await message.answer(
        f'<i>Баланс</i>: <b>{balance}</b>\n'
        f'<i>Лимит</i>: <b>{limit}</b>',
        reply_markup=admin_menu,  # исправил опечатку
        parse_mode='HTML'
    )


@admin_only()
@router.message(F.text == 'Автопополнение включить')
@router.message(Command('active_auto_PP'))
async def active_auto_pp(message: Message):
    await message.answer(
        f"✅ <b>Авто пополнение включен</b>: {auto_PP(True)}",
        reply_markup=admin_menu,  # исправил опечатку
        parse_mode='HTML'
    )
    
@admin_only()
@router.message(F.text == 'Автопополнение выключить')
@router.message(Command('inactive_auto_PP'))
async def inactive_auto_pp(message: Message):
    await message.answer(
        f"❌ <b>Авто пополнение включен</b>: {auto_PP(False)}",
        reply_markup=admin_menu,  # исправил опечатку
        parse_mode='HTML'
    )
    
@admin_only()
@router.message(F.text == 'Автовывод включить')
@router.message(Command('active_auto_PP'))
async def active_auto_pp(message: Message):
    await message.answer(
        f"✅ <b>Авто вывод включен</b>: {auto_VV(True)}",
        reply_markup=admin_menu,  # исправил опечатку
        parse_mode='HTML'
    )
    
@admin_only()
@router.message(F.text == 'Автовывод выключить')
@router.message(Command('inactive_auto_PP'))
async def inactive_auto_pp(message: Message):
    await message.answer(
        f"❌ <b>Авто вывод включен</b>: {auto_VV(False)}",
        reply_markup=admin_menu,  # исправил опечатку
        parse_mode='HTML'
    )