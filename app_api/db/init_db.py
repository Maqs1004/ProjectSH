from .base import Base
from .session import engine
from ..core.logging_config import logger
from sqlalchemy_utils import database_exists, create_database


def init_db() -> None:
    """
    Инициализирует базу данных, проверяя существование и создавая её при необходимости,
    а затем создаёт все необходимые таблицы на основе метаданных модели.
    Функция сначала проверяет, существует ли база данных по указанному URL.
    Если база данных не существует, она будет создана, и в журнал будет записано соответствующее сообщение.
    Если база данных уже существует, в журнал также будет записано сообщение о её наличии.
    Независимо от наличия базы данных, функция производит создание всех таблиц,
    описанных в метаданных Base, если они ещё не были созданы.
    """
    if not database_exists(engine.url):
        logger.info("Database does not exist and will be created.")
        create_database(engine.url)
    else:
        logger.info("Database exists.")
    Base.metadata.create_all(bind=engine)
