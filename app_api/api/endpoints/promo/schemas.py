from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app_api.models.interaction import DiscountType, CourseContentVolume


class PromoCodeSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    discount_type: DiscountType = Field(title="Тип скидки, проценты", examples=["percent"])
    discount_value: float = Field(title="Значение скидки", examples=[50])
    expiry_date: datetime = Field(title="Дата, когда заканчивает свое действе код")
    course_content_volume: CourseContentVolume = Field(title="Объем курса")

    class Config:
        from_attributes = True


class AddPromoCodeSchema(BaseModel):
    discount_type: DiscountType = Field(title="Тип скидки, проценты", examples=["percent"])
    discount_value: float = Field(title="Значение скидки", examples=[50])
    expiry_date: datetime = Field(title="Дата, когда заканчивает свое действе код")
    course_content_volume: CourseContentVolume = Field(title="Объем курса")


class PatchPromoCodeSchema(BaseModel):
    discount_type: Optional[DiscountType] = Field(default=None, title="Тип скидки", examples=["percent"])
    discount_value: Optional[float] = Field(default=None, title="Сообщение пользователя модели", examples=[50])
    expiry_date: Optional[datetime] = Field(default=None, title="Дата, когда окончания")
    course_content_volume: Optional[CourseContentVolume] = Field(default=None, title="Объем курса")


class PromoCodeNotFoundErrorSchema(BaseModel):
    detail: str = "Promo code not found"


class PromoCodeExistErrorSchema(BaseModel):
    detail: str = "Promo code already exists"


class PromoCodeUsedErrorSchema(BaseModel):
    detail: str = "Promo code was used"
