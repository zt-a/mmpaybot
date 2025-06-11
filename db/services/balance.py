from sqlalchemy.orm import Session
from models import Balance
from datetime import datetime

# Создать запись баланса (операцию)
def create_balance_record(db: Session, user_id: int, amount: float, description: str):
    balance_record = Balance(
        user_id=user_id,
        amount=amount,
        description=description,
        created_at=datetime.utcnow()
    )
    db.add(balance_record)
    db.commit()
    db.refresh(balance_record)
    return balance_record

# Получить записи баланса пользователя
def get_balance_records_by_user(db: Session, user_id: int):
    return db.query(Balance).filter(Balance.user_id == user_id).all()

# Получить общий баланс пользователя (сумма всех amount)
def get_user_total_balance(db: Session, user_id: int):
    from sqlalchemy import func
    total = db.query(func.coalesce(func.sum(Balance.amount), 0)).filter(Balance.user_id == user_id).scalar()
    return total

# Удалить запись баланса по id
def delete_balance_record(db: Session, balance_id: int):
    record = db.query(Balance).filter(Balance.id == balance_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True
