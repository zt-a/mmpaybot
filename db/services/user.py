from sqlalchemy import insert
from sqlalchemy.future import select
from db.models import User  # Импортируй свои модели
from sqlalchemy.ext.asyncio import AsyncSession

async def get_or_create_user(session: AsyncSession, telegram_id: int, full_name: str = None, username: str = None) -> User:
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, full_name=full_name or "", username=username or "")
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            await session.rollback()
            raise e
    return user


from sqlalchemy.orm import Session
from db.models import User  # твой файл с моделями

# Создать нового пользователя
def create_user(db: Session, telegram_id: int, full_name: str = None, username: str = None):
    user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Получить пользователя по telegram_id
def get_user_by_telegram_id(db: Session, telegram_id: int):
    return db.query(User).filter(User.telegram_id == telegram_id).first()

# Получить пользователя по id
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# Обновить информацию о пользователе
def update_user(db: Session, user_id: int, full_name: str = None, username: str = None, last_action: str = None):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if full_name is not None:
        user.full_name = full_name
    if username is not None:
        user.username = username
    if last_action is not None:
        user.last_action = last_action
    db.commit()
    db.refresh(user)
    return user

# Удалить пользователя
def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True



from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User

class UserCRUD:
    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, telegram_id: int, full_name: str, username: str) -> User:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_or_create(session: AsyncSession, telegram_id: int, full_name: str, username: str) -> User:
        user = await UserCRUD.get_by_telegram_id(session, telegram_id)
        if user:
            return user
        return await UserCRUD.create(session, telegram_id, full_name, username)
