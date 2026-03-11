"""Seed script — creates the default admin user if not already present.

This script is idempotent: running it multiple times is safe.
It is executed automatically by the backend entrypoint after migrations.
"""

import asyncio
import sys

from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_admin() -> None:
    """Create the default admin user if it does not exist."""
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.username == settings.admin_username)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info(f"Admin user '{settings.admin_username}' already exists — skipping seed.")
            await engine.dispose()
            return

        # Create admin user with bcrypt-hashed password
        admin = User(
            username=settings.admin_username,
            password_hash=pwd_context.hash(settings.admin_password),
            is_admin=True,
        )
        session.add(admin)
        await session.commit()
        logger.success(f"Admin user '{settings.admin_username}' created successfully.")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(seed_admin())
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        sys.exit(1)