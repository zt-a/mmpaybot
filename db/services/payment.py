from sqlalchemy.future import select
from sqlalchemy import update
from db.models import PaymentMethod
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def get_or_create_paymentMethod(
    session: AsyncSession,
    title: str,
    type: str,
    account_number: str,
    phone_number: str,
    holder_name: str,
    qr_photo: str,
    is_active: bool,
    bank_id: int,
):
    # Проверяем — есть ли уже реквизит с таким номером счёта
    query = select(PaymentMethod).where(PaymentMethod.account_number == account_number)
    result = await session.execute(query)
    payment = result.scalars().first()

    if not payment:
        # Деактивируем текущий активный метод для этого банка
        if is_active:
            await session.execute(
                update(PaymentMethod)
                .where(PaymentMethod.bank_id == bank_id, PaymentMethod.is_active == True)
                .values(is_active=False)
            )

        # Создаём новый реквизит
        payment = PaymentMethod(
            title=title,
            type=type,
            account_number=account_number,
            phone_number=phone_number,
            holder_name=holder_name,
            qr_photo=qr_photo,
            is_active=is_active,
            bank_id=bank_id,
            created_at=datetime.utcnow()
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)

    return payment


async def activate_payment_method_by_id(session: AsyncSession, method_id: int):
    # Получаем метод оплаты по ID
    result = await session.execute(
        select(PaymentMethod).where(PaymentMethod.id == method_id)
    )
    method = result.scalar_one_or_none()

    if not method:
        return None  # Метод не найден

    bank_id = method.bank_id

    # Деактивируем все методы оплаты этого банка
    await session.execute(
        update(PaymentMethod)
        .where(PaymentMethod.bank_id == bank_id)
        .values(is_active=False)
    )

    # Активируем выбранный метод
    method.is_active = True

    await session.commit()
    await session.refresh(method)

    return method


async def delete_payment_method_by_id(session: AsyncSession, method_id: int):
    # Получаем метод оплаты по ID
    result = await session.execute(
        select(PaymentMethod).where(PaymentMethod.id == method_id)
    )
    method = result.scalar_one_or_none()

    if not method:
        return False  # Метод не найден

    await session.delete(method)
    await session.commit()
    return True  # Удаление успешно




from sqlalchemy.orm import Session
from db.models import PaymentMethod
from datetime import datetime

# Создать PaymentMethod
def create_payment_method(db: Session, title: str, bank_id: int, type_: str = None,
                          account_number: str = None, phone_number: str = None,
                          holder_name: str = None, qr_photo: str = None, is_active: bool = True):
    payment_method = PaymentMethod(
        title=title,
        bank_id=bank_id,
        type=type_,
        account_number=account_number,
        phone_number=phone_number,
        holder_name=holder_name,
        qr_photo=qr_photo,
        is_active=is_active,
        created_at=datetime.utcnow()
    )
    db.add(payment_method)
    db.commit()
    db.refresh(payment_method)
    return payment_method

# Получить PaymentMethod по id
def get_payment_method_by_id(db: Session, payment_method_id: int):
    return db.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()

# Получить все активные методы оплаты
def get_active_payment_methods(db: Session):
    return db.query(PaymentMethod).filter(PaymentMethod.is_active == True).all()

# Обновить PaymentMethod (например, изменить статус или название)
def update_payment_method(db: Session, payment_method_id: int, **kwargs):
    payment_method = get_payment_method_by_id(db, payment_method_id)
    if not payment_method:
        return None
    for key, value in kwargs.items():
        if hasattr(payment_method, key):
            setattr(payment_method, key, value)
    db.commit()
    db.refresh(payment_method)
    return payment_method

# Удалить PaymentMethod
def delete_payment_method(db: Session, payment_method_id: int):
    payment_method = get_payment_method_by_id(db, payment_method_id)
    if not payment_method:
        return False
    db.delete(payment_method)
    db.commit()
    return True


async def get_methods_by_bank_id(session: AsyncSession, bank_id: int) -> list[PaymentMethod]:
    """Получить все методы оплаты, привязанные к банку по ID."""
    result = await session.execute(
        select(PaymentMethod).where(PaymentMethod.bank_id == bank_id)
    )
    return result.scalars().all()


from sqlalchemy import update, select
from db.models import PaymentMethod

async def activate_payment_method_by_id(session: AsyncSession, method_id: int):
    # Сначала деактивируем все методы этого банка (если логика такая)
    method = await session.get(PaymentMethod, method_id)
    if not method:
        return None

    # Деактивируем другие методы банка
    await session.execute(
        update(PaymentMethod)
        .where(PaymentMethod.bank_id == method.bank_id)
        .values(is_active=False)
    )

    # Активируем выбранный метод
    method.is_active = True
    session.add(method)
    await session.commit()
    await session.refresh(method)
    return method


async def get_all_payment_methods(session: AsyncSession):
    result = await session.execute(select(PaymentMethod))
    return result.scalars().all()