"""
Telegram bot message handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .llm import extract_filters
from .db import search_cars


# ---------------------------------------------------------------------------
# Helper: format price in human-readable form
# ---------------------------------------------------------------------------

def format_price(price) -> str:
    if price is None:
        return "Price on request"
    p = int(price)
    if p >= 1_000_000:
        return f"¥{p / 1_000_000:.1f}M ({p:,})"
    elif p >= 10_000:
        return f"¥{p:,}"
    else:
        return f"¥{p}"


def format_filters_summary(filters: dict) -> str:
    """Build a human-readable summary of applied filters."""
    parts = []
    if filters.get("make"):
        parts.append(f"Brand: <b>{filters['make']}</b>")
    if filters.get("model"):
        parts.append(f"Model: <b>{filters['model']}</b>")
    if filters.get("color"):
        parts.append(f"Color: <b>{filters['color']}</b>")
    if filters.get("year_min") and filters.get("year_max"):
        parts.append(f"Year: <b>{filters['year_min']}–{filters['year_max']}</b>")
    elif filters.get("year_min"):
        parts.append(f"Year: <b>{filters['year_min']}+</b>")
    elif filters.get("year_max"):
        parts.append(f"Year: <b>up to {filters['year_max']}</b>")
    if filters.get("price_max"):
        parts.append(f"Max price: <b>{format_price(filters['price_max'])}</b>")
    if filters.get("price_min"):
        parts.append(f"Min price: <b>{format_price(filters['price_min'])}</b>")
    return " | ".join(parts) if parts else "No filters — showing all cars"


def format_car_card(car: dict, index: int) -> str:
    """Format a single car result as a Telegram HTML message block."""
    make = car.get("make", "")
    model = car.get("model", "")

    # If make is Unknown, try to extract a readable title from model
    if not make or make.lower() == "unknown":
        title = model[:50] + ("..." if len(model) > 50 else "")
    else:
        title = f"{make} {model}"
        if len(title) > 60:
            title = title[:57] + "..."

    year = car.get("year") or "N/A"
    price = format_price(car.get("price"))
    color = car.get("color") or "N/A"
    link = car.get("link", "")

    color_emoji = {
        "red": "🔴", "blue": "🔵", "black": "⚫", "white": "⚪",
        "silver": "🔘", "gray": "🩶", "grey": "🩶", "green": "🟢",
        "yellow": "🟡", "gold": "🟡", "orange": "🟠",
    }.get((color or "").lower(), "🎨")

    card = (
        f"<b>{index}. {title}</b>\n"
        f"   📅 Year: {year}\n"
        f"   💴 Price: {price}\n"
        f"   {color_emoji} Color: {color}\n"
    )
    if link:
        card += f'   🔗 <a href="{link}">View on CarSensor</a>\n'

    return card


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

WELCOME_MESSAGE = """🚗 <b>Welcome to Auto Ads Bot!</b>

I search Japanese used cars from CarSensor.net.
Just describe what you're looking for in plain English!

<b>Example queries:</b>
• <i>Find a red BMW under 2 million</i>
• <i>Show me Toyota cars from 2015</i>
• <i>Honda cars under 1 million yen</i>
• <i>White Nissan newer than 2018</i>
• <i>Show me all cars</i>

<b>Commands:</b>
/start — Show this message
/help — Show this message
/latest — Show the 5 most recently added cars
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="HTML")


async def latest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the 5 most recently added cars."""
    await update.message.reply_text("⏳ Fetching latest listings...")

    from sqlalchemy import text
    from .db import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT make, model, year, price, color, link FROM cars WHERE is_active=true ORDER BY created_at DESC LIMIT 5")
            )
            rows = result.fetchall()

        if not rows:
            await update.message.reply_text("No cars in database yet. The scraper may still be running.")
            return

        response = "🆕 <b>5 Latest Listings:</b>\n\n"
        for i, row in enumerate(rows, 1):
            car = {"make": row[0], "model": row[1], "year": row[2], "price": row[3], "color": row[4], "link": row[5]}
            response += format_car_card(car, i) + "\n"

        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Latest handler error: {e}")
        await update.message.reply_text("❌ Error fetching cars. Please try again.")


# ---------------------------------------------------------------------------
# Main search handler
# ---------------------------------------------------------------------------

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-form natural language car search queries."""
    user_message = update.message.text
    username = update.effective_user.username or update.effective_user.first_name
    logger.info(f"Query from {username}: {user_message}")

    # Send typing indicator
    await update.message.reply_text("🔍 Searching...")

    # Step 1: Extract filters (LLM or keyword fallback)
    filters = await extract_filters(user_message)

    # Step 2: Query database
    cars = await search_cars(filters)

    # Step 3: Build response
    filter_summary = format_filters_summary(filters)

    if not cars:
        no_results = (
            f"😔 <b>No cars found</b>\n"
            f"Filters: {filter_summary}\n\n"
            f"💡 <b>Try:</b>\n"
            f"• Removing the color filter\n"
            f"• Increasing your price limit\n"
            f"• Using a broader year range\n"
            f"• Try: <i>Show me all cars</i>"
        )
        await update.message.reply_text(no_results, parse_mode="HTML")
        return

    # Build results message
    count = len(cars)
    header = f"✅ <b>Found {count} car{'s' if count != 1 else ''}</b>\n"
    header += f"📋 Filters: {filter_summary}\n\n"

    car_cards = ""
    for i, car in enumerate(cars, 1):
        car_cards += format_car_card(car, i) + "\n"

    footer = "\n💬 <i>Ask me anything — e.g. 'Show me blue cars under 1 million'</i>"

    full_message = header + car_cards + footer

    # Telegram max message length is 4096 chars
    if len(full_message) > 4000:
        full_message = full_message[:3980] + "\n\n<i>...results truncated</i>"

    await update.message.reply_text(full_message, parse_mode="HTML", disable_web_page_preview=True)