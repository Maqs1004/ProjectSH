from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, Path
from app_api.db.redis_connection import get_redis
from .crud import get_prompt, add_prompt, patch_prompt
from .schemas import (PatchPromptsSchema, PromptsSchema, PromptsNotFoundErrorSchema, PromptsExistErrorSchema,
                      AddPromptsSchema)

prompts = APIRouter(prefix="/prompts", tags=["GPT Prompts"])


@prompts.get(path="/{name}",
             response_model=PromptsSchema,
             summary="Получение информации о промпте",
             responses={404: {"model": PromptsNotFoundErrorSchema, "description": "Model not found"}}
             )
def prompt_route(name: str = Path(description="Имя промпта", example="allow_topic"),
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    """
    Получает информацию о промпте используя ее имя.

    Этот эндпоинт осуществляет поиск промпта, используя ее имя.


    ### Параметры
    - `name` (str): Имя промпта.

    ### Возвращает
    - `PromptsSchema`: Схема данных о промпте

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если промпт с указанным именем не найден.
    """
    prompt = get_prompt(db=db, redis=redis, name=name)
    return prompt


@prompts.post(path="/{name}",
              response_model=PromptsSchema,
              summary="Добавление модель в базу",
              responses={409: {"model": PromptsExistErrorSchema, "description": "Prompts already exists"}}
              )
def prompt_route(prompt: AddPromptsSchema,
                 name: str = Path(description="Имя промпта", example="allow_topic"),
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    """
    Добавляет промпт в базу.

    Этот эндпоинт осуществляет добавление промпта в базу данных с сообщениями и привязкой к конкретной GPT модели.


    ### Параметры
    - `name` (str): Имя промпта.

    ### Возвращает
    - `PromptsSchema`: Схема данных о модели

    ### Исключения
    - `HTTPException` с кодом 409: Вызывается, если модель с указанным именем уже есть.
    """
    prompt = add_prompt(db=db, redis=redis, name=name, prompt=prompt)
    return prompt


@prompts.patch(path="/{name}",
               response_model=PromptsSchema,
               summary="Обновляет значения модели в базе",
               responses={404: {"model": PromptsNotFoundErrorSchema, "description": "Model not found"}}
               )
def prompt_route(prompt: PatchPromptsSchema,
                 name: str = Path(description="Имя промпта", example="allow_topic"),
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    """
    Обновляет значения промпта в базе

    Этот эндпоинт предназначен для обновления атрибутов промпта в базе, используя его имя.


    ### Параметры
    - `name` (str): Имя промпта.

    ### Возвращает
    - `PromptsSchema`: Схема данных о промпте

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    prompt = patch_prompt(db=db, redis=redis, name=name, prompt_patch=prompt)
    return prompt
