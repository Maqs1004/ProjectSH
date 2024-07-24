from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UsersSchema(BaseModel):
    chat_id: int = Field(title="Уникальный ID чата с пользователем", examples=[123321])
    username: Optional[str] = Field(title="Никнейм в telegram", examples=["Max"])
    telegram_id: int = Field(
        title="Уникальный ID пользователя в telegram", examples=[12456789]
    )
    id: int = Field(title="Уникальный ID пользователя", examples=[12])
    active: bool = Field(title="Флаг активен ли пользователь", examples=[True])
    created_at: datetime = Field(
        title="Дата создания пользователя", examples=["2023-04-20 09:49:51.252"]
    )
    blocked: bool = Field(title="Флаг блокировки пользователя", examples=[False])


class TranslationSchema(BaseModel):
    id: Optional[int] = Field(default=None, title="Уникальный ID", examples=[1])
    message_key: str = Field(
        title="Название промпта в системе", examples=["hello_message"]
    )
    language_code: str = Field(title="Название промпта в системе", examples=["EN"])
    message_text: str = Field(
        title="Название промпта в системе", examples=["Hello World"]
    )


class UserBalance(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    user_id: int = Field(title="Уникальный ID пользователя", examples=[1])
    count_course: int = Field(title="Количество доступных курсов", examples=[1])


class PromoCode(BaseModel):
    code: Optional[str] = Field(title="Промо код", default=None)
    discount_type: Optional[str] = Field(
        title="Тип скидки, процент или сумма", default=None
    )
    discount_value: Optional[float] = Field(
        title="Значение скидки", default=None, examples=[95]
    )
    expiry_date: Optional[datetime] = Field(
        title="Дата, когда заканчивается код", default=None
    )
    course_content_volume: Optional[str] = Field(
        title="Размер курса, на который применяется скидка", default=None
    )
