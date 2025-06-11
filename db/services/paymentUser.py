from sqlalchemy.orm import Session
from models import PaymentUser

# Создать PaymentUser
def create_payment_user(db: Session, user_id: int, bank_id: int, card_number: str = None,
                        phone_number: str = None, holder_name: str = None, qr_photo: str = None,
                        confirmed_by: int = None, confirmed_at=None):
    payment_user = PaymentUser(
        user_id=user_id,
        bank_id=bank_id,
        card_number=card_number,
        phone_number=phone_number,
        holder_name=holder_name,
        qr_photo=qr_photo,
        confirmed_by=confirmed_by,
        confirmed_at=confirmed_at
    )
    db.add(payment_user)
    db.commit()
    db.refresh(payment_user)
    return payment_user

# Получить PaymentUser по id
def get_payment_user_by_id(db: Session, payment_user_id: int):
    return db.query(PaymentUser).filter(PaymentUser.id == payment_user_id).first()

# Получить все PaymentUser для конкретного user_id
def get_payment_users_by_user_id(db: Session, user_id: int):
    return db.query(PaymentUser).filter(PaymentUser.user_id == user_id).all()

# Обновить PaymentUser (например, обновим card_number и holder_name)
def update_payment_user(db: Session, payment_user_id: int, **kwargs):
    payment_user = get_payment_user_by_id(db, payment_user_id)
    if not payment_user:
        return None
    for key, value in kwargs.items():
        if hasattr(payment_user, key):
            setattr(payment_user, key, value)
    db.commit()
    db.refresh(payment_user)
    return payment_user

# Удалить PaymentUser
def delete_payment_user(db: Session, payment_user_id: int):
    payment_user = get_payment_user_by_id(db, payment_user_id)
    if not payment_user:
        return False
    db.delete(payment_user)
    db.commit()
    return True
