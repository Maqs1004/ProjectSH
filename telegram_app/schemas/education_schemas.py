import enum
from typing import Optional
from pydantic import BaseModel, Field
from schemas.course_schemas import CurrentStage


class QuestionType(enum.Enum):
    open = "open"
    multiple_choice = "multiple_choice"


class NextStageIDSchema(BaseModel):
    current_module_id: int = Field(
        title="Следующая id модуля", examples=[1], default=None
    )
    current_sub_module_id: int = Field(
        title="Следующая id суб модуля", examples=[1], default=None
    )
    current_order_number: int = Field(
        title="Следующий порядковый номер", examples=[1], default=None
    )


class UserCoursesNextStageSchema(BaseModel):
    stage: CurrentStage = Field(title="Следующая стадия курса", examples=["education"])
    data: Optional[NextStageIDSchema] = Field(default={}, title="Следующие ID обучения")


class UserAnswersSchema(BaseModel):
    id: int = Field(title="ID ответа", examples=[1])
    user_id: int = Field(title="ID пользователя", examples=[1])
    question_id: int = Field(title="ID Вопроса", examples=[1])
    answer: str | None = Field(title="Ответ пользователя", examples=["Ответ"])
    score: Optional[int] = Field(title="Оценка", examples=[5])
    feedback: Optional[str] = Field(title="Комментарий системы", examples=["..."])


class QuestionsSchema(BaseModel):
    id: int = Field(title="Уникальный ID", examples=[1])
    sub_module_id: int = Field(title="Уникальный ID субмодуля", examples=[1])
    content: str = Field(title="Вопрос", examples=["Кто был царем в 1718 году"])
    question_type: QuestionType = Field(title="Тип вопроса", examples=["open"])
    options: Optional[list] = Field(title="Ответы")
    order_number: int = Field(title="Порядковый номер контента", examples=[1])


class BaseAnswerSchema(BaseModel):
    response: str | None


class QuestionAnswersSchema(BaseAnswerSchema):
    score: int


class ContentAnswerSchema(BaseAnswerSchema):
    is_validate: bool


class HelpSchema(BaseAnswerSchema):
    pass


class MessageStorageSchema(BaseModel):
    messages: list
