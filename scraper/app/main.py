"""Scraper service entry point.

Runs an initial scrape on startup, then schedules periodic scrapes.
Falls back to seed data if carsensor.net is unreachable.
"""

import asyncio
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config import settings
from app.database import async_session
from app.scraper import CarSensorScraper
from app.seed_data import get_seed_data
from app.upsert import upsert_cars

# Configure structured logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)


async def scrape_job() -> None:
    """Execute a single scrape cycle.

    1. Attempt to scrape carsensor.net
    2. If scraping returns data, upsert to database
    3. If scraping fails or returns empty, fall back to seed data
    """
    logger.info("=" * 50)
    logger.info("Starting scrape cycle...")

    scraper = CarSensorScraper()
    cars = []

    try:
        cars = await scraper.scrape_listings(max_pages=settings.scrape_max_pages)
        logger.info(f"Scraper returned {len(cars)} car listings")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")

    # Fall back to seed data if scraping returned no results
    if not cars:
        logger.warning(
            "No cars scraped from carsensor.net — using seed data fallback. "
            "This is expected if the site is geo-restricted or rate-limited."
        )
        cars = get_seed_data()
        logger.info(f"Loaded {len(cars)} cars from seed data")

    # Upsert to database
    async with async_session() as session:
        stats = await upsert_cars(session, cars)
        logger.info(f"Upsert stats: {stats}")

    logger.info("Scrape cycle complete")
    logger.info("=" * 50)


async def main() -> None:
    """Main entry point — runs initial scrape and starts scheduler."""
    logger.info("Auto-Ads Scraper Service starting...")
    logger.info(f"Scrape interval: {settings.scrape_interval_minutes} minutes")
    logger.info(f"Max pages per brand: {settings.scrape_max_pages}")

    # Wait briefly for database to be ready
    await asyncio.sleep(3)

    # Run initial scrape immediately
    await scrape_job()

    # Schedule periodic scrapes
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scrape_job,
        "interval",
        minutes=settings.scrape_interval_minutes,
        id="scrape_carsensor",
        name="Scrape carsensor.net listings",
    )
    scheduler.start()
    logger.info(f"Scheduler started — next scrape in {settings.scrape_interval_minutes} minutes")

    # Keep the service alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scraper service shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())