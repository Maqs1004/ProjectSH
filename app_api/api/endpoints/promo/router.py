from fastapi.openapi.models import Response
from redis import Redis
from sqlalchemy.orm import Session

from app_api.api.endpoints.promo.crud import (get_promo_code, add_promo_code, patch_promo_code, check_used_promo_code,
                                              apply_promo_code)
from app_api.api.endpoints.promo.schemas import (PromoCodeSchema, PromoCodeNotFoundErrorSchema,
                                                 PromoCodeExistErrorSchema, AddPromoCodeSchema, PatchPromoCodeSchema,
                                                 PromoCodeUsedErrorSchema)
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, Path
from app_api.db.redis_connection import get_redis

promo = APIRouter(prefix="/promo", tags=["Promo Codes"])


@promo.get(path="/{code}",
           response_model=PromoCodeSchema,
           summary="Получение информации о промокоде",
           responses={404: {"model": PromoCodeNotFoundErrorSchema, "description": "Promo code not found"}}
           )
def promo_route(code: str = Path(description="Промо код", example="SKILL-HELPER"),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Получает информацию о промокоде.


    ### Параметры
    - `promo_code` (str): Промо код.

    ### Возвращает
    - `PromoSchema`: Схема данных о промокоде

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если промокод не найден.
    """
    promo_code = get_promo_code(db=db, redis=redis, code=code)
    return promo_code


@promo.get(path="/{code}/user/{telegram_id}",
           response_model=PromoCodeSchema,
           summary="Проверяет, на доступность использования промокода",
           responses={404: {"model": PromoCodeNotFoundErrorSchema, "description": "Promo code not found"},
                      409: {"model": PromoCodeUsedErrorSchema, "description": "Promo code was used"}}
           )
def promo_route(code: str = Path(description="Промо код", example="SKILL-HELPER"),
                telegram_id: int = Path(description="Телеграм ID пользователя", example=123456789),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Получает информацию о промокоде.


    ### Параметры
    - `promo_code` (str): Промо код.
    - `telegram_id` (int): Телеграм ID пользователя

    ### Возвращает
    - `PromoSchema`: Схема данных о промокоде

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если промокод не найден.
    """
    promo_code, _ = check_used_promo_code(db=db, redis=redis, code=code, telegram_id=telegram_id)
    return promo_code


@promo.post(path="/{code}/user/{telegram_id}",
            summary="Делает промокод использованным",
            responses={404: {"model": PromoCodeNotFoundErrorSchema, "description": "Promo code not found"},
                       409: {"model": PromoCodeUsedErrorSchema, "description": "Promo code was used"}}
            )
def promo_route(code: str = Path(description="Промо код", example="SKILL-HELPER"),
                telegram_id: int = Path(description="Телеграм ID пользователя", example=123456789),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Добавляет промокод с пользователем, что бы зафиксировать его использование.


    ### Параметры
    - `promo_code` (str): Промо код.
    - `telegram_id` (int): Телеграм ID пользователя

    ### Возвращает
    - `PromoSchema`: Схема данных о промокоде

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если промокод не найден.
    """
    apply_promo_code(db=db, redis=redis, code=code, telegram_id=telegram_id)
    return Response(status_code=200, description="Generated")


@promo.post(path="/{code}",
            response_model=PromoCodeSchema,
            summary="Добавление промокод в базу",
            responses={409: {"model": PromoCodeExistErrorSchema, "description": "Promo code already exists"}}
            )
def promo_route(promo_info: AddPromoCodeSchema,
                code: str = Path(description="Название промо кода", example="SKILL-HELPER"),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Добавляет промокод в базу.


    ### Параметры
    - `promo_code` (str): Промо код.

    ### Возвращает
    - `PromoSchema`: Схема данных о модели

    ### Исключения
    - `HTTPException` с кодом 409: Вызывается, если промокод с указанным именем уже есть.
    """
    promo_code = add_promo_code(db=db, redis=redis, code=code, promo_info=promo_info)
    return promo_code


@promo.patch(path="/{code}",
             response_model=PromoCodeSchema,
             summary="Обновляет значения промокода в базе",
             responses={404: {"model": PromoCodeNotFoundErrorSchema, "description": "Promo code not found"}}
             )
def promo_route(promo_info: PatchPromoCodeSchema,
                code: str = Path(description="Название промо кода", example="SKILL-HELPER"),
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Обновляет значения промокода в базе

    ### Параметры
    - `promo_code` (str): Промокод

    ### Возвращает
    - `PatchPromoSchema`: Схема данных о промо коде

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    promo_code = patch_promo_code(db=db, redis=redis, code=code, promo_info=promo_info)
    return promo_code
