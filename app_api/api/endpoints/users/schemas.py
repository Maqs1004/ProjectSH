import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    telegram_id: int = Field(title="Уникальный ID пользователя в telegram", examples=[12456789])
    chat_id: int = Field(title="Уникальный ID чата", examples=[987654321])


class BaseUserSchema(BaseModel):
    chat_id: int = Field(title="Уникальный ID чата с пользователем", examples=[123321])
    username: Optional[str] = Field(title="Никнейм в telegram", examples=["Max"])

    class Config:
        from_attributes = True


class UsersSchema(BaseUserSchema):
    telegram_id: int = Field(title="Уникальный ID пользователя в telegram", examples=[12456789])
    id: int = Field(title="Уникальный ID пользователя", examples=[12])
    active: bool = Field(title="Флаг активен ли пользователь", examples=[True])
    created_at: datetime = Field(title="Дата создания пользователя", examples=["2023-04-20 09:49:51.252"])
    blocked: bool = Field(title="Флаг блокировки пользователя", examples=[False])


class AddUserSchema(BaseUserSchema):
    pass


class PatchUserSchema(BaseModel):
    active: Optional[bool] = Field(default=None, title="Флаг активен ли пользователь", examples=[True])
    blocked: Optional[bool] = Field(default=None, title="Флаг блокировки пользователя", examples=[False])


class UsersNotFoundErrorSchema(BaseModel):
    detail: str = "User not found"


class AnswersNotFoundErrorSchema(BaseModel):
    detail: str = "Answer not found"


class UsersExistErrorSchema(BaseModel):
    detail: str = "User already exists"


class BaseUserBalancesSchema(BaseModel):
    count_course: int = Field(title="Количество курсов доступных пользователю", examples=[3])

    class Config:
        from_attributes = True


class UserBalancesSchema(BaseUserBalancesSchema):
    id: int = Field(title="Уникальный ID записи", examples=[1])
    user_id: int = Field(title="Уникальный ID пользователя", examples=[1])


class BalancesAction(enum.Enum):
    deposit = "deposit"
    withdraw = "withdraw"


class PatchUserBalancesSchema(BaseUserBalancesSchema):
    action: BalancesAction = Field(title="Списание или пополнение", examples=["withdraw"])


class AddInvoicesSchema(BaseModel):
    payment_info: dict = Field(title="Платежная информация", examples=[{"currency": "RUB", "total_amount": 777}])

    class Config:
        from_attributes = True


class InvoicesSchema(AddInvoicesSchema):
    id: int = Field(title="Уникальный ID записи", examples=[1])
    user_id: int = Field(title="Уникальный ID пользователя", examples=[1])
