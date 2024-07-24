from typing import Optional
from pydantic import BaseModel, Field

from schemas.user_schemas import PromoCode


class Stages:
    payment_verified: str = "payment_verified"
    clarifying_questions: str = "clarifying_questions"
    input_title: str = "input_title"
    apply_promo_code: str = "apply_promo_code"
    preparing_plan: str = "preparing_plan"


class ExtraInfo(BaseModel):
    title: Optional[str] = Field(title="Название курса", default=None)
    promo_info: Optional[PromoCode] = Field(
        title="Информация о промо коде", default=None
    )
    questions: Optional[dict[str, str | None]] = Field(
        title="Вопросы для уточнения темы", default=None
    )
    summary: Optional[str] = Field(title="Резюме", default=None)
    language: Optional[str] = Field(title="Язык для генерации материала", default=None)


class CreatedEducationStage(BaseModel):
    stage: str = Field(
        title="Стадия, на которой находится пользователь",
        examples=["Ввел тему"],
        default=None,
    )
    extra_info: ExtraInfo = Field(title="Доп информация", default=None)


class PaymentInfoStage(BaseModel):
    count_course: int = Field(title="Количество курсов")
    amount: float = Field(title="Сумма списания с пользователя")


class CheckTitleCourse(BaseModel):
    allow: bool = Field(
        title="Флаг проверки названия курса к обучению", examples=[True]
    )
    description: Optional[str] = Field(
        default=None, title="Описание, почему не был допущен", examples=[True]
    )


class CreatedCourse(BaseModel):
    course_id: int = Field(title="Уникальный ID курса", examples=[1])
    plan: dict = Field(title="План курса")


class PreparingQuestions(BaseModel):
    questions: list = Field(title="Список с вопросами для подготовки курса")


class SummarizeAnswers(BaseModel):
    summary: str | None
    is_validate: bool
