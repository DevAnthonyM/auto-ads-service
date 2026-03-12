"""
CarSensor.net scraper — fetches used car listings from carsensor.net.
Uses Playwright for JS-rendered pages, falls back to httpx + BeautifulSoup.
"""

import asyncio
import re
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ---------------------------------------------------------------------------
# Brand mapping — Japanese brand codes and name fragments to English names
# ---------------------------------------------------------------------------

# carsensor.net URL brand codes → English brand names
BRAND_CODE_MAP = {
    "bTO": "Toyota",
    "bHO": "Honda",
    "bNI": "Nissan",
    "bMA": "Mazda",
    "bSU": "Subaru",
    "bMI": "Mitsubishi",
    "bDA": "Daihatsu",
    "bSZ": "Suzuki",
    "bIS": "Isuzu",
    "bHI": "Hino",
    "bLE": "Lexus",
    "bBM": "BMW",
    "bMB": "Mercedes",
    "bAU": "Audi",
    "bVW": "Volkswagen",
    "bPG": "Peugeot",
    "bMN": "MINI",
    "bVO": "Volvo",
    "bFO": "Ford",
    "bJA": "Jaguar",
    "bLR": "Land Rover",
    "bPO": "Porsche",
    "bFR": "Ferrari",
    "bLM": "Lamborghini",
    "bBC": "Bentley",
    "bRR": "Rolls-Royce",
    "bHY": "Hyundai",
    "bKI": "Kia",
}

# Japanese text fragments → English brand names (for model field fallback)
JAPANESE_BRAND_FRAGMENTS = {
    "トヨタ": "Toyota", "toyota": "Toyota",
    "ホンダ": "Honda", "honda": "Honda",
    "日産": "Nissan", "nissan": "Nissan",
    "マツダ": "Mazda", "mazda": "Mazda",
    "スバル": "Subaru", "subaru": "Subaru",
    "三菱": "Mitsubishi", "mitsubishi": "Mitsubishi",
    "ダイハツ": "Daihatsu", "daihatsu": "Daihatsu",
    "スズキ": "Suzuki", "suzuki": "Suzuki",
    "レクサス": "Lexus", "lexus": "Lexus",
    "BMW": "BMW", "bmw": "BMW",
    "メルセデス": "Mercedes", "mercedes": "Mercedes",
    "アウディ": "Audi", "audi": "Audi",
    "フォルクスワーゲン": "Volkswagen", "volkswagen": "Volkswagen",
    "プジョー": "Peugeot", "peugeot": "Peugeot",
    "ミニ": "MINI", "mini": "MINI",
    "ボルボ": "Volvo", "volvo": "Volvo",
    "フォード": "Ford", "ford": "Ford",
}

# Target URLs — (brand_code, brand_name) pairs to scrape
SCRAPE_TARGETS = [
    ("bTO", "Toyota"),
    ("bHO", "Honda"),
    ("bNI", "Nissan"),
    ("bMA", "Mazda"),
    ("bSU", "Subaru"),
    ("bMI", "Mitsubishi"),
    ("bDA", "Daihatsu"),
    ("bSZ", "Suzuki"),
    ("bLE", "Lexus"),
    ("bBM", "BMW"),
    ("bMB", "Mercedes"),
]

# Color mapping (Japanese → English)
COLOR_MAP = {
    "ホワイト": "White", "白": "White",
    "ブラック": "Black", "黒": "Black",
    "シルバー": "Silver", "銀": "Silver",
    "レッド": "Red", "赤": "Red",
    "ブルー": "Blue", "青": "Blue",
    "グレー": "Gray", "グレイ": "Gray", "灰": "Gray",
    "グリーン": "Green", "緑": "Green",
    "イエロー": "Yellow", "黄": "Yellow",
    "オレンジ": "Orange",
    "ブラウン": "Brown", "茶": "Brown",
    "ベージュ": "Beige",
    "パープル": "Purple", "紫": "Purple",
    "ゴールド": "Gold",
    "ピンク": "Pink",
    "white": "White", "black": "Black", "silver": "Silver",
    "red": "Red", "blue": "Blue", "gray": "Gray", "grey": "Gray",
    "green": "Green", "yellow": "Yellow", "orange": "Orange",
}


def normalize_color(raw: str) -> str:
    if not raw:
        return ""
    raw_clean = raw.strip()
    # Direct lookup
    if raw_clean in COLOR_MAP:
        return COLOR_MAP[raw_clean]
    # Partial match
    for jp, en in COLOR_MAP.items():
        if jp in raw_clean:
            return en
    return raw_clean


def normalize_price(raw: str) -> Optional[float]:
    """Convert Japanese price formats to numeric yen value."""
    if not raw:
        return None
    raw = raw.strip().replace(",", "").replace(" ", "")
    # "150万円" or "150万" → 1,500,000
    m = re.search(r"([\d.]+)万", raw)
    if m:
        return float(m.group(1)) * 10_000
    # Raw numeric
    m = re.search(r"([\d,]+)", raw.replace(",", ""))
    if m:
        val = float(m.group(1))
        # If value looks like it's already in full yen (> 10000), keep it
        # If it looks like man-en (< 5000 but nonzero), multiply by 10000
        if 0 < val < 5000:
            return val * 10_000
        return val
    return None


def extract_external_id(link: str) -> Optional[str]:
    """Extract unique listing ID from carsensor.net URL."""
    m = re.search(r"/detail/([A-Z]{2}\d+)/", link)
    if m:
        return m.group(1)
    # Fallback: use last URL segment
    parts = link.rstrip("/").split("/")
    return parts[-2] if len(parts) >= 2 else None


def detect_brand_from_url(url: str) -> Optional[str]:
    """Detect brand from the URL brand code (most reliable method)."""
    for code, brand in BRAND_CODE_MAP.items():
        if f"/{code}/" in url:
            return brand
    return None


def detect_brand_from_text(text: str) -> Optional[str]:
    """Detect brand name from any text string (model name, title, etc.)."""
    if not text:
        return None
    for fragment, brand in JAPANESE_BRAND_FRAGMENTS.items():
        if fragment in text:
            return brand
    return None


class CarSensorScraper:
    """
    Scraper for carsensor.net used car listings.
    Uses Playwright for JS-rendered pages, falls back to httpx.
    """

    BASE_URL = "https://www.carsensor.net/usedcar"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    KNOWN_SELECTORS = [
        "div.cassetteWrap",
        "div.carsensorCassetteWrap",
        "div[class*='cassette']",
        "li.cassetteItem",
        "div.searchResult li",
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=self.HEADERS,
            follow_redirects=True,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout)),
        reraise=True,
    )
    async def fetch_with_httpx(self, url: str) -> str:
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text

    async def fetch_page(self, url: str) -> str:
        """Fetch page HTML — tries Playwright first, falls back to httpx."""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_extra_http_headers(self.HEADERS)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            logger.warning(f"Playwright failed ({e}), falling back to httpx")
            return await self.fetch_with_httpx(url)

    def parse_listings(self, html: str, brand_name: str = None, page_url: str = None) -> list[dict]:
        """
        Parse car listings from HTML.
        brand_name is passed in from the URL so make is always correctly set.
        """
        soup = BeautifulSoup(html, "lxml")
        cars = []

        # Find listing containers
        container = None
        for selector in self.KNOWN_SELECTORS:
            items = soup.select(selector)
            if items:
                container = items
                logger.info(f"Found {len(items)} listings using selector: {selector}")
                break

        if not container:
            logger.warning("No listings found with known selectors, trying link-based extraction")
            return self._extract_from_links(soup, brand_name)

        for item in container:
            try:
                car = self._parse_single_listing(item, brand_name, page_url)
                if car and car.get("external_id"):
                    cars.append(car)
            except Exception as e:
                logger.debug(f"Error parsing listing: {e}")
                continue

        return cars

    def _parse_single_listing(self, item, brand_name: str = None, page_url: str = None) -> Optional[dict]:
        """Parse a single car listing element."""
        # --- Link and external ID ---
        link_el = item.select_one("a[href*='/usedcar/detail/']")
        if not link_el:
            link_el = item.select_one("a[href*='carsensor.net']")
        if not link_el:
            return None

        href = link_el.get("href", "")
        if not href.startswith("http"):
            href = "https://www.carsensor.net" + href

        external_id = extract_external_id(href)
        if not external_id:
            return None

        # --- Make (brand) — use URL-derived brand_name as primary source ---
        make = brand_name  # This is always correct since we pass it from the URL

        # --- Model name ---
        model = ""
        model_selectors = [
            ".cassetteModelName", ".modelName", ".carName",
            "h2", "h3", ".title", ".name",
            "[class*='model']", "[class*='name']",
        ]
        for sel in model_selectors:
            el = item.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 2:
                    model = text
                    break

        if not model:
            # Fallback: get all text and clean it up
            full_text = item.get_text(separator=" ", strip=True)
            lines = [l.strip() for l in full_text.split() if len(l.strip()) > 3]
            model = " ".join(lines[:5]) if lines else "Unknown Model"

        # If make still not resolved, try detecting from model text
        if not make:
            make = detect_brand_from_text(model) or "Unknown"

        # --- Price ---
        price = None
        price_selectors = [
            ".price", ".totalPrice", "[class*='price']",
            "span.price", "div.price", ".carPrice",
        ]
        for sel in price_selectors:
            el = item.select_one(sel)
            if el:
                raw_price = el.get_text(strip=True)
                price = normalize_price(raw_price)
                if price:
                    break

        # Fallback: search for price pattern in full text
        if not price:
            full_text = item.get_text()
            price = normalize_price(full_text)

        # --- Year ---
        year = None
        full_text = item.get_text()
        # Common patterns: "2020年", "2020年式", "令和2年"
        year_match = re.search(r"(20\d{2}|19[89]\d)年", full_text)
        if year_match:
            year = int(year_match.group(1))
        else:
            # Reiwa era: 令和N年 (2019 + N)
            reiwa = re.search(r"令和(\d+)年", full_text)
            if reiwa:
                year = 2018 + int(reiwa.group(1))
            else:
                # Heisei era: 平成N年 (1988 + N)
                heisei = re.search(r"平成(\d+)年", full_text)
                if heisei:
                    year = 1988 + int(heisei.group(1))

        # --- Color ---
        color = ""
        color_selectors = [".color", "[class*='color']", ".colorName"]
        for sel in color_selectors:
            el = item.select_one(sel)
            if el:
                color = normalize_color(el.get_text(strip=True))
                if color:
                    break

        # Fallback: scan text for color keywords
        if not color:
            for jp_color, en_color in COLOR_MAP.items():
                if jp_color in full_text:
                    color = en_color
                    break

        # --- Raw extra data ---
        raw_data = {
            "html_snippet": str(item)[:500],
        }
        mileage_match = re.search(r"([\d,]+)\s*km", full_text)
        if mileage_match:
            raw_data["mileage_km"] = mileage_match.group(1).replace(",", "")

        return {
            "external_id": external_id,
            "make": make or "Unknown",
            "model": model,
            "year": year,
            "price": price,
            "color": color,
            "link": href,
            "raw_data": raw_data,
        }

    def _extract_from_links(self, soup: BeautifulSoup, brand_name: str = None) -> list[dict]:
        """Last-resort extraction based on detail page links."""
        cars = []
        links = soup.find_all("a", href=re.compile(r"/usedcar/detail/"))
        seen = set()
        for link in links:
            href = link.get("href", "")
            if not href.startswith("http"):
                href = "https://www.carsensor.net" + href
            ext_id = extract_external_id(href)
            if ext_id and ext_id not in seen:
                seen.add(ext_id)
                cars.append({
                    "external_id": ext_id,
                    "make": brand_name or "Unknown",
                    "model": link.get_text(strip=True) or "Unknown",
                    "year": None,
                    "price": None,
                    "color": "",
                    "link": href,
                    "raw_data": {},
                })
        return cars

    async def scrape_listings(self, max_pages: int = 5) -> list[dict]:
        """
        Main scraping method — iterates over all brands and pages.
        Passes brand_name to parse_listings so make is always correct.
        """
        all_cars = []
        errors = 0

        for brand_code, brand_name in SCRAPE_TARGETS:
            for page_num in range(1, max_pages + 1):
                if page_num == 1:
                    url = f"{self.BASE_URL}/{brand_code}/s001/index.html"
                else:
                    url = f"{self.BASE_URL}/{brand_code}/s001/index{page_num}.html"

                try:
                    logger.info(f"Scraping [{brand_name} p{page_num}]: {url}")
                    html = await self.fetch_page(url)
                    cars = self.parse_listings(html, brand_name=brand_name, page_url=url)
                    logger.info(f"Found {len(cars)} cars on page")

                    if len(cars) == 0:
                        # No listings found — probably end of results for this brand
                        break

                    all_cars.extend(cars)
                    await asyncio.sleep(2)  # Rate limiting

                except Exception as e:
                    errors += 1
                    logger.error(f"Error scraping {url}: {e}")
                    if errors >= 5:
                        logger.warning("Too many errors, stopping scrape early")
                        break
                    continue

        logger.info(f"Scraping complete: {len(all_cars)} cars found, {errors} errors")
        return all_cars

    async def close(self):
        await self.client.aclose()