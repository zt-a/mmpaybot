from sqlalchemy.orm import Session
from models import TransactionLog
from datetime import datetime

# Создать запись лога транзакции
def create_transaction_log(db: Session, user_id: int, action: str, data: dict = None):
    log = TransactionLog(
        user_id=user_id,
        action=action,
        data=data,
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

# Получить лог по id
def get_transaction_log_by_id(db: Session, log_id: int):
    return db.query(TransactionLog).filter(TransactionLog.id == log_id).first()

# Получить все логи пользователя
def get_transaction_logs_by_user(db: Session, user_id: int):
    return db.query(TransactionLog).filter(TransactionLog.user_id == user_id).all()

# Получить все логи (с пагинацией, если нужно)
def get_all_transaction_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TransactionLog).offset(skip).limit(limit).all()

# Удалить лог
def delete_transaction_log(db: Session, log_id: int):
    log = get_transaction_log_by_id(db, log_id)
    if not log:
        return False
    db.delete(log)
    db.commit()
    return True
