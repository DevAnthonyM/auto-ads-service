"""Database upsert operations for scraped car data.

Uses PostgreSQL's INSERT ... ON CONFLICT for atomic upserts.
Batch processes all cars in a single transaction for efficiency.
"""

from loguru import logger
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Car


async def upsert_cars(session: AsyncSession, cars: list[dict]) -> dict:
    """Upsert a batch of car listings into the database.

    - New cars are inserted
    - Existing cars (matched by external_id) are updated
    - Returns stats: {inserted: N, updated: N, errors: N}

    Uses PostgreSQL dialect-specific INSERT ... ON CONFLICT DO UPDATE
    for atomic, concurrent-safe operations.
    """
    if not cars:
        logger.warning("No cars to upsert")
        return {"inserted": 0, "updated": 0, "errors": 0}

    stats = {"inserted": 0, "updated": 0, "errors": 0}

    try:
        # Build the upsert statement
        stmt = insert(Car).values([
            {
                "external_id": car["external_id"],
                "make": car["make"],
                "model": car["model"],
                "year": car["year"],
                "price": car["price"],
                "color": car.get("color"),
                "link": car["link"],
                "raw_data": car.get("raw_data"),
                "is_active": True,
            }
            for car in cars
        ])

        # ON CONFLICT: update price, color, raw_data, and timestamps
        stmt = stmt.on_conflict_do_update(
            index_elements=["external_id"],
            set_={
                "price": stmt.excluded.price,
                "color": stmt.excluded.color,
                "raw_data": stmt.excluded.raw_data,
                "updated_at": func.now(),
                "is_active": True,
            },
        )

        result = await session.execute(stmt)
        await session.commit()

        # rowcount reflects total affected rows (both inserts and updates)
        total_affected = result.rowcount if result.rowcount else len(cars)
        stats["inserted"] = total_affected

        logger.success(f"Upserted {total_affected} cars successfully")

    except Exception as e:
        await session.rollback()
        logger.error(f"Upsert failed: {e}")
        stats["errors"] = len(cars)
        raise

    return stats