"""
Database query layer for the Telegram bot.
Handles smart searching even when make field is 'Unknown' by also searching model text.
"""

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from .config import settings

# ---------------------------------------------------------------------------
# Database session setup (bot connects directly to same DB as backend)
# ---------------------------------------------------------------------------

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Lazy model import to avoid circular imports
# ---------------------------------------------------------------------------

def get_car_model():
    """Import Car model lazily."""
    from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class Car(Base):
        __tablename__ = "cars"
        id = Column(Integer, primary_key=True)
        external_id = Column(String, unique=True)
        make = Column(String)
        model = Column(String)
        year = Column(Integer)
        price = Column(Float)
        color = Column(String)
        link = Column(Text)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime)
        updated_at = Column(DateTime)

    return Car


async def search_cars(filters: dict) -> list[dict]:
    """
    Search cars in the database using extracted filters.
    
    Smart matching strategy:
    - If make filter is specified, search BOTH make AND model columns (ilike)
      because some records have make='Unknown' with brand name in model text.
    - All text filters use case-insensitive ILIKE for flexibility.
    - Results ordered by price ascending (cheapest first).
    """
    try:
        # Use raw SQLAlchemy text queries for reliability
        from sqlalchemy import text

        conditions = ["is_active = true"]
        params = {}

        make = filters.get("make")
        if make:
            # Search in BOTH make and model columns to handle 'Unknown' make records
            conditions.append(
                "(make ILIKE :make_pattern OR model ILIKE :make_pattern)"
            )
            params["make_pattern"] = f"%{make}%"

        model_filter = filters.get("model")
        if model_filter:
            conditions.append("model ILIKE :model_pattern")
            params["model_pattern"] = f"%{model_filter}%"

        if filters.get("year_min"):
            conditions.append("year >= :year_min")
            params["year_min"] = filters["year_min"]

        if filters.get("year_max"):
            conditions.append("year <= :year_max")
            params["year_max"] = filters["year_max"]

        if filters.get("price_min"):
            conditions.append("price >= :price_min")
            params["price_min"] = filters["price_min"]

        if filters.get("price_max"):
            conditions.append("price <= :price_max")
            params["price_max"] = filters["price_max"]

        color = filters.get("color")
        if color:
            conditions.append("color ILIKE :color_pattern")
            params["color_pattern"] = f"%{color}%"

        limit = min(int(filters.get("limit", 5)), 10)

        where_clause = " AND ".join(conditions)
        query = text(
            f"SELECT id, make, model, year, price, color, link "
            f"FROM cars "
            f"WHERE {where_clause} "
            f"ORDER BY price ASC NULLS LAST "
            f"LIMIT :limit"
        )
        params["limit"] = limit

        async with AsyncSessionLocal() as session:
            result = await session.execute(query, params)
            rows = result.fetchall()

        cars = []
        for row in rows:
            cars.append({
                "id": row[0],
                "make": row[1],
                "model": row[2],
                "year": row[3],
                "price": row[4],
                "color": row[5],
                "link": row[6],
            })

        logger.info(f"Database query returned {len(cars)} results")
        return cars

    except Exception as e:
        logger.error(f"Database search error: {e}")
        return []