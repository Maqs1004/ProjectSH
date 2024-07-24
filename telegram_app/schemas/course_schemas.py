import enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CurrentStage(enum.Enum):
    not_generated = "not_generated"
    generating = "generating"
    generated = "generated"
    education = "education"
    question = "question"
    ask_question = "ask_question"
    waiting_response = "waiting_user_response"
    completed = "completed"


class ContentType(enum.Enum):
    text = "text"
    image = "image"


class UserCoursesSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    course_id: int = Field(title="Уникальный ID курса", examples=[1])
    user_id: int = Field(title="Уникальный ID пользователя", examples=[1])
    title: str = Field(title="Название курса", examples=["ООП в Python"])
    current_module_id: int = Field(
        title="Уникальный ID модуля, на котором находится пользователь", examples=[1]
    )
    current_sub_module_id: int = Field(
        title="Уникальный ID субмодуля, на котором находится пользователь", examples=[1]
    )
    current_stage: CurrentStage = Field(
        title="Стадия, на котрой находится пользователь", examples=["learning"]
    )
    current_order_number: int = Field(
        title="Номер материала или вопроса в блоке", examples=[1]
    )
    plan: dict = Field(title="План курса")
    active: bool = Field(title="Активен ли курс", examples=[True])
    archived: bool = Field(title="Архивирован ли курс", examples=[False])
    finished: bool = Field(title="Закончен ли курс", examples=[False])
    input_token: Optional[int] = Field(
        default=None, title="Количество потраченных входящих токенов", examples=[11731]
    )
    output_token: Optional[int] = Field(
        default=None, title="Количество потраченных исходящих токенов", examples=[9731]
    )
    spent_amount: Optional[float] = Field(
        default=None, title="Потраченная сумма", examples=[0.86]
    )
    usage_count: int = Field(
        title="Количество перепрохождения курса пользователем", examples=[1]
    )
    rating: int = Field(title="Рейтинг курса", examples=[1])
    created_at: datetime = Field(title="Дата добавления/создания куса пользователем")
    last_updated_at: Optional[datetime] = Field(title="Дата изменения")


class ModuleContentsSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    sub_module_id: int = Field(title="Уникальный ID субмодуля", examples=[1])
    title: str = Field(title="Название контента", examples=["Основные принципы ООП"])
    content_type: ContentType = Field(title="Тип контента", examples=["text"])
    content_data: Optional[dict] = Field(title="Контент")
    order_number: int = Field(title="Порядковый номер контента", examples=[1])


class PaginatedUserCoursesSchema(BaseModel):
    total_records: int = Field(title="Количество записей", examples=[12])
    page: int = Field(title="Страница", examples=[2])
    page_size: int = Field(title="Записей на странице", examples=[4])
    data: list[UserCoursesSchema] = Field(title="Список записей")
