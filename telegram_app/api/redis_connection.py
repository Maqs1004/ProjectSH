import json
import redis
from typing import Type
from telebot import logger
from pydantic import BaseModel
from core.config import setting


class RedisClient:
    """
     Клиент для работы с Redis, включающий методы для получения, установки, удаления и очистки кэша.
     """
    def __init__(self):
        self.__client = redis.StrictRedis(
            host=setting.REDIS_HOST, port=setting.REDIS_PORT, db=setting.REDIS_DB, password=setting.REDIS_PASSWORD,
            username="default"
        )

    def get(self, base_model: Type[BaseModel], cache_key: str):
        """
        Получает данные из кэша по заданному ключу и валидирует их с использованием указанной модели.

        Args:
            base_model (Type[BaseModel]): Модель для валидации данных
            cache_key (str): Ключ для получения данных из кэша

        Returns:
            BaseModel | None: Экземпляр модели с валидированными данными, если данные найдены, иначе None.
        """
        record: str | None = self.__client.get(cache_key)
        if record is not None:
            cache = base_model.model_validate_json(record)
            logger.info(f"Found records in cache by key {cache_key} ")
            return cache

    def set(self, cache_key: str, cached: dict, ex: int | None = None):
        """
        Устанавливает данные в кэш с заданным ключом и временем жизни.

        Args:
            cache_key (str): Ключ для установки данных в кэш
            cached (dict): Данные для кэширования
            ex (int | None): Время жизни кэша в секундах (по умолчанию None)

        """
        logger.info(f"Set cache by key {cache_key}  with ex={ex}")
        self.__client.set(cache_key, json.dumps(cached), ex=ex)

    def clear(self):
        """
          Очищает весь кэш, удаляя все ключи и базы данных.
        """
        self.__client.flushall()
        self.__client.flushdb()

    def delete_keys_by_pattern(self, pattern: str, cursor="0"):
        """
        Удаляет ключи из кэша, соответствующие заданному шаблону.

        Args:
            pattern (str): Шаблон для поиска ключей
            cursor (str): Начальная позиция курсора для итерации по ключам
        """
        with self.__client as redis_connection:
            keys_to_delete = []
            while cursor != 0:
                cursor, keys = redis_connection.scan(
                    cursor=cursor, match=pattern, count=100
                )
                keys_to_delete.extend(keys)
            if keys_to_delete:
                redis_connection.delete(*keys_to_delete)
                logger.info(f"Deleted {len(keys_to_delete)} keys by pattern {pattern}")
