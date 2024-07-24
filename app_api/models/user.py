import datetime
from ..db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, String, Float, BigInteger, JSON


class UserInfo(Base):
    __tablename__ = "user_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    additional_info = Column(String(255), default=None)
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("Users", back_populates="user_info")


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    blocked = Column(Boolean, default=False)
    chat_id = Column(Integer, nullable=False)
    user_info = relationship("UserInfo", back_populates="user", uselist=False)
    personal_topic = relationship("PersonalTopics", back_populates="user")
    user_balance = relationship("UserBalances", back_populates="user", uselist=False)
    user_course = relationship("UserCourseTracker", back_populates="user")
    answer = relationship("UserAnswers", back_populates="user")
    user_promo = relationship("UserPromoCode", back_populates="promo_user")
    invoices = relationship("Invoices", back_populates="user")


class PersonalTopics(Base):
    __tablename__ = "personal_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("Users", back_populates="personal_topic")


class UserBalances(Base):
    __tablename__ = "user_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    count_course = Column(Integer, default=-1)
    user = relationship("Users", back_populates="user_balance")


class Invoices(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    paid_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    payment_info = Column(JSON, nullable=True)
    user = relationship("Users", back_populates="invoices")
