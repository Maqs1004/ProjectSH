from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app_api.models.education import QuestionType, ContentType


class CourseTitleSchema(BaseModel):
    title: str = Field(title="Название курса, который планируется изучать")
    language: str = Field(title="Язык")


class PromoCode(BaseModel):
    code: Optional[str] = Field(title="Промо код", default=None)
    discount_type: Optional[str] = Field(title="Тип скидки, процент или сумма", default=None)
    discount_value: Optional[float] = Field(title="Значение скидки", default=None, examples=[95])
    expiry_date: Optional[datetime] = Field(title="Дата, когда заканчивается код", default=None)
    course_content_volume: Optional[str] = Field(title="Размер курса, на который применяется скидка", default=None)


class CreateCoursePlanSchema(BaseModel):
    title: Optional[str] = Field(title="Название курса", default=None)
    promo_info: Optional[PromoCode] = Field(title="Информация о промо коде", default=None)
    questions: Optional[dict[str, str]] = Field(title="Вопросы для уточнения темы", default=None)
    summary: Optional[str] = Field(title="Резюме", default=None)
    language: Optional[str] = Field(title="Язык для генерации материала", default=None)


class BaseCourseSchema(BaseModel):
    available: bool = Field(title="Доступен ли курс к обучению", examples=[True])
    is_generated: bool = Field(title="Сгенерирован ли материал для этого курса", examples=[True])

    class Config:
        from_attributes = True


class CourseSchema(BaseCourseSchema):
    id: int = Field(title="Уникальный ID", examples=[1])
    title: str = Field(title="Название курса", examples=["ООП в Python"])
    description: Optional[str] = Field(default=None, title="Описание Курса", examples=["Этот курс ..."])
    created_at: datetime = Field(title="Дата создания курса")
    is_personalized: bool = Field(title="Был ли этот курс персонализирован под пользователя", examples=[True])
    stat_modul_id: int = Field(title="ID модуля с которого начинается обучение", examples=[1])
    stat_sub_modul_id: int = Field(title="ID субмодуля с которого начинается обучение", examples=[1])
    default_plan: dict = Field(title="План обучения", examples=[1])
    summary: Optional[str] = Field(title="Информация о пользователе при составлении плана", examples=[1])


class PatchCourseSchema(BaseModel):
    available: bool = Field(default=None, title="Доступен ли курс для изменений в данный момент", examples=[True])
    is_generated: bool = Field(default=None, title="Сгенерирован ли материал для этого курса", examples=[True])


class ModulesSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    course_id: int = Field(title="Уникальный ID курса", examples=[1])
    title: str = Field(title="Название модуля", examples=["Введение в объектно-ориентированное программирование (ООП)"])
    description: Optional[str] = Field(title="Описание модуля", examples=["...."])
    order_number: int = Field(title="Порядковый номер модуля", examples=[1])

    class Config:
        from_attributes = True


class SubModulesSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    module_id: int = Field(title="Уникальный ID модуля", examples=[1])
    title: str = Field(title="Название модуля", examples=["Основные принципы ООП"])
    description: Optional[str] = Field(title="Описание субмодуля", examples=["...."])
    order_number: int = Field(title="Порядковый номер субмодуля", examples=[1])

    class Config:
        from_attributes = True


class ModuleContentsSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    sub_module_id: int = Field(title="Уникальный ID субмодуля", examples=[1])
    title: str = Field(title="Название контента", examples=["Основные принципы ООП"])
    content_type: ContentType = Field(title="Тип контента", examples=["text"])
    content_data: Optional[dict] = Field(title="Контент")
    order_number: int = Field(title="Порядковый номер контента", examples=[1])

    class Config:
        from_attributes = True


class QuestionsSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    sub_module_id: int = Field(title="Уникальный ID субмодуля", examples=[1])
    content: str = Field(title="Вопрос", examples=["Кто был царем в 1718 году"])
    question_type: QuestionType = Field(title="Тип вопроса", examples=["open"])
    options: Optional[list] = Field(title="Ответы")
    order_number: int = Field(title="Порядковый номер контента", examples=[1])

    class Config:
        from_attributes = True


class QuestionsForSurveySchema(BaseModel):
    questions: list[str] = Field(title="Список вопросов для уточнения темы", examples=[["Кто ты из winx"]])
