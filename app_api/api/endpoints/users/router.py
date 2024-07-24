from fastapi.openapi.models import Response
from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from app_api.db.redis_connection import get_redis
from fastapi import APIRouter, Depends, Path, Query
from .crud import get_user, add_user, patch_user, get_user_balance, patch_user_balance, get_user_answers, add_invoices
from .schemas import (PatchUserSchema, UsersSchema, UsersNotFoundErrorSchema, UsersExistErrorSchema, AddUserSchema,
                      UserBalancesSchema, PatchUserBalancesSchema, AnswersNotFoundErrorSchema, AddInvoicesSchema,
                      InvoicesSchema)
from ..user_courses.schemas import UserAnswersSchema

users = APIRouter(prefix="/users", tags=["Users"])


@users.get(path="/{telegram_id}",
           response_model=UsersSchema,
           summary="Получение информации о пользователе",
           responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
           )
def user_route(telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Получает информацию о пользователе используя его уникальный телеграм ID.

    Этот эндпоинт осуществляет поиск пользователя, используя его уникальный телеграм ID.


    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.

    ### Возвращает
    - `UsersSchema`: Схема данных о пользователе

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    user = get_user(db=db, redis=redis, telegram_id=telegram_id)
    return user


@users.post(path="/{telegram_id}",
            response_model=UsersSchema,
            summary="Добавление пользователя в базу",
            responses={409: {"model": UsersExistErrorSchema, "description": "User already exists"}}
            )
def user_route(user: AddUserSchema,
               telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Добавляет пользователя в базу.

    Этот эндпоинт осуществляет добавление пользователя в базу.


    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.

    ### Возвращает
    - `UsersSchema`: Схема данных о пользователе

    ### Исключения
    - `HTTPException` с кодом 409: Вызывается, если пользователь с указанным ID уже есть в базу.
    """
    user = add_user(db=db, redis=redis, telegram_id=telegram_id, user=user)
    return user


@users.patch(path="/{telegram_id}",
             response_model=UsersSchema,
             summary="Обновляет значения пользователя в базе",
             responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
             )
def user_route(user: PatchUserSchema,
               telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Обновляет значения пользователя в базе

    Этот эндпоинт предназначен для обновления атрибутов пользователя в базе, используя его уникальный телеграм ID.


    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.

    ### Возвращает
    - `UsersSchema`: Схема данных о пользователе

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    user = patch_user(db=db, redis=redis, telegram_id=telegram_id, user_patch=user)
    return user


@users.get(path="/{telegram_id}/balance",
           response_model=UserBalancesSchema,
           summary="Получение информации о балансе пользователя",
           responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
           )
def user_route(telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Получает информацию о балансе пользователе используя его уникальный телеграм ID.

    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.

    ### Возвращает
    - `UsersBalanceSchema`: Схема данных о балансе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    balance = get_user_balance(db=db, redis=redis, telegram_id=telegram_id)
    return balance


@users.get(path="/{telegram_id}/answers",
           response_model=UserAnswersSchema,
           summary="Проверяет наличие ответа на конкретный вопрос",
           responses={404: {"model": AnswersNotFoundErrorSchema, "description": "Answer not found"}}
           )
def user_route(question_id: int = Query(description="ID вопроса"),
               telegram_id: int = Path(description="Уникальный телеграм "
                                                   "ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Проверяет наличие ответа пользователя на конкретный вопрос используя его уникальный телеграм ID и ID вопроса.

    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь или ответ с указанным ID не найден.
    """
    answer = get_user_answers(db=db, redis=redis, telegram_id=telegram_id, question_id=question_id)
    return answer


@users.patch(path="/{telegram_id}/balance",
             response_model=UserBalancesSchema,
             summary="Списание или пополнение баланса",
             responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
             )
def user_route(user_balance_patch: PatchUserBalancesSchema,
               telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Либо списывает, либо пополняет баланс пользователя используя его уникальный телеграм ID.

    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.
    - `action`: Списание или пополнение баланса
    - `amount`: Сумма пополнения или списания

    ### Возвращает
    - `UsersBalanceSchema`: Схема данных о балансе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    balance = patch_user_balance(db=db, redis=redis, telegram_id=telegram_id, user_balance_patch=user_balance_patch)
    return balance


@users.post(path="/{telegram_id}/invoices",
            response_model=InvoicesSchema,
            summary="Добавление инвойса пользователю",
            responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
            )
def user_route(invoices: AddInvoicesSchema,
               telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
               db: Session = Depends(get_db),
               redis: Redis = Depends(get_redis)
               ):
    """
    Добавляет платежный инвойс пользователю.

    ### Параметры
    - `telegram_id` (int): Уникальный ID пользователя в telegram.


    ### Возвращает
    - `InvoicesSchema`: Схема данных о добавленном инвойсе

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    invoice = add_invoices(db=db, redis=redis, telegram_id=telegram_id, invoices=invoices)
    return invoice
