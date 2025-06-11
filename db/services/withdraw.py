from datetime import datetime

from sqlalchemy import update
from db.models import WithdrawRequest
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import WithdrawRequest

async def create_withdraw(
    session,
    user_id: int,
    account_id: str,
    amount: float,
    confirmation_code: str,
    status: str = "pending",
    payment_details: str = None,
    payment_user_id: int = None
) -> WithdrawRequest:
    withdraw = WithdrawRequest(
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        confirmation_code=confirmation_code,
        status=status,
        payment_details=payment_details,
        payment_user_id=payment_user_id
    )
    session.add(withdraw)
    await session.commit()
    await session.refresh(withdraw)
    return withdraw


async def update_withdraw_status(session, withdraw_id, status, confirmed_by=None):
    stmt = (
        update(WithdrawRequest)
        .where(WithdrawRequest.id == withdraw_id)
        .values(
            status=status,
            confirmed_by_id=confirmed_by,
            confirmed_at=datetime.utcnow()
        )
    )
    await session.execute(stmt)
    await session.commit()
    
    
    
from sqlalchemy.orm import Session
from db.models import WithdrawRequest
from datetime import datetime

# Создать заявку на вывод средств
def create_withdraw_request(db: Session, user_id: int, account_id: str, amount: float,
                            payment_details: str, confirmation_code: str,
                            status: str = 'pending', confirmed_by: int = None, confirmed_at: datetime = None):
    withdraw_request = WithdrawRequest(
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        payment_details=payment_details,
        confirmation_code=confirmation_code,
        status=status,
        confirmed_by=confirmed_by,
        confirmed_at=confirmed_at,
        created_at=datetime.utcnow()
    )
    db.add(withdraw_request)
    db.commit()
    db.refresh(withdraw_request)
    return withdraw_request

# Получить заявку по id
def get_withdraw_request_by_id(db: Session, withdraw_request_id: int):
    return db.query(WithdrawRequest).filter(WithdrawRequest.id == withdraw_request_id).first()

# Получить все заявки пользователя
def get_withdraw_requests_by_user(db: Session, user_id: int):
    return db.query(WithdrawRequest).filter(WithdrawRequest.user_id == user_id).all()

# Обновить статус заявки
def update_withdraw_request_status(db: Session, withdraw_request_id: int, status: str,
                                   confirmed_by: int = None, confirmed_at: datetime = None):
    withdraw_request = get_withdraw_request_by_id(db, withdraw_request_id)
    if not withdraw_request:
        return None
    withdraw_request.status = status
    if confirmed_by:
        withdraw_request.confirmed_by = confirmed_by
    if confirmed_at:
        withdraw_request.confirmed_at = confirmed_at
    db.commit()
    db.refresh(withdraw_request)
    return withdraw_request

# Удалить заявку на вывод
def delete_withdraw_request(db: Session, withdraw_request_id: int):
    withdraw_request = get_withdraw_request_by_id(db, withdraw_request_id)
    if not withdraw_request:
        return False
    db.delete(withdraw_request)
    db.commit()
    return True
