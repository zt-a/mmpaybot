from functools import wraps
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Admin

def admin_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, session: AsyncSession, *args, **kwargs):
            telegram_id = message.from_user.id
            result = await session.execute(
                Admin.__table__.select().where(
                    (Admin.telegram_id == telegram_id) & 
                    (Admin.status == 'active')
                )
            )
            admin = result.first()

            if not admin:
                await message.answer("⛔️ Доступ запрещён. Только для активных админов.")
                return
            return await func(message, session, *args, **kwargs)
        return wrapper
    return decorator