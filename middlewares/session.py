from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_session  # твоя функция создания сессии

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with get_session() as session:
            data["session"] = session
            return await handler(event, data)
