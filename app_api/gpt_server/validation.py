from typing import Optional

from pydantic import BaseModel, Field


class ContentModel(BaseModel):
    title: str
    content: str


class ResponseModelContent(BaseModel):
    title: str
    introduction: str
    sections: list[ContentModel]
    conclusion: str


class ContentResponse(BaseModel):
    response: ResponseModelContent


class OpenQuestionResponse(BaseModel):
    question: str


class AnswersMultipleChoice(BaseModel):
    option: str
    is_correct: bool


class MultipleChoiceQuestionResponse(BaseModel):
    question: str
    answers: list[AnswersMultipleChoice]


class AllowCourseResponse(BaseModel):
    allow: bool = Field(title="Флаг доступности темы к обучению", examples=[True])
    description: str = Field(title="Описание, почему доступна или не доступна данная", examples=["Потому что"])


plan = {
    "Введение в объектно-ориентированное программирование (ООП)": [
        {"Основные принципы ООП": ["Инкапсуляция", "Наследование", "Полиморфизм", "Абстракция"]},
        {"Преимущества ООП": ["Модульность", "Повторное использование кода", "Упрощение сложных программ"]}
    ],
    "ООП в Python": [
        {"Классы и объекты": ["Создание класса", "Создание объекта", "Конструктор __init__"]},
        {"Наследование и полиморфизм": ["Примеры наследования", "Методы переопределения", "Использование super()"]},
        {"Инкапсуляция и абстракция": ["Использование приватных переменных", "Абстрактные классы и методы"]}
    ],
    "Практическое применение ООП в Python": [
        {"Разработка простой игры": ["Планирование архитектуры", "Реализация с использованием классов"]},
        {"Проект 'Учётная система'": ["Описание проекта", "Применение ООП-подходов"]}
    ]
}


class PlanResponse(BaseModel):
    course_id: Optional[int] = Field(default=None, title="ID курса", examples=[1])
    plan: dict[str, list[dict[str, list[str]]]] = Field(title="Сгенерированный план", examples=[plan])


class SummarizeModel(BaseModel):
    summary: str | None
    is_validate: bool


class PromptResponse(BaseModel):
    prompt: str


class ContentAnswerResponse(BaseModel):
    response: str | None
    is_validate: bool


class SurveyResponse(BaseModel):
    questions: list[str]


class AnswersResponse(BaseModel):
    response: str
    score: int


class HelpResponse(BaseModel):
    response: str
