"""Web scraper for carsensor.net car listings.

Uses Playwright for JavaScript-rendered pages with httpx as a lightweight fallback.
Implements retry logic with exponential backoff via tenacity.
"""

import asyncio
import re

from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings

# Base URL patterns for carsensor.net
BASE_URL = "https://www.carsensor.net"
LISTING_URL = f"{BASE_URL}/usedcar/index{{page}}.html"
BRAND_URLS = [
    f"{BASE_URL}/usedcar/bTO/s001/index{{page}}.html",  # Toyota Prius
    f"{BASE_URL}/usedcar/bHO/s062/index{{page}}.html",  # Honda Fit
    f"{BASE_URL}/usedcar/bNI/s049/index{{page}}.html",  # Nissan Note
    f"{BASE_URL}/usedcar/bBM/index{{page}}.html",        # BMW
    f"{BASE_URL}/usedcar/bMB/index{{page}}.html",        # Mercedes-Benz
]


class CarSensorScraper:
    """Scrapes car listings from carsensor.net.

    Primary: Playwright (handles JS-rendered content)
    Fallback: httpx + BeautifulSoup (for server-rendered pages)
    """

    def __init__(self):
        self.scraped_count = 0
        self.error_count = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        ),
    )
    async def fetch_page_playwright(self, url: str) -> str:
        """Fetch a page using Playwright (handles JavaScript rendering)."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                )
            )
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                content = await page.content()
                return content
            finally:
                await browser.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    )
    async def fetch_page_httpx(self, url: str) -> str:
        """Fetch a page using httpx (lightweight, no JS rendering)."""
        import httpx

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ja,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def fetch_page(self, url: str) -> str:
        """Fetch a page, trying Playwright first, then httpx fallback."""
        try:
            logger.debug(f"Fetching with Playwright: {url}")
            return await self.fetch_page_playwright(url)
        except Exception as e:
            logger.warning(f"Playwright failed ({e}), falling back to httpx")
            try:
                return await self.fetch_page_httpx(url)
            except Exception as e2:
                logger.error(f"httpx also failed: {e2}")
                raise

    def parse_listings(self, html: str) -> list[dict]:
        """Parse car listings from carsensor.net HTML.

        Extracts: make, model, year, price, color, link from listing cards.
        carsensor.net uses various CSS class patterns for their listing items.
        """
        soup = BeautifulSoup(html, "lxml")
        cars = []

        # carsensor.net listing cards — try multiple known selectors
        # The site structure can change, so we try several patterns
        selectors = [
            "div.cassetteWrap",           # Main listing wrapper
            "div.casetteArea",            # Alternative wrapper
            "section.cassetteItem",       # Section-based cards
            "div[data-vc-bkn]",           # Data-attribute based
            "li.js-listItem",             # List item cards
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"Found {len(items)} listings using selector: {selector}")
                break

        if not items:
            # Try generic approach — find all links to individual car pages
            logger.warning("No listings found with known selectors, trying link-based extraction")
            return self._parse_from_links(soup)

        for item in items:
            try:
                car = self._extract_car_data(item)
                if car and car.get("external_id"):
                    cars.append(car)
            except Exception as e:
                logger.debug(f"Failed to parse listing item: {e}")
                self.error_count += 1
                continue

        return cars

    def _extract_car_data(self, item) -> dict | None:
        """Extract car data from a single listing card element."""
        car = {}

        # Find the detail link — this gives us the external_id
        link_el = item.select_one("a[href*='/usedcar/detail/']")
        if not link_el:
            link_el = item.select_one("a[href*='BKN=']")
        if not link_el:
            return None

        href = link_el.get("href", "")
        car["link"] = href if href.startswith("http") else f"{BASE_URL}{href}"
        car["external_id"] = self._extract_external_id(href)

        # Extract make and model from title/heading text
        title_el = (
            item.select_one(".cassetteMain__title")
            or item.select_one(".casetteItemTtl")
            or item.select_one("h3")
            or item.select_one(".carName")
            or link_el
        )
        if title_el:
            title_text = title_el.get_text(strip=True)
            make, model = self._parse_make_model(title_text)
            car["make"] = make
            car["model"] = model

        # Extract year
        year_el = item.select_one(".cassetteMain__spec") or item.select_one(".year")
        if year_el:
            car["year"] = self._parse_year(year_el.get_text())
        else:
            # Try to find year anywhere in the card text
            all_text = item.get_text()
            car["year"] = self._parse_year(all_text)

        # Extract price
        price_el = (
            item.select_one(".cassetteMain__priceValue")
            or item.select_one(".priceWrap")
            or item.select_one(".price")
        )
        if price_el:
            car["price"] = self._parse_price(price_el.get_text())
        else:
            car["price"] = self._parse_price(item.get_text())

        # Extract color
        color_el = item.select_one(".color") or item.select_one("[class*='color']")
        if color_el:
            car["color"] = color_el.get_text(strip=True)
        else:
            car["color"] = self._extract_color_from_text(item.get_text())

        # Store extra data
        car["raw_data"] = {"source": "carsensor.net", "scraped_text": item.get_text()[:500]}

        # Validate required fields
        if not all(car.get(f) for f in ["make", "model", "year", "price", "link", "external_id"]):
            return None

        return car

    def _parse_from_links(self, soup) -> list[dict]:
        """Fallback: extract car data from individual detail page links."""
        cars = []
        links = soup.select("a[href*='/usedcar/detail/']")
        seen_ids = set()

        for link in links:
            href = link.get("href", "")
            ext_id = self._extract_external_id(href)
            if not ext_id or ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)

            text = link.get_text(strip=True)
            if len(text) < 3:
                continue

            make, model = self._parse_make_model(text)
            year = self._parse_year(text)
            price = self._parse_price(text)

            if make and year and price:
                cars.append({
                    "external_id": ext_id,
                    "make": make,
                    "model": model or "Unknown",
                    "year": year,
                    "price": price,
                    "color": self._extract_color_from_text(text),
                    "link": href if href.startswith("http") else f"{BASE_URL}{href}",
                    "raw_data": {"source": "carsensor.net", "method": "link_extraction"},
                })

        return cars

    @staticmethod
    def _extract_external_id(url: str) -> str:
        """Extract unique car ID from carsensor.net URL."""
        # Pattern: /usedcar/detail/CU1234567890/
        match = re.search(r"(CU\d+|BKN=\w+|\d{10,})", url)
        if match:
            return match.group(1).replace("BKN=", "")
        # Use URL hash as fallback
        return str(hash(url))[-12:] if url else ""

    @staticmethod
    def _parse_make_model(text: str) -> tuple[str, str]:
        """Parse Japanese car make and model from listing title.

        Maps Japanese brand names to English equivalents.
        """
        japanese_to_english = {
            "トヨタ": "Toyota", "ホンダ": "Honda", "日産": "Nissan",
            "マツダ": "Mazda", "スバル": "Subaru", "三菱": "Mitsubishi",
            "スズキ": "Suzuki", "ダイハツ": "Daihatsu", "レクサス": "Lexus",
            "BMW": "BMW", "メルセデス・ベンツ": "Mercedes-Benz",
            "メルセデスベンツ": "Mercedes-Benz",
            "アウディ": "Audi", "フォルクスワーゲン": "Volkswagen",
            "ポルシェ": "Porsche", "ボルボ": "Volvo", "ミニ": "Mini",
            "フィアット": "Fiat", "プジョー": "Peugeot",
            "ランドローバー": "Land Rover", "ジャガー": "Jaguar",
        }

        make = "Unknown"
        model = text.strip()

        for jp_name, en_name in japanese_to_english.items():
            if jp_name in text:
                make = en_name
                model = text.replace(jp_name, "").strip()
                break

        # Also check for English brand names directly
        english_brands = [
            "Toyota", "Honda", "Nissan", "Mazda", "Subaru", "Mitsubishi",
            "Suzuki", "Daihatsu", "Lexus", "BMW", "Mercedes", "Audi",
            "Volkswagen", "Porsche", "Volvo", "Mini", "Fiat",
        ]
        for brand in english_brands:
            if brand.lower() in text.lower():
                make = brand
                model = re.sub(re.escape(brand), "", text, flags=re.IGNORECASE).strip()
                break

        # Clean up model name
        model = model[:100] if model else "Unknown"
        return make, model

    @staticmethod
    def _parse_year(text: str) -> int:
        """Extract manufacturing year from Japanese text.

        Handles patterns like: 2024(R06)年, 2020年式, H30年, R03年, 2022
        """
        # Western year: 2020, 2024, etc.
        match = re.search(r"(19[89]\d|20[0-2]\d)", text)
        if match:
            return int(match.group(1))

        # Japanese era year: R03 -> 2021, H30 -> 2018
        reiwa = re.search(r"R\.?(\d{1,2})", text)
        if reiwa:
            return 2018 + int(reiwa.group(1))

        heisei = re.search(r"H\.?(\d{1,2})", text)
        if heisei:
            return 1988 + int(heisei.group(1))

        return 2024  # Default to current-ish year

    @staticmethod
    def _parse_price(text: str) -> float:
        """Extract price in JPY from Japanese price text.

        Handles: 150万円 -> 1500000, 150.5万円 -> 1505000,
                 1,500,000円 -> 1500000, 応談 -> 0
        """
        #万円 (man-en) = 10,000 yen units
        man_match = re.search(r"([\d,.]+)\s*万", text)
        if man_match:
            value = float(man_match.group(1).replace(",", ""))
            return value * 10000

        # Direct yen amount
        yen_match = re.search(r"([\d,]+)\s*円", text)
        if yen_match:
            return float(yen_match.group(1).replace(",", ""))

        # Just a number
        num_match = re.search(r"([\d,]+\.?\d*)", text)
        if num_match:
            val = float(num_match.group(1).replace(",", ""))
            if val < 10000:  # Likely in 万 units
                return val * 10000
            return val

        return 0

    @staticmethod
    def _extract_color_from_text(text: str) -> str | None:
        """Extract car color from Japanese text."""
        color_map = {
            "ブラック": "Black", "黒": "Black",
            "ホワイト": "White", "白": "White",
            "シルバー": "Silver", "銀": "Silver",
            "レッド": "Red", "赤": "Red",
            "ブルー": "Blue", "青": "Blue",
            "グレー": "Gray", "灰": "Gray",
            "グリーン": "Green", "緑": "Green",
            "イエロー": "Yellow", "黄": "Yellow",
            "ブラウン": "Brown", "茶": "Brown",
            "パール": "Pearl White",
            "ベージュ": "Beige",
            "ゴールド": "Gold",
            "オレンジ": "Orange",
            "ワインレッド": "Wine Red",
            "ガンメタリック": "Gunmetal",
        }
        for jp, en in color_map.items():
            if jp in text:
                return en
        return None

    async def scrape_listings(self, max_pages: int = 5) -> list[dict]:
        """Scrape car listings from multiple pages.

        Rate limits requests to avoid overloading the server.
        """
        all_cars = []
        seen_ids = set()

        urls_to_scrape = []
        for brand_url_template in BRAND_URLS[:3]:  # Limit to 3 brands for speed
            for page_num in range(1, max_pages + 1):
                page_suffix = "" if page_num == 1 else str(page_num)
                url = brand_url_template.replace("{page}", page_suffix)
                urls_to_scrape.append(url)

        for url in urls_to_scrape:
            try:
                logger.info(f"Scraping: {url}")
                html = await self.fetch_page(url)
                cars = self.parse_listings(html)

                for car in cars:
                    if car["external_id"] not in seen_ids:
                        seen_ids.add(car["external_id"])
                        all_cars.append(car)
                        self.scraped_count += 1

                logger.info(f"Found {len(cars)} cars on page")

                # Rate limiting — be respectful to the server
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                self.error_count += 1
                continue

        logger.info(
            f"Scraping complete: {self.scraped_count} cars found, {self.error_count} errors"
        )
        return all_cars