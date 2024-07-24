from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    API_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str
    SEAWEEDFS_VOLUME_URL: str
    AMOUNT: int
    DISCOUNT: int
    CURRENCY: str
    AMOUNT_STARS: int
    DISCOUNT_STARS: int
    CURRENCY_STARS: str = ""
    PROVIDER_TOKEN: str


setting = Settings()
