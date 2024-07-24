import json
from uuid import UUID
from typing import Type
from redis import Redis
from sqlalchemy import select, func
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session, Query
from app_api.core.logging_config import logger


def apply_filter(
        query: Query,
        model,
        column_name: str,
        value,
        operator: str = 'eq'
):
    """
    Применяет фильтр к запросу на основе заданного столбца и оператора.

    Args:
        query (Query): Объект запроса SQLAlchemy, к которому применяется фильтр.
        model (DeclarativeMeta): Класс модели SQLAlchemy, в которой ищется столбец.
        column_name (str): Имя столбца, к которому нужно применить фильтр.
        value (Any): Значение для сравнения в условии фильтра. Может быть списком для операторов 'in' и 'not_in'.
        operator (str, optional): Оператор сравнения, используемый в фильтре. Поддерживаемые значения: 'eq', 'ne',
            'lt', 'gt', 'le', 'ge', 'in', 'not_in', 'like', 'ilike'. По умолчанию 'eq'.

    Returns:
        Query: Объект запроса с примененным фильтром.

    Raises:
        AttributeError: Если указанный столбец не найден в модели.
        ValueError: Если передан неподдерживаемый оператор или значение для операторов 'in' и 'not_in' не является списком.
    """
    column = getattr(model, column_name, None)
    if column is None:
        raise AttributeError(f"Столбец '{column_name}' не найден в модели {model.__name__}.")
    if operator == 'eq':
        condition = column == value
    elif operator == 'ne':
        condition = column != value
    elif operator == 'lt':
        condition = column < value
    elif operator == 'gt':
        condition = column > value
    elif operator == 'le':
        condition = column <= value
    elif operator == 'ge':
        condition = column >= value
    elif operator == 'in':
        if not isinstance(value, list):
            raise ValueError("Для оператора 'in' значение должно быть списком.")
        condition = column.in_(value)
    elif operator == 'not_in':
        if not isinstance(value, list):
            raise ValueError("Для оператора 'not_in' значение должно быть списком.")
        condition = ~column.in_(value)
    elif operator == 'like':
        condition = column.like(value)
    elif operator == 'ilike':
        condition = column.ilike(value)
    else:
        raise ValueError(f"Неподдерживаемый оператор сравнения '{operator}'.")

    query = query.filter(condition)
    return query


def get_record(
        db: Session,
        redis: Redis,
        identifier: str | int | UUID,
        base_model: Type[BaseModel],
        sql_model,
        cache_key: str,
        filters: list,
        only_check: bool,
        ex=None,

):
    """
    Получает запись из кэша или базы данных по заданному идентификатору, используя заданные фильтры.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        identifier (Union[str, int, UUID]): Идентификатор записи.
        base_model (Type[BaseModel]): Тип модели Pydantic для сериализации данных.
        sql_model (Base): Класс модели SQLAlchemy, используемый для запроса.
        cache_key (str): Ключ для кэширования данных в Redis.
        filters (list): Список фильтров, применяемых для поиска записи.
        only_check (bool): Если `True`, в случае отсутствия записи не генерирует исключение, возвращая `None`.
        ex (Optional[int]): Время жизни кэша в секундах (если указано).

    Returns:
        Any | None: Объект, десериализованный из кэша или загруженный из базы данных, или `None`, если `only_check`
         равен `True` и запись не найдена.

    Raises:
        HTTPException: Если `only_check` равен `False` и запись не найдена, возникает исключение с кодом 404 и
         сообщением о том, что запись не найдена.
    """
    cache = Cache(redis=redis, cache_key=f"{cache_key}:{identifier}", base_model=base_model)
    cached = cache.get()
    if cached is not None:
        return cached
    query = select(sql_model)
    for column_name, value, operator in filters:
        query = apply_filter(query, sql_model, column_name, value, operator)
    query = db.scalars(query).first()
    if query is None:
        if only_check:
            return
        raise HTTPException(status_code=404, detail=f"Record `{identifier}` not found")
    cache.set(query=query, ex=ex)
    return query


def get_records(
        db: Session,
        redis: Redis,
        page: int,
        cache_key: str,
        base_model: Type[BaseModel],
        extract_base_model: Type[BaseModel],
        sql_model,
        filters: list,
        page_size: int = 4,
        ex=None
):
    """
    Извлекает страницу записей из кэша или базы данных, применяя заданные фильтры и учитывая пагинацию.

    Args:
        db (Session): Сессия SQLAlchemy для выполнения запросов к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        page (int): Номер страницы результатов.
        cache_key (str): Ключ для кэширования страницы данных в Redis.
        base_model (Type[BaseModel]): Тип модели Pydantic для начальной сериализации данных.
        extract_base_model (Type[BaseModel]): Тип модели Pydantic для окончательной сериализации данных.
        sql_model (Base): Класс модели SQLAlchemy, используемый для построения запроса.
        filters (list): Список фильтров (каждый фильтр - это список из имени столбца, значения и оператора).
        page_size (int, optional): Количество записей на странице. По умолчанию 4.
        ex (Optional[int]): Время жизни кэша в секундах.

    Returns:
        dict: Словарь с данными, включая общее количество записей, текущую страницу, размер
         страницы и список десериализованных данных.
    """
    cache_key = f"{cache_key}:page:{page}:size:{page_size}"
    cache = Cache(redis=redis, cache_key=cache_key, base_model=base_model)
    cached_list = cache.get_list()
    if cached_list is not None:
        return cached_list
    query = select(sql_model).order_by(sql_model.id.desc())
    for column_name, value, operator in filters:
        query = apply_filter(query, sql_model, column_name, value, operator)
    subquery = select(func.count()).select_from(query.subquery()).scalar_subquery()
    query = query.limit(page_size).offset((page - 1) * page_size)
    queries = db.execute(query).scalars().all()
    total_count_query = select(subquery)
    total_records = db.execute(total_count_query).scalar()
    data = [json.loads(extract_base_model.model_validate(query).model_dump_json()) for query in queries]
    cached_data = {"total_records": total_records, "page": page, "page_size": page_size, "data": data}
    cache.set_list(cached_data=cached_data, ex=ex)
    return cached_data


def patch_record(
        db: Session,
        redis: Redis,
        identifier: str | int | UUID,
        base_model: Type[BaseModel],
        patch_schema: BaseModel,
        sql_model,
        cache_key: str,
        filters: list,
        only_check: bool = False,
        ex=None,

):
    """
    Обновляет информацию о ресурсе в базе данных и удаляет соответствующий кэш, чтобы затем обновить его.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        identifier (Union[str, int, UUID]): Идентификатор записи
        patch_schema (Any): Схема, содержащая обновляемые поля.
        base_model (Type[BaseModel]): Тип модели Pydantic, используемой для сериализации данных
        sql_model (Base): Класс модели SQL Alchemy для построения запроса
        cache_key (str): Ключ для хранения записи в кэше
        filters (list): Список фильтров для поиска
        only_check (bool) Флаг указывающий, что в случае отсутствие записи не выводить ошибку
        ex (Optional[int]): Время жизни кэша в секундах

    Returns:
        Any: Десериализованный объект модели из кэша или базы данных.

    Raises:
        HTTPException: Если запись не найдена.
    """
    query = select(sql_model)
    for column_name, value, operator in filters:
        query = apply_filter(query, sql_model, column_name, value, operator)
    query = db.scalars(query).first()
    if query is None:
        if not only_check:
            raise HTTPException(status_code=404, detail=f"Record `{identifier}` not found")
    for field, value in patch_schema.__dict__.items():
        if value is not None:
            setattr(query, field, value)
    db.commit()
    db.refresh(query)
    cache = Cache(redis=redis, cache_key=cache_key, base_model=base_model)
    cache.delete_key()
    cache.set(query=query, ex=ex)
    return query


def add_record(
        db: Session,
        redis: Redis,
        base_model: Type[BaseModel],
        cache_key: str,
        record,
        ex=None
):
    """
    Добавляет запись в базу данных и кэш.

    Args:
        db (Session): Сессия SQL Alchemy для взаимодействия с базой данных
        redis (Redis): Клиент Redis для доступа к кэшу
        base_model (Type[BaseModel]): Тип модели Pydantic, используемой для сериализации данных
        cache_key (str): Ключ для хранения записи в кэше
        record (Base): Экземпляр модели SQL Alchemy, который будет добавлен
        ex (Optional[int]): Время жизни кэша в секундах

    Returns:
        Any: Десериализованный объект модели, добавленный в базу данных и кэш.
    """
    db.add(record)
    db.commit()
    db.refresh(record)
    cache = Cache(redis=redis, cache_key=cache_key, base_model=base_model)
    cache.set(query=record, ex=ex)
    return record


class Cache:
    def __init__(self,
                 redis: Redis,
                 cache_key: str | None = None,
                 base_model: Type[BaseModel] = None
                 ):
        self.redis = redis
        self.cache_key = cache_key
        self.base_model = base_model

    def get(self):
        """
        Получает объект из кэша по текущему ключу.

        Returns:
            Optional[Any]: Десериализованный объект модели, если он найден в кэше, иначе None
        """
        record = self.redis.get(self.cache_key)
        if record is not None:
            logger.info(f"Found record in cache by key {self.cache_key}")
            cache = self.base_model.model_validate_json(record)
            return cache

    def get_list(self):
        """
        Получает список объектов из кэша по текущему ключу.

        Returns:
            List[Any]: Список десериализованных объектов модели, если они найдены в кэше
        """
        records: str | None = self.redis.get(self.cache_key)
        if records is not None:
            cached = self.base_model.model_validate(json.loads(records))
            logger.info(f"Found records in cache by key {self.cache_key} ")
            return cached

    def set(self, query, ex=None):
        """
        Сохраняет сериализованный объект в кэше.

        Args:
            query (Base): Объект модели, который будет стерилизован и сохранен
            ex (Optional[int]): Время жизни кэша в секундах
        """
        cached = self.base_model.model_validate(query).model_dump_json()
        self.redis.set(self.cache_key, cached, ex=ex)
        logger.info(f"Set cache by key {self.cache_key}  with ex={ex}")

    def set_list(self, cached_data, ex=None):
        """
        Сохраняет список данных для записи в кэш.

        Args:
            cached_data (dict): Список записей для сохранения в кэш
            ex (Optional[int]): Время жизни кэша в секундах
        """
        self.redis.set(self.cache_key, json.dumps(cached_data), ex=ex)
        logger.info(f"Set cache by key {self.cache_key} with ex={ex}")

    def delete_key(self):
        """
        Удаляет запись из кэша по текущему ключу.
        """
        record = self.redis.delete(self.cache_key)
        logger.info(f"Delete {record} record in cache by key {self.cache_key}")

    def delete_keys_by_pattern(self, pattern: str, cursor="0"):
        """
        Удаляет ключи из кэша, соответствующие заданному шаблону.

        Args:
            pattern (str): Шаблон для поиска ключей
            cursor (str): Начальная позиция курсора для итерации по ключам
        """
        with self.redis as redis_connection:
            keys_to_delete = []
            while cursor != 0:
                cursor, keys = redis_connection.scan(cursor=cursor, match=pattern, count=100)
                keys_to_delete.extend(keys)
            if keys_to_delete:
                redis_connection.delete(*keys_to_delete)
                logger.info(f"Deleted {len(keys_to_delete)} keys by pattern {pattern}")
