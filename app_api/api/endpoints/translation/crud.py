import psycopg2
from fastapi import HTTPException
from redis import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app_api.api.dependencies import get_record, add_record, patch_record
from app_api.models.interaction import Translation
from .schemas import TranslationSchema, AddTranslationSchema, PatchTranslationsSchema


def get_translation(
        db: Session,
        redis: Redis,
        message_key: str,
        language_code: str,
        only_check=False,
) -> TranslationSchema | None | Translation:
    """
    Извлекает запись перевода из кэша или базы данных по ключу и языку.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        message_key (str): Ключ сообщения
        language_code (str): Язык
        only_check (bool): Флаг, указывающий что при отсутствии записи не выводить ошибку

    Returns:
        Union[TranslationSchema, None, Translation]: Объект перевода, если она найдена; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Translation,
        base_model=TranslationSchema,
        identifier=f"message_key:{message_key}:language_code:{language_code}",
        only_check=only_check,
        cache_key="translation",
        filters=[["message_key", message_key, "eq"], ["language_code", language_code, "eq"]],
    )

    return query


def add_translation(
        db: Session,
        redis: Redis,
        translation: AddTranslationSchema
) -> TranslationSchema:
    """
    Добавляет перевод в базу данных и кэш.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        translation (AddTranslationSchema): Схема для добавления перевода, содержащая необходимую информацию

    Returns:
        TranslationSchema: Объект схемы перевода после его добавления в базу данных и кэш.
    """
    translation = Translation(
        message_key=translation.message_key,
        language_code=translation.language_code,
        message_text=translation.message_text
    )
    try:
        record = add_record(
            db=db,
            redis=redis,
            record=translation,
            base_model=TranslationSchema,
            cache_key=f"translation:message_key:{translation.message_key}:language_code:{translation.language_code}"
        )
        return record
    except IntegrityError as e:
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            error_message = str(e.orig)
            if "_message_key_language_uc" in error_message:
                raise HTTPException(status_code=409, detail="Translation already exists")


def patch_translation(
        message_key: str,
        language_code: str,
        db: Session,
        redis: Redis,
        translation_patch: PatchTranslationsSchema
) -> Translation:
    """
    Обновляет текст перевода в базе данных и удаляет соответствующий кэш, чтобы затем обновить его.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        message_key (str): Ключ сообщения
        language_code (language_code): Язык сообщения
        translation_patch (PatchTranslationsSchema): Схема, содержащая обновляемые поля пользователя.

    Returns:
        Translation: Объект промпта после обновления.

    Raises:
        HTTPException: Если значение не найдено, возвращает HTTP статус 404.
    """
    translation = patch_record(
        db=db,
        redis=redis,
        identifier=f"{message_key}&&{language_code}",
        sql_model=Translation,
        filters=[["message_key", message_key, "eq"], ["language_code", language_code, "eq"]],
        base_model=TranslationSchema,
        patch_schema=translation_patch,
        cache_key=f"translation:message_key:{message_key}:language_code:{language_code}",
    )
    return translation
