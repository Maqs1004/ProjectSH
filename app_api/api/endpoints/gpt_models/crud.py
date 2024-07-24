from redis import Redis
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app_api.models.interaction import GPTModels
from app_api.api.dependencies import get_record, add_record, Cache, patch_record
from .schemas import GPTModelsSchema, AddGPTModelsSchema, PatchGPTModelsSchema


def get_model(
        db: Session,
        redis: Redis,
        name: str,
        only_check=False,
) -> GPTModelsSchema | None | GPTModels:
    """
    Извлекает информацию о GPT модели из кэша или базы данных по ее названию.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        name (str): Название модели.
        only_check (bool): Флаг нужна ли только проверка, что бы в случае отсутствия записи не выводить ошибку

    Returns:
        Union[GPTModelsSchema, None, GPTModels]: Десериализованный объект модели, если он найден; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        identifier=name,
        sql_model=GPTModels,
        cache_key="gpt_model:name",
        only_check=only_check,
        filters=[["name", name, "eq"]],
        base_model=GPTModelsSchema,
    )

    return query


def get_model_by_id(
        db: Session,
        redis: Redis,
        model_id: int,
        only_check=False,
) -> GPTModelsSchema | None | GPTModels:
    """
    Извлекает информацию о GPT модели из кэша или базы данных по ее названию.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        model_id (int): ID модели модели.
        only_check (bool): Флаг нужна ли только проверка, что бы в случае отсутствия записи не выводить ошибку

    Returns:
        Union[GPTModelsSchema, None, GPTModels]: Десериализованный объект модели, если он найден; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        identifier=model_id,
        sql_model=GPTModels,
        cache_key="gpt_model:id",
        only_check=only_check,
        filters=[["id", model_id, "eq"]],
        base_model=GPTModelsSchema,
    )

    return query


def check_model_exists(db: Session, redis: Redis, name: str):
    """
    Проверяет существование пользователя в базе данных на основе Telegram идентификатора.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        name (str): Название модели

    Raises:
        HTTPException: Если пользователь уже существует, возвращает HTTP статус 409.
    """
    if get_model(db=db, redis=redis, name=name, only_check=True) is not None:
        raise HTTPException(status_code=409, detail="GPT model already exists")


def add_model(
        db: Session,
        redis: Redis,
        name: str,
        model: AddGPTModelsSchema
) -> GPTModels | GPTModelsSchema:
    """
    Добавляет новую модель в базу данных и кэш.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        name (str): Имя GPT модели
        model (AddGPTModelsSchema): Схема для добавления GPT модели, содержащая необходимую информацию,
         такую как стоимость и опционально описание

    Returns:
        GPTModels | GPTModelsSchema: Объект схемы GPT модели после ее добавления в базу данных и кэш.
    """
    check_model_exists(
        db=db,
        name=name,
        redis=redis,
    )

    record = GPTModels(
        name=name,
        release=model.release,
        description=model.description,
        input_price=model.input_price,
        output_price=model.output_price
    )

    record = add_record(
        db=db,
        redis=redis,
        record=record,
        base_model=GPTModelsSchema,
        cache_key=f"gpt_model:name:{name}"
    )

    return record


def patch_model(
        db: Session,
        redis: Redis,
        name: str,
        model_patch: PatchGPTModelsSchema
) -> GPTModels:
    """
    Обновляет информацию о пользователе в базе данных и удаляет соответствующий кэш, чтобы затем обновить его.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        name (str): Имя GPT модели
        model_patch (PatchGPTModelsSchema): Схема, содержащая обновляемые поля модели

    Returns:
        GPTModels: Объект пользователя после обновления.

    Raises:
        HTTPException: Если пользователь не найден, возвращает HTTP статус 404.
    """
    model = patch_record(
        db=db,
        redis=redis,
        identifier=name,
        sql_model=GPTModels,
        patch_schema=model_patch,
        filters=[["name", name, "eq"]],
        base_model=GPTModelsSchema,
        cache_key=f"gpt_model:name:{name}",
    )
    return model
