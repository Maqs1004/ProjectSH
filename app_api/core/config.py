from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    SEAWEEDFS_MASTER_URL: str
    SEAWEEDFS_VOLUME_URL: str


setting = Settings()
