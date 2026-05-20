from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "fitlife-service"
    service_port: int = 8500
    environment: str = "dev"

    postgres_dsn: str = "postgresql+psycopg://fitlife:fitlife@postgres:5432/fitlife"
    mongodb_uri: str = "mongodb://mongodb:27017"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = "fitlife-dev-secret"

    program_load_target_seconds: float = 2.0
    calorie_accuracy_tolerance_pct: float = 10.0
    max_supported_users: int = 1_000_000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
