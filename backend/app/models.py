"""SQLAlchemy ORM models — Users and Cars tables."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """Application user — supports admin authentication via JWT."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, is_admin={self.is_admin})>"


class Car(Base):
    """Scraped car advertisement from carsensor.net.

    Uses external_id (derived from listing URL) as the unique key for upsert logic.
    The composite search index supports the Telegram bot's LLM-generated filter queries.
    """

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
        comment="Unique identifier derived from carsensor.net listing URL"
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    price: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, index=True,
        comment="Price in JPY (Japanese Yen)"
    )
    color: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    link: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Additional scraped fields stored for future use"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
        comment="Soft-delete flag — False when listing is no longer found"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Composite index for efficient LLM filter queries
    __table_args__ = (
        Index("ix_cars_search", "make", "model", "year", "price", "color"),
    )

    def __repr__(self) -> str:
        return f"<Car(id={self.id}, make={self.make}, model={self.model}, year={self.year})>"