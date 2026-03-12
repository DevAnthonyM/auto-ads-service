"""
LLM integration for extracting structured car search filters from natural language.

Primary mode: DeepSeek API (OpenAI-compatible) using ANTHROPIC_API_KEY variable.
Fallback mode: Keyword-based extraction (no API key required).
"""

import json
import re
import httpx
from loguru import logger
from .config import settings


# ---------------------------------------------------------------------------
# Tool / Function schema — defines what filters the LLM can extract
# ---------------------------------------------------------------------------

SEARCH_CARS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_cars",
        "description": "Search for cars in the database based on user-specified filters. Extract all relevant filters from the user's message.",
        "parameters": {
            "type": "object",
            "properties": {
                "make": {
                    "type": "string",
                    "description": "Car manufacturer/brand (e.g. Toyota, BMW, Honda, Nissan, Mercedes)"
                },
                "model": {
                    "type": "string",
                    "description": "Car model name (e.g. Corolla, X5, Civic)"
                },
                "year_min": {
                    "type": "integer",
                    "description": "Minimum manufacturing year (e.g. 2015)"
                },
                "year_max": {
                    "type": "integer",
                    "description": "Maximum manufacturing year (e.g. 2020)"
                },
                "price_min": {
                    "type": "number",
                    "description": "Minimum price in Japanese Yen (e.g. 500000)"
                },
                "price_max": {
                    "type": "number",
                    "description": "Maximum price in Japanese Yen. Convert: '1 million' = 1000000, '2 million' = 2000000, '500k' = 500000"
                },
                "color": {
                    "type": "string",
                    "description": "Car exterior color in English (e.g. Red, Blue, White, Black, Silver, Gray)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5, max: 10)"
                }
            },
            "required": []
        }
    }
}

SYSTEM_PROMPT = """You are a car search assistant for a Japanese used car marketplace.
Your job is to extract structured search filters from the user's natural language query.
ALWAYS call the search_cars function with whatever filters you can extract.
Price conversions: '1 million yen' = 1000000, '2 million' = 2000000, '500k' = 500000, '150万' = 1500000.
If no specific filters are mentioned, call search_cars with an empty object to show all cars.
Extract partial information — if only a color is mentioned, just pass the color."""


async def extract_filters_llm(user_message: str) -> dict:
    """
    Use DeepSeek API (OpenAI-compatible) to extract structured filters.
    Variable name kept as anthropic_api_key per project requirements.
    """
    if not settings.anthropic_api_key or settings.anthropic_api_key == "your-anthropic-api-key":
        raise ValueError("No API key configured")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "tools": [SEARCH_CARS_TOOL],
        "tool_choice": {"type": "function", "function": {"name": "search_cars"}},
        "max_tokens": 500,
        "temperature": 0.1
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.anthropic_api_key}"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

    # Extract tool call arguments from response
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("Empty response from LLM")

    message = choices[0].get("message", {})
    tool_calls = message.get("tool_calls", [])

    if not tool_calls:
        raise ValueError("No tool call in LLM response")

    arguments_str = tool_calls[0]["function"]["arguments"]
    filters = json.loads(arguments_str)

    # Enforce limit cap
    if "limit" not in filters or filters["limit"] > 10:
        filters["limit"] = 5

    logger.info(f"LLM extracted filters: {filters}")
    return filters


def extract_filters_keyword(message: str) -> dict:
    """
    Keyword-based fallback filter extraction.
    Works without any API key. Handles common patterns robustly.
    """
    filters = {}
    msg = message.lower()

    # --- Car makes ---
    make_map = {
        "toyota": "Toyota", "トヨタ": "Toyota",
        "honda": "Honda", "ホンダ": "Honda",
        "nissan": "Nissan", "日産": "Nissan",
        "bmw": "BMW",
        "mercedes": "Mercedes", "benz": "Mercedes",
        "mazda": "Mazda", "マツダ": "Mazda",
        "subaru": "Subaru", "スバル": "Subaru",
        "suzuki": "Suzuki", "スズキ": "Suzuki",
        "lexus": "Lexus", "レクサス": "Lexus",
        "volkswagen": "Volkswagen", "vw": "Volkswagen",
        "audi": "Audi",
        "mitsubishi": "Mitsubishi", "三菱": "Mitsubishi",
        "daihatsu": "Daihatsu", "ダイハツ": "Daihatsu",
        "peugeot": "Peugeot",
        "volvo": "Volvo",
        "ford": "Ford",
        "hyundai": "Hyundai",
    }
    for key, brand in make_map.items():
        if key in msg:
            filters["make"] = brand
            break

    # --- Colors ---
    color_map = {
        "red": "Red", "scarlet": "Red", "crimson": "Red",
        "blue": "Blue", "navy": "Blue",
        "white": "White",
        "black": "Black",
        "silver": "Silver",
        "gray": "Gray", "grey": "Gray",
        "green": "Green",
        "yellow": "Yellow", "gold": "Yellow",
        "orange": "Orange",
        "brown": "Brown", "beige": "Beige",
        "purple": "Purple",
    }
    for key, color in color_map.items():
        if key in msg:
            filters["color"] = color
            break

    # --- Price patterns ---
    # "under X million", "below X million", "less than X million"
    price_upper_patterns = [
        r"(?:under|below|less\s+than|cheaper\s+than|max|within)\s+(\d+(?:\.\d+)?)\s*million",
        r"(?:under|below|less\s+than)\s+(\d+(?:\.\d+)?)\s*(?:yen|jpy|¥)",
        r"(\d+(?:\.\d+)?)\s*million\s+(?:yen|jpy|¥|or\s+less|max)",
        r"(?:up\s+to|max(?:imum)?)\s+(\d+(?:\.\d+)?)\s*m(?:illion)?",
        r"budget\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*m(?:illion)?",
    ]
    for pattern in price_upper_patterns:
        m = re.search(pattern, msg)
        if m:
            filters["price_max"] = float(m.group(1)) * 1_000_000
            break

    # "over X million", "above X million", "more than X million"
    price_lower_patterns = [
        r"(?:over|above|more\s+than|at\s+least)\s+(\d+(?:\.\d+)?)\s*million",
        r"(\d+(?:\.\d+)?)\s*million\s+(?:or\s+more|minimum|min)",
    ]
    for pattern in price_lower_patterns:
        m = re.search(pattern, msg)
        if m:
            filters["price_min"] = float(m.group(1)) * 1_000_000
            break

    # Raw yen amounts: "under 1000000", "under 500000 yen"
    raw_price_pattern = r"(?:under|below|less\s+than)\s+(\d{5,7})(?:\s*(?:yen|jpy|¥))?"
    m = re.search(raw_price_pattern, msg)
    if m and "price_max" not in filters:
        filters["price_max"] = float(m.group(1))

    # --- Year patterns ---
    # "from 2015", "2015 or newer", "after 2015"
    year_min_patterns = [
        r"(?:from|since|after|starting|newer\s+than)\s+(20\d{2}|19\d{2})",
        r"(20\d{2}|19\d{2})\s+(?:or\s+newer|and\s+newer|onwards|up)",
        r"(?:year\s+)?(\d{4})\s+model",
    ]
    for pattern in year_min_patterns:
        m = re.search(pattern, msg)
        if m:
            year = int(m.group(1))
            if 1990 <= year <= 2030:
                filters["year_min"] = year
                break

    # "before 2020", "older than 2020", "up to 2020"
    year_max_patterns = [
        r"(?:before|until|up\s+to|older\s+than)\s+(20\d{2}|19\d{2})",
        r"(20\d{2}|19\d{2})\s+(?:or\s+older|and\s+older)",
    ]
    for pattern in year_max_patterns:
        m = re.search(pattern, msg)
        if m:
            year = int(m.group(1))
            if 1990 <= year <= 2030:
                filters["year_max"] = year
                break

    # Bare 4-digit year: "Toyota 2014" — treat as year_min if no range set
    bare_year = re.search(r'\b(20\d{2}|19\d{2})\b', msg)
    if bare_year and "year_min" not in filters and "year_max" not in filters:
        year = int(bare_year.group(1))
        if 1990 <= year <= 2030:
            filters["year_min"] = year

    filters["limit"] = 5
    logger.info(f"Keyword parser extracted filters: {filters}")
    return filters


async def extract_filters(user_message: str) -> dict:
    """
    Main entry point. Tries LLM first, falls back to keyword parser.
    """
    try:
        filters = await extract_filters_llm(user_message)
        return filters
    except Exception as e:
        logger.error(f"LLM extraction failed: {e} — falling back to keywords")
        return extract_filters_keyword(user_message)