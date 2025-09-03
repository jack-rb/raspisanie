from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    BOT_TOKEN: str | None = None
    BOT_USERNAME: str | None = None  # @username без @, например: www_test_www_bot
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    DOMAIN: str
    SUBDOMAIN_ENABLED: bool = True
    ALLOW_PUBLIC: bool = False  # Позволять доступ без Telegram InitData (для отладки/демо)

    class Config:
        env_file = ".env"

settings = Settings()
