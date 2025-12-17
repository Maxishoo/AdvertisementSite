from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str

    API_V1_STR: ClassVar[str] = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
