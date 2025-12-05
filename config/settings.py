# config/settings.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str | None = None
    database_url: str | None = None
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
