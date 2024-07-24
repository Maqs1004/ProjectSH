from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, Path, Query
from app_api.db.redis_connection import get_redis
from .schemas import (TranslationSchema, TranslationNotFoundErrorSchema, AddTranslationSchema, PatchTranslationsSchema)
from .crud import (get_translation, add_translation, patch_translation)

translations = APIRouter(prefix="/translation", tags=["Translation"])


@translations.get(path="",
                  response_model=TranslationSchema,
                  summary="Получение сообщения в нужном переводе",
                  responses={404: {"model": TranslationNotFoundErrorSchema, "description": "Translation not found"}}
                  )
def translation_route(message_key: str = Query(description="Ключ, для поиска текста"),
                      language_code: str = Query(description="Язык"),
                      db: Session = Depends(get_db),
                      redis: Redis = Depends(get_redis)
                      ):
    """
    Получает текст для сообщения по ключу и языку.

    ### Параметры
    - `language_code` (int): Язык, текс которого надо искать.
    - `message_key` (str): Ключ, по которому надо искать

    ### Возвращает
    - `TranslationSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если ничего не найдено.
    """
    message = get_translation(db=db, redis=redis, message_key=message_key, language_code=language_code)
    return message


@translations.post(path="",
                   response_model=TranslationSchema,
                   summary="Добавляет перевод"
                   )
def translation_route(translation: AddTranslationSchema,
                      db: Session = Depends(get_db),
                      redis: Redis = Depends(get_redis),
                      ):
    """
    Добавляет ключ, код языка и сам текс, который будет выводится пользователю.


    ### Возвращает
    - `TranslationSchema`: Схема данных о курсе пользователя

    """
    user_course = add_translation(db=db, redis=redis, translation=translation)
    return user_course


@translations.patch(path="",
                    response_model=TranslationSchema,
                    summary="Обновляет значения текста в базе",
                    responses={404: {"model": TranslationNotFoundErrorSchema, "description": "Translation not found"}}
                    )
def translation_route(translation_patch: PatchTranslationsSchema,
                      message_key: str = Query(description="Ключ, для поиска текста"),
                      language_code: str = Query(description="Язык"),
                      db: Session = Depends(get_db),
                      redis: Redis = Depends(get_redis)
                      ):
    """
    Обновляет значения текста в базе

    Этот эндпоинт предназначен для обновления текста перевода для конкретного ключа и языка.


    ### Параметры
    - `message_key` (str): ключ перевода.
    - `language_code` (str) Язык


    ### Возвращает
    - `TranslationSchema`: Схема данных о промпте

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если запись с указанными параметрами не найдена.
    """
    translation = patch_translation(db=db, redis=redis, translation_patch=translation_patch, message_key=message_key,
                                    language_code=language_code)
    return translation

# @translations.delete(path="",
#                      response_model=TranslationSchema,
#                      summary="Удаление ключа с переводом",
#                      responses={404: {"model": TranslationNotFoundErrorSchema,
#                      "description": "Translation not found"}}
#                      )
# def translation_route(message_key: str = Query(description="Ключ, для поиска текста"),
#                       language_code: str = Query(description="Язык"),
#                       db: Session = Depends(get_db),
#                       redis: Redis = Depends(get_redis)
#                       ):
#     """
#     Удаляет запись с переводом.
#
#     ### Параметры
#     - `language_code` (int): Язык, текс которого надо искать.
#     - `message_key` (str): Ключ, по которому надо искать
#
#     ### Возвращает
#     - `status_code`: 204
#
#     ### Исключения
#     - `HTTPException` с кодом 404: Вызывается, если ничего не найдено.
#     """
#     message = delete_translation(db=db, redis=redis, message_key=message_key, language_code=language_code)
#     return message
