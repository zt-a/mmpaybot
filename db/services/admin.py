from sqlalchemy import update
from sqlalchemy.future import select
from db.models import Admin
from sqlalchemy.ext.asyncio import AsyncSession

async def get_or_create_admin(session: AsyncSession, telegram_id: int, username: str, status: str = "active"):
    query = select(Admin).where(Admin.telegram_id == telegram_id)
    result = await session.execute(query)
    admin = result.scalars().first()

    if status == "active":
        # Деактивируем всех остальных активных админов
        await session.execute(
            update(Admin)
            .where(Admin.status == "active", Admin.telegram_id != telegram_id)
            .values(status="inactive")
        )

    if not admin:
        admin = Admin(
            telegram_id=telegram_id,
            username=username or "",
            status=status or "active"
        )
        session.add(admin)
    else:
        # Если админ уже есть, обновляем username и статус
        admin.username = username or admin.username
        admin.status = status or admin.status

    await session.commit()
    await session.refresh(admin)
    return admin

async def get_active_admin(session: AsyncSession) -> int | None:
    query = select(Admin).where(Admin.status == 'active')
    result = await session.execute(query)
    admin = result.scalar_one_or_none()
    return admin.telegram_id if admin else None



from sqlalchemy.orm import Session
from db.models import Admin

# Создать нового админа
def create_admin(db: Session, telegram_id: int, username: str = None, status: str = 'inactive', user_id: int = None):
    admin = Admin(
        telegram_id=telegram_id,
        username=username,
        status=status,
        user_id=user_id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

# Получить админа по telegram_id
def get_admin_by_telegram_id(db: Session, telegram_id: int):
    return db.query(Admin).filter(Admin.telegram_id == telegram_id).first()

# Получить админа по id
def get_admin_by_id(db: Session, admin_id: int):
    return db.query(Admin).filter(Admin.id == admin_id).first()

# Обновить данные админа
def update_admin(db: Session, admin_id: int, username: str = None, status: str = None, user_id: int = None):
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        return None
    if username is not None:
        admin.username = username
    if status is not None:
        admin.status = status
    if user_id is not None:
        admin.user_id = user_id
    db.commit()
    db.refresh(admin)
    return admin

# Удалить админа
def delete_admin(db: Session, admin_id: int):
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        return False
    db.delete(admin)
    db.commit()
    return True


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from db.models import Admin, User

class AdminCRUD:
    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Admin | None:
        result = await session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, telegram_id: int, username: str, user_id: int, status='inactive') -> Admin:
        admin = Admin(
            telegram_id=telegram_id,
            username=username,
            user_id=user_id,
            status=status
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin

    @staticmethod
    async def set_active(session: AsyncSession, telegram_id: int):
        # Деактивируем всех админов кроме текущего
        await session.execute(
            update(Admin)
            .where(Admin.telegram_id != telegram_id, Admin.status == 'active')
            .values(status='inactive')
        )
        # Активируем текущего
        admin = await AdminCRUD.get_by_telegram_id(session, telegram_id)
        if admin:
            admin.status = 'active'
            await session.commit()
        return admin

    @staticmethod
    async def set_inactive(session: AsyncSession, telegram_id: int):
        admin = await AdminCRUD.get_by_telegram_id(session, telegram_id)
        if admin:
            admin.status = 'inactive'
            await session.commit()
        return admin

    @staticmethod
    async def delete_by_telegram_id(session: AsyncSession, telegram_id: int) -> bool:
        admin = await AdminCRUD.get_by_telegram_id(session, telegram_id)
        if not admin:
            return False
        await session.delete(admin)
        await session.commit()
        return True
