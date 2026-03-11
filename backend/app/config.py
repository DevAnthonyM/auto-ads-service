"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration class.

    All values are read from environment variables or .env file.
    The application will fail fast on startup if required variables are missing.
    """

    # ── Database ───────────────────────────────────────────
    database_url: str
    postgres_user: str = "postgres"
    postgres_password: str = "changeme"
    postgres_db: str = "auto_ads"

    # ── JWT Authentication ─────────────────────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # ── Default Admin ──────────────────────────────────────
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # ── Scraper ────────────────────────────────────────────
    scrape_interval_minutes: int = 30
    scrape_max_pages: int = 5

    # ── Telegram Bot ───────────────────────────────────────
    telegram_bot_token: str = ""

    # ── LLM (Anthropic) ───────────────────────────────────
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()