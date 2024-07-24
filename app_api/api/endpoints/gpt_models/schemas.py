from pydantic import BaseModel, Field


class BaseGPTModelsSchema(BaseModel):
    release: str = Field(title="Релиз (версия) модели", examples=["gpt-4-turbo-2024-04-09"])
    input_price: float = Field(title="Стоимость входящих 1M токенов", examples=[10.00])
    output_price: float = Field(title="Стоимость исходящих 1M токенов", examples=[30.00])
    description: str = Field(default=None, title="Никнейм в telegram", examples=["Самая последняя модель"])

    class Config:
        from_attributes = True


class GPTModelsSchema(BaseGPTModelsSchema):
    name: str = Field(title="Модель", examples=["GTP-4"])
    id: int = Field(title="Уникальный ID пользователя", examples=[1])


class AddGPTModelsSchema(BaseGPTModelsSchema):
    pass


class PatchGPTModelsSchema(BaseModel):
    release: str = Field(default=None, title="Релиз (версия) модели", examples=["gpt-4-turbo-2024-04-09"])
    input_price: float = Field(default=None, title="Стоимость входящих 1M токенов", examples=[10.00])
    output_price: float = Field(default=None, title="Стоимость исходящих 1M токенов", examples=[30.00])
    description: str = Field(default=None, title="Никнейм в telegram", examples=["Самая последняя модель"])


class GPTModelsNotFoundErrorSchema(BaseModel):
    detail: str = "Model not found"


class GPTModelsExistErrorSchema(BaseModel):
    detail: str = "Model already exists"
