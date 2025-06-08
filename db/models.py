from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, Numeric, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base, validates
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(Text)
    username = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    last_action = Column(Text)

    # Связь "один-ко-многим" с PaymentUser (у пользователя может быть несколько платёжных аккаунтов)
    payment_users = relationship("PaymentUser", back_populates="user")

    # Связь с Admin (у пользователя может быть 0 или несколько записей админов, в зависимости от логики)
    admins = relationship("Admin", back_populates="user")


class Admin(Base):
    __tablename__ = 'admins'
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(Text)
    status = Column(Text, default='inactive')
    added_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="admins")


class Bank(Base):
    __tablename__ = 'banks'
    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False, unique=True)

    payment_methods = relationship("PaymentMethod", back_populates="bank")
    payment_users = relationship("PaymentUser", back_populates="bank")


class PaymentUser(Base):
    __tablename__ = 'payment_user'

    id = Column(BigInteger, primary_key=True)
    card_number = Column(Text)
    phone_number = Column(Text)
    holder_name = Column(Text)
    qr_photo = Column(Text)
    confirmed_by_id = Column(BigInteger, ForeignKey('admins.id'), nullable=True)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    bank_id = Column(BigInteger, ForeignKey('banks.id'), nullable=False)
    bank = relationship("Bank", back_populates="payment_users")

    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="payment_users")

    withdraw_requests = relationship("WithdrawRequest", back_populates="payment_user")


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    id = Column(BigInteger, primary_key=True)
    title = Column(Text, nullable=False)
    type = Column(Text)
    account_number = Column(Text)
    phone_number = Column(Text)
    holder_name = Column(Text)
    qr_photo = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    bank_id = Column(BigInteger, ForeignKey('banks.id'), nullable=False)
    bank = relationship("Bank", back_populates="payment_methods")


class DepositRequest(Base):
    __tablename__ = 'deposit_requests'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    account_id = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    receipt_photo = Column(Text)
    status = Column(Text, default='pending')
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    confirmed_by_id = Column(BigInteger, ForeignKey('admins.id'), nullable=True)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    @validates('account_id')
    def validate_account_id(self, key, value):
        if not (value.isdigit() and len(value) == 9):
            raise ValueError("account_id должен содержать ровно 9 цифр")
        return value


class WithdrawRequest(Base):
    __tablename__ = 'withdraw_requests'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    account_id = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_details = Column(Text)
    confirmation_code = Column(Text, nullable=False)
    status = Column(Text, default='pending')
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    confirmed_by_id = Column(BigInteger, ForeignKey('admins.id'), nullable=True)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    payment_user_id = Column(BigInteger, ForeignKey('payment_user.id'), nullable=True)
    payment_user = relationship("PaymentUser", back_populates="withdraw_requests")

    @validates('account_id')
    def validate_account_id(self, key, value):
        if not (value.isdigit() and len(value) == 9):
            raise ValueError("account_id должен содержать ровно 9 цифр")
        return value


class TransactionLog(Base):
    __tablename__ = 'transactions_log'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    action = Column(Text, nullable=False)
    data = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class Balance(Base):
    __tablename__ = 'balances'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # положительное - пополнение, отрицательное - списание
    description = Column(Text, nullable=False)       # описание операции ("Пополнение", "Вывод" и т.д.)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
