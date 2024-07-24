from redis import Redis
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app_api.models.interaction import Prompts
from app_api.api.endpoints.gpt_models.crud import get_model
from app_api.api.dependencies import get_record, add_record, patch_record
from .schemas import PromptsSchema, AddPromptsSchema, PatchPromptsSchema


def get_prompt(
        db: Session,
        redis: Redis,
        name: str,
        only_check=False,
) -> PromptsSchema | None | Prompts:
    """
    Извлекает запись о промпте для GTP модели из кэша или базы данных по её названию.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        name (str): Название подсказки, которую нужно получить
        only_check (bool): Флаг, указывающий что при отсутствии записи не выводить ошибку

    Returns:
        Union[PromptsSchema, None, Prompts]: Объект промпта, если она найдена; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Prompts,
        base_model=PromptsSchema,
        identifier=name,
        only_check=only_check,
        cache_key="prompt:name",
        filters=[["name", name, "eq"]],
    )

    return query


def check_prompt_exists(db: Session, redis: Redis, name: str):
    """
    Проверяет существование промпта в базе данных по имени.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        name (str): Имя промпта

    Raises:
        HTTPException: Если пользователь уже существует, возвращает HTTP статус 409.
    """
    if get_prompt(db=db, redis=redis, name=name, only_check=True) is not None:
        raise HTTPException(status_code=409, detail="Prompt already exists")


def add_prompt(
        db: Session,
        redis: Redis,
        name: str,
        prompt: AddPromptsSchema
) -> PromptsSchema:
    """
    Добавляет промпт в базу данных и кэш.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        name (str): Имя промпта
        prompt (AddPromptsSchema): Схема для добавления промпта, содержащая необходимую информацию

    Returns:
        UsersSchema: Объект схемы пользователя после его добавления в базу данных и кэш.
    """
    check_prompt_exists(
        db=db,
        redis=redis,
        name=name
    )
    gpt_model = get_model(
        db=db,
        redis=redis,
        name=prompt.gpt_model
    )
    prompt = Prompts(
        name=name,
        system=prompt.system,
        user=prompt.user,
        gpt_model_id=gpt_model.id
    )

    record = add_record(
        db=db,
        redis=redis,
        record=prompt,
        base_model=PromptsSchema,
        cache_key=f"prompt:name:{name}"
    )
    return record


def patch_prompt(
        name: str,
        db: Session,
        redis: Redis,
        prompt_patch: PatchPromptsSchema
) -> Prompts:
    """
    Обновляет информацию промпта в базе данных и удаляет соответствующий кэш, чтобы затем обновить его.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        name (int): Имя промпта
        prompt_patch (PatchPromptsSchema): Схема, содержащая обновляемые поля пользователя.

    Returns:
        Prompts: Объект промпта после обновления.

    Raises:
        HTTPException: Если промпт не найден, возвращает HTTP статус 404.
    """
    prompt = patch_record(
        db=db,
        redis=redis,
        identifier=name,
        sql_model=Prompts,
        filters=[["name", name, "eq"]],
        base_model=PromptsSchema,
        patch_schema=prompt_patch,
        cache_key=f"prompt:name:{name}",
    )
    return prompt
