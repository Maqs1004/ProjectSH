from typing import Optional
from pydantic import BaseModel, Field


class BaseTranslationSchema(BaseModel):
    message_key: str = Field(title="Название промпта в системе", examples=["hello_message"])
    language_code: str = Field(title="Название промпта в системе", examples=["EN"])
    message_text: str = Field(title="Название промпта в системе", examples=["Hello World"])

    class Config:
        from_attributes = True


class TranslationSchema(BaseTranslationSchema):
    id: int = Field(title="Уникальный ID", examples=[1])


class TranslationNotFoundErrorSchema(BaseModel):
    detail: str = "Translation not found"


class AddTranslationSchema(BaseTranslationSchema):
    pass


class PatchTranslationsSchema(BaseModel):
    message_text: str = Field(title="Название промпта в системе", examples=["Hello World"])
