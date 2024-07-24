from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, Path
from app_api.db.redis_connection import get_redis
from .crud import get_model, add_model, patch_model
from .schemas import (PatchGPTModelsSchema, GPTModelsSchema, GPTModelsNotFoundErrorSchema,
                      GPTModelsExistErrorSchema, AddGPTModelsSchema)

models = APIRouter(prefix="/models", tags=["GPT Models"])


@models.get(path="/{name}",
            response_model=GPTModelsSchema,
            summary="Получение информации о модели",
            responses={404: {"model": GPTModelsNotFoundErrorSchema, "description": "Model not found"}}
            )
def model_route(name: str = Path(description="Имя модели", example="GPT-4"),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Получает информацию о модели используя ее имя.

    Этот эндпоинт осуществляет поиск GPT моделей, используя ее имя.


    ### Параметры
    - `name` (str): Имя модели.

    ### Возвращает
    - `GPTModelsSchema`: Схема данных о модели

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если модель с указанным именем не найден.
    """
    model = get_model(db, redis, name=name)
    return model


@models.post(path="/{name}",
             response_model=GPTModelsSchema,
             summary="Добавление модель в базу",
             responses={409: {"model": GPTModelsExistErrorSchema, "description": "Model already exists"}}
             )
def model_route(model: AddGPTModelsSchema,
                name: str = Path(description="Имя модели", example="GPT-4"),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Добавляет модель в базу.

    Этот эндпоинт осуществляет добавление модели.


    ### Параметры
    - `name` (str): Имя модели.

    ### Возвращает
    - `GPTModelsSchema`: Схема данных о модели

    ### Исключения
    - `HTTPException` с кодом 409: Вызывается, если модель с указанным именем уже есть.
    """
    model = add_model(db, redis, name=name, model=model)
    return model


@models.patch(path="/{name}",
              response_model=GPTModelsSchema,
              summary="Обновляет значения модели в базе",
              responses={404: {"model": GPTModelsNotFoundErrorSchema, "description": "Model not found"}}
              )
def user_route(model: PatchGPTModelsSchema,
               name: str = Path(description="Имя модели", example="GPT-4"),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Обновляет значения модели в базе

    Этот эндпоинт предназначен для обновления атрибутов модели в базе, используя ее имя.


    ### Параметры
    - `name` (str): Имя модели.

    ### Возвращает
    - `UsersSchema`: Схема данных о пользователе

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    model = patch_model(db, redis, name=name, model_patch=model)
    return model
