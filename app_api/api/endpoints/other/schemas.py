from typing import Literal

from pydantic import BaseModel, Field


class SurveySchema(BaseModel):
    data: dict


class SummarizeSchema(BaseModel):
    summary: str | None
    is_validate: bool


class GenerateImageSchema(BaseModel):
    course_title: str
    sub_module_title: str
    content_title: str
    size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024"
    quality: Literal["standard", "hd"] = "standard"


class ContentQuestionSchema(BaseModel):
    content: str = Field(title="Пройденный материал")
    history: list = Field(title="История диалога")
    language: str = Field(title="Язык, на котором надо дать ответ")
    user_course_id: int = Field(title="ID пользовательского курса")
