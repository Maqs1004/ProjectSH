from fastapi import HTTPException
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session
from app_api.models.interaction import PromoCode, UserPromoCode
from app_api.api.dependencies import get_record, add_record, patch_record
from .schemas import PromoCodeSchema, AddPromoCodeSchema, PatchPromoCodeSchema
from app_api.api.endpoints.users.crud import get_user


def get_promo_code(
        db: Session,
        redis: Redis,
        code: str,
        only_check=False,
) -> PromoCodeSchema | None | PromoCode:
    """
    Извлекает запись о промокоде из кэша или базы данных.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        code (str): Название промокода
        only_check (bool): Флаг, указывающий что при отсутствии записи не выводить ошибку

    Returns:
        Union[PromptsSchema, None, Prompts]: Объект промпта, если она найдена; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=PromoCode,
        base_model=PromoCodeSchema,
        identifier=code,
        only_check=only_check,
        cache_key="promo_code:code",
        filters=[["code", code, "eq"]],
    )

    return query


def add_promo_code(
        db: Session,
        redis: Redis,
        code: str,
        promo_info: AddPromoCodeSchema
) -> PromoCodeSchema | None | PromoCode:
    """
    Добавляет промпт в базу данных и кэш.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для взаимодействия с кэшем
        code (str): Код
        promo_info (AddPromptsSchema): Схема для добавления промокода, содержащая необходимую информацию

    Returns:
        UsersSchema: Объект схемы пользователя после его добавления в базу данных и кэш.
    """
    promo_code = PromoCode(
        code=code,
        discount_type=promo_info.discount_type,
        discount_value=promo_info.discount_value,
        expiry_date=promo_info.expiry_date,
        course_content_volume=promo_info.course_content_volume
    )

    record = add_record(
        db=db,
        redis=redis,
        record=promo_code,
        base_model=PromoCodeSchema,
        cache_key=f"promo_code:code:{code}"
    )
    return record


def patch_promo_code(
        code: str,
        db: Session,
        redis: Redis,
        promo_info: PatchPromoCodeSchema
) -> PromoCodeSchema | None | PromoCode:
    """
    Обновляет информацию промокода в базе данных и удаляет соответствующий кэш, чтобы затем обновить его.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных.
        redis (Redis): Клиент Redis для взаимодействия с кэшем.
        code (str): Промо код
        promo_info (PatchPromoCodeSchema): Схема, содержащая обновляемые поля промокода.

    Returns:
        PromoCodeSchema: Объект промокода после обновления.

    Raises:
        HTTPException: Если промокод не найден, возвращает HTTP статус 404.
    """
    promo_code = patch_record(
        db=db,
        redis=redis,
        identifier=code,
        sql_model=PromoCode,
        filters=[["code", code, "eq"]],
        base_model=PromoCodeSchema,
        patch_schema=promo_info,
        cache_key=f"promo_code:code:{code}",
    )
    return promo_code


def check_used_promo_code(
        code: str,
        db: Session,
        redis: Redis,
        telegram_id: int
):
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id,
    )
    promo_code = get_promo_code(
        db=db,
        redis=redis,
        code=code
    )
    query = select(UserPromoCode).filter_by(user_id=user.id, promo_code_id=promo_code.id)
    user_promo_code = db.scalars(query).first()
    if user_promo_code:
        raise HTTPException(status_code=409, detail=f"Promo code was used")
    return promo_code, user


def apply_promo_code(
        code: str,
        db: Session,
        redis: Redis,
        telegram_id: int
):
    promo_code, user = check_used_promo_code(code=code, db=db, redis=redis, telegram_id=telegram_id)
    record = UserPromoCode(
        user_id=user.id,
        promo_code_id=promo_code.id,
    )
    db.add(record)
    db.commit()


