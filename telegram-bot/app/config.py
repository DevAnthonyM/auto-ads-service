"""Telegram bot configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot settings — reads from .env or environment variables."""

    database_url: str
    telegram_bot_token: str = ""
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()