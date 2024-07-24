from typing import Optional
from pydantic import BaseModel, Field


class BasePromptsSchema(BaseModel):
    system: Optional[str] = Field(title="Системное сообщение для модели", examples=["Представь что ты..."])
    user: str = Field(title="Сообщение пользователя для модели", examples=["Напиши мне ..."])

    class Config:
        from_attributes = True


class PromptsSchema(BasePromptsSchema):
    name: str = Field(title="Название промпта в системе", examples=["allow_topic"])
    id: int = Field(title="Уникальный ID", examples=[1])
    gpt_model_id: int = Field(title="ID GPT модели, которая используется для генерации", examples=[1])


class AddPromptsSchema(BaseModel):
    system: Optional[str] = Field(default=None, title="Системное сообщение модели", examples=["Представь что ты..."])
    user: Optional[str] = Field(default=None, title="Сообщение пользователя модели", examples=["Напиши мне ..."])
    gpt_model: str = Field(title="Имя GPT модели", examples=["GPT-4 Turbo"])


class PatchPromptsSchema(BaseModel):
    system: Optional[str] = Field(default=None, title="Системное сообщение модели", examples=["Представь что ты..."])
    user: Optional[str] = Field(default=None, title="Сообщение пользователя модели", examples=["Напиши мне ..."])
    gpt_model_id: int = Field(title="Имя GPT модели", examples=[2])


class PromptsNotFoundErrorSchema(BaseModel):
    detail: str = "Prompts not found"


class PromptsExistErrorSchema(BaseModel):
    detail: str = "Prompts already exists"
