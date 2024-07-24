import enum
import datetime
from ..db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, BigInteger, DateTime, Enum, String, Float, Text, UniqueConstraint


class MessagesType(enum.Enum):
    system = "system"
    user = "user"
    bot = "bot"


class DiscountType(enum.Enum):
    percent = "percent"


class CourseContentVolume(enum.Enum):
    very_short = "очень короткий"
    short = "короткий"
    medium = "средний"


class GPTModels(Base):
    __tablename__ = "gpt_models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    release = Column(String(255), nullable=False)
    input_price = Column(Float, nullable=False)
    output_price = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    prompt = relationship("Prompts", back_populates="gpt_model")


class Prompts(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    system = Column(Text, nullable=True)
    user = Column(Text, nullable=False)
    gpt_model_id = Column(Integer, ForeignKey("gpt_models.id"), nullable=False)
    gpt_model = relationship("GPTModels", back_populates="prompt")


class Translation(Base):
    __tablename__ = 'translations'

    id = Column(Integer, primary_key=True)
    message_key = Column(String(255), nullable=False)
    language_code = Column(String(10), nullable=False)
    message_text = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('message_key', 'language_code', name='_message_key_language_uc'),)


class PromoCode(Base):
    __tablename__ = 'promo_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Float, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    course_content_volume = Column(Enum(CourseContentVolume))
    promo_code = relationship("UserPromoCode", back_populates="promo")


class UserPromoCode(Base):
    __tablename__ = 'user_promo_codes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    promo_code_id = Column(Integer, ForeignKey('promo_codes.id'), nullable=False)
    applied_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'promo_code_id', name='_user_promo_uc'),)
    promo = relationship("PromoCode", back_populates="promo_code")
    promo_user = relationship("Users", back_populates="user_promo")
