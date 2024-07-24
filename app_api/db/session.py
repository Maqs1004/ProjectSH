from typing import Generator, Any
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from ..core.config import setting


def create_local_engine(
        echo=True,
        pool_size=20,
        max_overflow=15,
        pool_recycle=300,
        pool_pre_ping=True,
        pool_use_lifo=True,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
) -> Engine:
    """
    Создаёт и возвращает объект движка базы данных с заданными параметрами подключения.

    Args:
      echo (bool): Включает или выключает логирование для всех операций с базой данных. По умолчанию True
      pool_size (int): Максимальное количество постоянных соединений, которые могут быть открыты в пуле. По умолчанию 20
      max_overflow (int): Максимальное количество временных соединений, которые могут быть открыты сверх pool_size,
       если пул исчерпан. По умолчанию 15
      pool_recycle (int): Количество секунд, после которых соединения в пуле будут переподключены, чтобы избежать
       устаревания соединения. По умолчанию 300
      pool_pre_ping (bool): Если True, пул будет использовать pre-ping для проверки соединений перед их использованием,
       чтобы избежать ошибок из-за устаревания соединений. По умолчанию True
      pool_use_lifo (bool): Если True, пул соединений будет использовать стратегию "последний пришел — первый вышел"
       (LIFO) для управления соединениями. По умолчанию True
      keepalives (int): Включает использование TCP keepalive для поддержания активных соединений с сервером, чтобы
       предотвратить их неожиданное закрытие. По умолчанию 1
      keepalives_idle (int): Время в секундах, после которого начинаются keepalive-пробы, если не было активности по
       соединению. По умолчанию 30
      keepalives_interval (int): Интервал в секундах между keepalive-пробами. По умолчанию 10.
      keepalives_count (int): Количество неотвеченных keepalive-проб, после которого соединение считается потерянным.
       По умолчанию 5

    Returns:
      Engine: Объект движка базы данных, настроенный с указанными параметрами.
    """
    return create_engine(
        setting.DATABASE_URL,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        pool_use_lifo=pool_use_lifo,
        connect_args={
            "keepalives": keepalives,
            "keepalives_idle": keepalives_idle,
            "keepalives_interval": keepalives_interval,
            "keepalives_count": keepalives_count,
        }
    )


engine = create_local_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, Any, None]:
    """
    Генератор, создающий и управляющий сессией базы данных.

    Использует контекстный менеджер для гарантии закрытия сессии после использования.
    При вызове функции создаётся новая сессия, которая предоставляется для использования,
    а по завершении работы с ней сессия автоматически закрывается.

    Yields:
      Session: Активная сессия базы данных для выполнения операций.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
