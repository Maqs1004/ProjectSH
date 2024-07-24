import redis
from redis import Redis
from typing import Any, Generator

from ..core.config import setting


def get_redis_connection(
        redis_url=setting.REDIS_URL,
        max_connections=20,
        socket_timeout=5,
        socket_connect_timeout=2,
        decode_responses=True,
        retry_on_timeout=True
):
    """
    Создает пул подключений к Redis и возвращает объект Redis, использующий этот пул.

    Args:
        redis_url (str): URL для подключения к серверу Redis, обычно включает в себя учетные данные и порт
        max_connections (int): Максимальное количество подключений, которые могут быть установлены пулом одновременно
        socket_timeout (int): Максимальное время в секундах ожидания ответа от сервера Redis перед тем,
         как операция будет считаться просроченной
        socket_connect_timeout (int): Максимальное время в секундах для установки соединения с сервером Redis
        decode_responses (bool): Если True, ответы от сервера будут декодированы в строки, иначе они будут возвращены
         как байты
        retry_on_timeout (bool): Если True, операция будет повторно выполнена в случае возникновения тайм-аута

    Returns:
        Redis: Объект клиента Redis, подключенный к базе данных с использованием созданного пула подключений.
    """
    pool = redis.ConnectionPool.from_url(
        url=redis_url,
        max_connections=max_connections,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_connect_timeout,
        decode_responses=decode_responses,
        retry_on_timeout=retry_on_timeout
    )

    return redis.Redis(connection_pool=pool)


def get_redis() -> Generator[Redis, Any, None]:
    """
    Генератор, обеспечивающий контекстное управление подключением к Redis.

    Yields:
        Redis: Объект клиента Redis для использования в контексте with-statement.
    """
    redis_connection = get_redis_connection()
    # redis_connection.flushall()
    # redis_connection.flushdb()
    try:
        yield redis_connection
    finally:
        redis_connection.close()
