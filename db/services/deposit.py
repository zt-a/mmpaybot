from datetime import datetime
from sqlalchemy import update
from db.models import DepositRequest
from sqlalchemy.future import select

async def create_deposit(
    session,
    user_id: int,
    account_id: str,
    amount: float,
    receipt_photo: str,
    status: str = 'pending'
):
    from db.models import User  # Импортируем модель User
    
    # Проверяем существование пользователя
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"Пользователь с ID {user_id} не найден")
    
    deposit = DepositRequest(
        user_id=user_id,
        account_id=str(account_id),
        amount=amount,
        receipt_photo=receipt_photo,
        status=status,
    )
    session.add(deposit)
    await session.commit()
    await session.refresh(deposit)
    return deposit


async def update_deposit_status(session, deposit_id, status, confirmed_by=None):
    stmt = (
        update(DepositRequest)
        .where(DepositRequest.id == deposit_id)
        .values(
            status=status,
            confirmed_by_id=confirmed_by,
            confirmed_at=datetime.utcnow()
        )
    )
    await session.execute(stmt)
    await session.commit()
    
    
    
from sqlalchemy.orm import Session
from db.models import DepositRequest
from datetime import datetime

# Создать заявку на депозит
def create_deposit_request(db: Session, user_id: int, account_id: str, amount: float,
                           payment_method_id: int = None, receipt_photo: str = None,
                           status: str = 'pending', confirmed_by: int = None, confirmed_at: datetime = None):
    deposit_request = DepositRequest(
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        payment_method_id=payment_method_id,
        receipt_photo=receipt_photo,
        status=status,
        confirmed_by=confirmed_by,
        confirmed_at=confirmed_at,
        created_at=datetime.utcnow()
    )
    db.add(deposit_request)
    db.commit()
    db.refresh(deposit_request)
    return deposit_request

# Получить заявку по id
def get_deposit_request_by_id(db: Session, deposit_request_id: int):
    return db.query(DepositRequest).filter(DepositRequest.id == deposit_request_id).first()

# Получить все заявки пользователя
def get_deposit_requests_by_user(db: Session, user_id: int):
    return db.query(DepositRequest).filter(DepositRequest.user_id == user_id).all()

# Обновить статус заявки
def update_deposit_request_status(db: Session, deposit_request_id: int, status: str,
                                  confirmed_by: int = None, confirmed_at: datetime = None):
    deposit_request = get_deposit_request_by_id(db, deposit_request_id)
    if not deposit_request:
        return None
    deposit_request.status = status
    if confirmed_by:
        deposit_request.confirmed_by = confirmed_by
    if confirmed_at:
        deposit_request.confirmed_at = confirmed_at
    db.commit()
    db.refresh(deposit_request)
    return deposit_request

# Удалить заявку на депозит
def delete_deposit_request(db: Session, deposit_request_id: int):
    deposit_request = get_deposit_request_by_id(db, deposit_request_id)
    if not deposit_request:
        return False
    db.delete(deposit_request)
    db.commit()
    return True
