import datetime
from redis import Redis
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_api.models.education import UserAnswers
from app_api.models.user import Users, UserBalances, Invoices
from .schemas import (UsersSchema, AddUserSchema, PatchUserSchema, UserBalancesSchema, PatchUserBalancesSchema,
                      BalancesAction, AddInvoicesSchema, InvoicesSchema)
from app_api.api.dependencies import get_record, add_record, Cache, patch_record
from ..user_courses.schemas import UserAnswersSchema


def get_user(
        db: Session,
        redis: Redis,
        telegram_id: int,
        only_check=False,
) -> UsersSchema | None | Users:
    """
    Извлекает пользователя из кэша или базы данных на основе идентификатора Telegram.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        telegram_id (int): Уникальный ID пользователя.
        only_check (bool): Флаг нужна ли только проверка, что бы в случае отсутствия записи не выводить ошибку

    Returns:
        Union[UsersSchema, None, Users]: Десериализованный объект пользователя, если он найден; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Users,
        base_model=UsersSchema,
        identifier=telegram_id,
        only_check=only_check,
        cache_key="user:telegram_id",
        filters=[["telegram_id", telegram_id, "eq"]],
    )

    return query


def check_user_exists(db: Session, redis: Redis, telegram_id: int):
    """
    Проверяет существование пользователя в базе данных на основе Telegram идентификатора.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        telegram_id (int): Уникальный ID пользователя в телеграмме

    Raises:
        HTTPException: Если пользователь уже существует, возвращает HTTP статус 409.
    """
    if get_user(db=db, redis=redis, telegram_id=telegram_id, only_check=True) is not None:
        raise HTTPException(status_code=409, detail="User already exists")


def add_user(
        db: Session,
        redis: Redis,
        telegram_id: int,
        user: AddUserSchema
) -> UsersSchema:
    """
    Добавляет нового пользователя в базу данных и кэш.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        telegram_id (int): Уникальный ID пользователя в телеграмме
        user (AddUserSchema): Схема для добавления пользователя, содержащая необходимую информацию

    Returns:
        UsersSchema: Объект схемы пользователя после его добавления в базу данных и кэш.
    """
    check_user_exists(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )

    user = Users(
        telegram_id=telegram_id,
        chat_id=user.chat_id,
        username=user.username
    )

    record = add_record(
        db=db,
        redis=redis,
        record=user,
        base_model=UsersSchema,
        cache_key=f"user:telegram_id:{telegram_id}"
    )
    balance = UserBalances(
        user_id=user.id
    )
    add_record(
        db=db,
        redis=redis,
        record=balance,
        base_model=UserBalancesSchema,
        cache_key=f"user_balance:user_id:{user.id}"
    )
    return record


def patch_user(
        db: Session,
        redis: Redis,
        telegram_id: int,
        user_patch: PatchUserSchema
) -> Users:
    """
    Обновляет информацию о пользователе в базе данных и удаляет соответствующий кэш, чтобы затем обновить его.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        telegram_id (int): Уникальный ID пользователя в телеграмме
        user_patch (PathUserSchema): Схема, содержащая обновляемые поля пользователя.

    Returns:
        Users: Объект пользователя после обновления.

    Raises:
        HTTPException: Если пользователь не найден, возвращает HTTP статус 404.
    """
    user = patch_record(
        db=db,
        redis=redis,
        sql_model=Users,
        base_model=UsersSchema,
        identifier=telegram_id,
        patch_schema=user_patch,
        filters=[["telegram_id", telegram_id, "eq"]],
        cache_key=f"user:telegram_id:{telegram_id}",
    )
    return user


def get_user_balance(
        db: Session,
        redis: Redis,
        telegram_id: int,
):
    """
    Получает баланс пользователя по его Telegram ID.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        telegram_id (int): Уникальный ID пользователя в Telegram.

    Returns:
        UserBalancesSchema: Схема баланса пользователя, содержащая всю информацию о текущем балансе.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    balance = get_record(
        db=db,
        redis=redis,
        sql_model=UserBalances,
        base_model=UserBalancesSchema,
        identifier=user.id,
        only_check=False,
        cache_key="user_balance:user_id",
        filters=[["user_id", user.id, "eq"]],
    )

    return balance


def patch_user_balance(
        db: Session,
        redis: Redis,
        telegram_id: int,
        user_balance_patch: PatchUserBalancesSchema
):
    """
    Обновляет баланс пользователя на основе предоставленной схемы обновления.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        telegram_id (int): Уникальный ID пользователя в Telegram.
        user_balance_patch (PatchUserBalancesSchema): Схема для обновления баланса пользователя,
         содержащая изменяемые данные.

    Returns:
        UserBalancesSchema: Обновленная схема баланса пользователя после применения изменений.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    query = db.scalars(select(UserBalances).filter_by(**{"user_id": user.id})).first()
    if user_balance_patch.action == BalancesAction.deposit:
        query.count_course += user_balance_patch.count_course
    elif user_balance_patch.action == BalancesAction.withdraw:
        query.count_course -= user_balance_patch.count_course
    else:
        raise HTTPException(status_code=409, detail=f"Action `{user_balance_patch.action}` not found")
    db.commit()
    db.refresh(query)
    cache = Cache(redis=redis, cache_key=f"user_balance:user_id:{user.id}", base_model=UserBalancesSchema)
    cache.delete_key()
    cache.set(query=query, ex=None)
    return query


def add_invoices(
        db: Session,
        redis: Redis,
        telegram_id: int,
        invoices: AddInvoicesSchema,
):
    """
    Добавляет платежную информацию

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        telegram_id (int): Уникальный ID пользователя в Telegram.
        invoices (AddInvoicesSchema): Схема для добавления инвойса пользователя,
         содержащая изменяемые данные.

    Returns:
        InvoicesSchema: Добавленная схема платежа.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    invoices = Invoices(
        user_id=user.id,
        payment_info=invoices.payment_info,
    )

    record = add_record(
        db=db,
        redis=redis,
        record=invoices,
        base_model=InvoicesSchema,
        cache_key=f"user_invoices:telegram_id:{telegram_id}",
        ex=1
    )
    return record


def get_user_answers(
        db: Session,
        redis: Redis,
        telegram_id: int,
        question_id: int
):
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    cache_key = f"user_answer:user_id:{user.id}:question_id"
    record = get_record(
        db=db,
        redis=redis,
        sql_model=UserAnswers,
        base_model=UserAnswersSchema,
        identifier=question_id,
        only_check=False,
        cache_key=cache_key,
        filters=[["user_id", user.id, "eq"], ["question_id", question_id, "eq"]],
        ex=600
    )
    return record
