from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

import asyncio

from config import BOT_TOKEN
from bot.handlers import base, deposit, request, withdraw, bankDetail, payment_method, admin
from utils.logger import logger

from db.models import Base
from db.db import engine


from middlewares.db import DbSessionMiddleware

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

dp.message.middleware(DbSessionMiddleware())
dp.callback_query.middleware(DbSessionMiddleware())


dp.include_routers(
    base.router,
    admin.router,
    bankDetail.router,
    payment_method.router,
    deposit.router,
    withdraw.router,
    request.router
)

async def bot_start():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Бот запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(bot_start())
