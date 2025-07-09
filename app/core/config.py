from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    BOT_TOKEN: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    DOMAIN: str
    SUBDOMAIN_ENABLED: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
