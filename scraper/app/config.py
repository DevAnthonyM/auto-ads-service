"""Scraper configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Scraper settings — reads from .env or environment variables."""

    database_url: str
    scrape_interval_minutes: int = 30
    scrape_max_pages: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()