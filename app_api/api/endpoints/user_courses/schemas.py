from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app_api.models.education import CurrentStage


class BaseUserCoursesSchema(BaseModel):
    course_id: int = Field(title="Уникальный ID курса", examples=[1])

    class Config:
        from_attributes = True


class UserCoursesSchema(BaseUserCoursesSchema):
    id: int = Field(title="Уникальный ID", examples=[1])
    user_id: int = Field(title="Уникальный ID пользователя", examples=[1])
    title: str = Field(title="Название курса", examples=["ООП в Python"])
    current_module_id: int = Field(title="Уникальный ID модуля, на котором находится пользователь", examples=[1])
    current_sub_module_id: int = Field(title="Уникальный ID субмодуля, на котором находится пользователь", examples=[1])
    current_stage: str = Field(title="Стадия, на котрой находится пользователь", examples=["learning"])
    current_order_number: int = Field(title="Номер материала или вопроса в блоке", examples=[1])
    plan: dict = Field(title="План курса")
    active: bool = Field(title="Активен ли курс", examples=[True])
    archived: bool = Field(title="Архивирован ли курс", examples=[False])
    finished: bool = Field(title="Закончен ли курс", examples=[False])
    input_token: Optional[int] = Field(default=None, title="Количество потраченных входящих токенов", examples=[11731])
    output_token: Optional[int] = Field(default=None, title="Количество потраченных исходящих токенов", examples=[9731])
    spent_amount: Optional[float] = Field(default=None, title="Потраченная сумма", examples=[0.86])
    usage_count: int = Field(title="Количество перепрохождения курса пользователем", examples=[1])
    rating: int = Field(title="Рейтинг курса", examples=[1])
    created_at: datetime = Field(title="Дата добавления/создания куса пользователем")
    last_updated_at: Optional[datetime] = Field(title="Дата изменения")


class AddUserCoursesSchema(BaseUserCoursesSchema):
    current_stage: CurrentStage = Field(title="Стадия курса", examples=["not_generated"])


class AddUserAnswersSchema(BaseModel):
    question_id: int = Field(title="ID Вопроса", examples=[1])
    answer: str | None = Field(title="Ответ пользователя", examples=["Ответ"])
    score: Optional[int] = Field(title="Оценка", examples=[5])
    feedback: Optional[str] = Field(title="Комментарий системы", examples=["..."])

    class Config:
        from_attributes = True


class UserAnswersSchema(AddUserAnswersSchema):
    id: int = Field(title="ID ответа", examples=[1])
    user_id: int = Field(title="ID пользователя", examples=[1])


class CheckAnswersSchema(BaseModel):
    question: str = Field(title="Вопрос по курсу", examples=["Вопрос"])
    answer: str = Field(title="Ответ пользователя", examples=["Ответ"])
    language: str = Field(title="Язык, на котором нужно дать комментарий", examples=["ru"])


class HelpAnswersSchema(CheckAnswersSchema):
    feedback: str = Field(title="Правильный ответ (обратная связь)", examples=["Неправильны ответ"])


class PaginatedUserCoursesSchema(BaseModel):
    total_records: int = Field(title="Количество записей", examples=[12])
    page: int = Field(title="Страница", examples=[2])
    page_size: int = Field(title="Записей на странице", examples=[4])
    data: list[UserCoursesSchema] = Field(title="Список записей")

    class Config:
        from_attributes = True


class UserCoursesNotFoundErrorSchema(BaseModel):
    detail: str = "User course not found"


class NextStageIDSchema(BaseModel):
    current_module_id: int = Field(title="Следующая id модуля", examples=[1])
    current_sub_module_id: int = Field(title="Следующая id суб модуля", examples=[1])
    current_order_number: int = Field(title="Следующий порядковый номер", examples=[1])


class UserCoursesNextStageSchema(BaseModel):
    stage: CurrentStage = Field(title="Следующая стадия курса", examples=["education"])
    data: Optional[NextStageIDSchema] = Field(default={}, title="Следующие ID обучения")


class PatchUserCoursesSchema(BaseModel):
    current_module_id: int | None = Field(title="Уникальный ID модуля, на котором находится пользователь", default=None)
    current_sub_module_id: int | None = Field(title="Уникальный ID субмодуля, на котором находится пользователь",
                                              default=None)
    current_stage: str = Field(title="Стадия, на котрой находится пользователь", default=None)
    current_order_number: int | None = Field(title="Номер материала или вопроса в блоке", default=None)
    plan: dict = Field(title="План курса", default=None)
    active: bool = Field(title="Активен ли курс", default=None)
    archived: bool = Field(title="Архивирован ли курс", default=None)
    finished: bool = Field(title="Закончен ли курс", default=None)
    usage_count: int = Field(title="Количество перепрохождения курса пользователем", default=None)
    rating: int = Field(title="Рейтинг курса", default=None)
    input_token: int = Field(title="Количество входящих токенов", default=None)
    output_token: int = Field(title="Количество исходящих токенов", default=None)
    spent_amount: float = Field(title="Общие затраты на генерацию", default=None)
