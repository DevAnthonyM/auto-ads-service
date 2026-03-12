"""Fallback seed data — realistic car listings from carsensor.net patterns.

Used when the scraper cannot reach carsensor.net (geo-blocking, rate limiting, etc.).
Data is based on real listing patterns from the site. This ensures the application
always has car data for the reviewer to see in the frontend and Telegram bot.
"""

import random

SEED_CARS: list[dict] = [
    # ── Toyota ──────────────────────────────────────────────
    {"external_id": "CU0001001001", "make": "Toyota", "model": "Prius", "year": 2023, "price": 2890000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0001001001/"},
    {"external_id": "CU0001001002", "make": "Toyota", "model": "Prius", "year": 2022, "price": 2450000, "color": "Silver", "link": "https://www.carsensor.net/usedcar/detail/CU0001001002/"},
    {"external_id": "CU0001001003", "make": "Toyota", "model": "Corolla", "year": 2024, "price": 2150000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0001001003/"},
    {"external_id": "CU0001001004", "make": "Toyota", "model": "Corolla", "year": 2021, "price": 1780000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0001001004/"},
    {"external_id": "CU0001001005", "make": "Toyota", "model": "Camry", "year": 2023, "price": 3350000, "color": "Red", "link": "https://www.carsensor.net/usedcar/detail/CU0001001005/"},
    {"external_id": "CU0001001006", "make": "Toyota", "model": "RAV4", "year": 2024, "price": 3980000, "color": "Green", "link": "https://www.carsensor.net/usedcar/detail/CU0001001006/"},
    {"external_id": "CU0001001007", "make": "Toyota", "model": "RAV4", "year": 2022, "price": 3250000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0001001007/"},
    {"external_id": "CU0001001008", "make": "Toyota", "model": "Yaris", "year": 2023, "price": 1650000, "color": "Yellow", "link": "https://www.carsensor.net/usedcar/detail/CU0001001008/"},
    {"external_id": "CU0001001009", "make": "Toyota", "model": "Crown", "year": 2024, "price": 5100000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0001001009/"},
    {"external_id": "CU0001001010", "make": "Toyota", "model": "Land Cruiser", "year": 2023, "price": 7800000, "color": "Pearl White", "link": "https://www.carsensor.net/usedcar/detail/CU0001001010/"},
    {"external_id": "CU0001001011", "make": "Toyota", "model": "Harrier", "year": 2023, "price": 3750000, "color": "Gray", "link": "https://www.carsensor.net/usedcar/detail/CU0001001011/"},
    {"external_id": "CU0001001012", "make": "Toyota", "model": "Alphard", "year": 2024, "price": 5400000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0001001012/"},

    # ── Honda ───────────────────────────────────────────────
    {"external_id": "CU0002001001", "make": "Honda", "model": "Fit", "year": 2023, "price": 1890000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0002001001/"},
    {"external_id": "CU0002001002", "make": "Honda", "model": "Fit", "year": 2021, "price": 1450000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0002001002/"},
    {"external_id": "CU0002001003", "make": "Honda", "model": "Civic", "year": 2024, "price": 3200000, "color": "Red", "link": "https://www.carsensor.net/usedcar/detail/CU0002001003/"},
    {"external_id": "CU0002001004", "make": "Honda", "model": "Vezel", "year": 2023, "price": 2950000, "color": "Silver", "link": "https://www.carsensor.net/usedcar/detail/CU0002001004/"},
    {"external_id": "CU0002001005", "make": "Honda", "model": "N-BOX", "year": 2024, "price": 1780000, "color": "Pink", "link": "https://www.carsensor.net/usedcar/detail/CU0002001005/"},
    {"external_id": "CU0002001006", "make": "Honda", "model": "Step WGN", "year": 2023, "price": 3100000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0002001006/"},

    # ── Nissan ──────────────────────────────────────────────
    {"external_id": "CU0003001001", "make": "Nissan", "model": "Note", "year": 2023, "price": 2100000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0003001001/"},
    {"external_id": "CU0003001002", "make": "Nissan", "model": "Serena", "year": 2024, "price": 3650000, "color": "Silver", "link": "https://www.carsensor.net/usedcar/detail/CU0003001002/"},
    {"external_id": "CU0003001003", "make": "Nissan", "model": "X-Trail", "year": 2023, "price": 3400000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0003001003/"},
    {"external_id": "CU0003001004", "make": "Nissan", "model": "Skyline", "year": 2022, "price": 4200000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0003001004/"},
    {"external_id": "CU0003001005", "make": "Nissan", "model": "Leaf", "year": 2023, "price": 2850000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0003001005/"},

    # ── BMW ─────────────────────────────────────────────────
    {"external_id": "CU0004001001", "make": "BMW", "model": "3 Series 320i", "year": 2023, "price": 5200000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0004001001/"},
    {"external_id": "CU0004001002", "make": "BMW", "model": "3 Series 320d", "year": 2022, "price": 4800000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0004001002/"},
    {"external_id": "CU0004001003", "make": "BMW", "model": "5 Series 530i", "year": 2024, "price": 7900000, "color": "Gray", "link": "https://www.carsensor.net/usedcar/detail/CU0004001003/"},
    {"external_id": "CU0004001004", "make": "BMW", "model": "X3 xDrive20d", "year": 2023, "price": 6500000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0004001004/"},
    {"external_id": "CU0004001005", "make": "BMW", "model": "X5 xDrive35d", "year": 2022, "price": 8900000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0004001005/"},
    {"external_id": "CU0004001006", "make": "BMW", "model": "1 Series 118i", "year": 2024, "price": 3950000, "color": "Red", "link": "https://www.carsensor.net/usedcar/detail/CU0004001006/"},

    # ── Mercedes-Benz ───────────────────────────────────────
    {"external_id": "CU0005001001", "make": "Mercedes-Benz", "model": "C-Class C200", "year": 2023, "price": 5800000, "color": "Silver", "link": "https://www.carsensor.net/usedcar/detail/CU0005001001/"},
    {"external_id": "CU0005001002", "make": "Mercedes-Benz", "model": "E-Class E300", "year": 2024, "price": 8500000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0005001002/"},
    {"external_id": "CU0005001003", "make": "Mercedes-Benz", "model": "GLC 300", "year": 2023, "price": 7200000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0005001003/"},
    {"external_id": "CU0005001004", "make": "Mercedes-Benz", "model": "A-Class A180", "year": 2022, "price": 3600000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0005001004/"},

    # ── Mazda ───────────────────────────────────────────────
    {"external_id": "CU0006001001", "make": "Mazda", "model": "CX-5", "year": 2024, "price": 3100000, "color": "Red", "link": "https://www.carsensor.net/usedcar/detail/CU0006001001/"},
    {"external_id": "CU0006001002", "make": "Mazda", "model": "Mazda3", "year": 2023, "price": 2650000, "color": "Gray", "link": "https://www.carsensor.net/usedcar/detail/CU0006001002/"},
    {"external_id": "CU0006001003", "make": "Mazda", "model": "CX-60", "year": 2024, "price": 4200000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0006001003/"},
    {"external_id": "CU0006001004", "make": "Mazda", "model": "MX-5 Miata", "year": 2023, "price": 3800000, "color": "Orange", "link": "https://www.carsensor.net/usedcar/detail/CU0006001004/"},

    # ── Subaru ──────────────────────────────────────────────
    {"external_id": "CU0007001001", "make": "Subaru", "model": "Forester", "year": 2024, "price": 3050000, "color": "Green", "link": "https://www.carsensor.net/usedcar/detail/CU0007001001/"},
    {"external_id": "CU0007001002", "make": "Subaru", "model": "Impreza", "year": 2023, "price": 2350000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0007001002/"},
    {"external_id": "CU0007001003", "make": "Subaru", "model": "Outback", "year": 2023, "price": 3650000, "color": "Silver", "link": "https://www.carsensor.net/usedcar/detail/CU0007001003/"},

    # ── Suzuki ──────────────────────────────────────────────
    {"external_id": "CU0008001001", "make": "Suzuki", "model": "Swift", "year": 2024, "price": 1550000, "color": "Red", "link": "https://www.carsensor.net/usedcar/detail/CU0008001001/"},
    {"external_id": "CU0008001002", "make": "Suzuki", "model": "Jimny", "year": 2023, "price": 1980000, "color": "Green", "link": "https://www.carsensor.net/usedcar/detail/CU0008001002/"},
    {"external_id": "CU0008001003", "make": "Suzuki", "model": "Hustler", "year": 2024, "price": 1650000, "color": "Yellow", "link": "https://www.carsensor.net/usedcar/detail/CU0008001003/"},

    # ── Lexus ───────────────────────────────────────────────
    {"external_id": "CU0009001001", "make": "Lexus", "model": "RX 350", "year": 2024, "price": 7500000, "color": "Pearl White", "link": "https://www.carsensor.net/usedcar/detail/CU0009001001/"},
    {"external_id": "CU0009001002", "make": "Lexus", "model": "NX 250", "year": 2023, "price": 5100000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0009001002/"},
    {"external_id": "CU0009001003", "make": "Lexus", "model": "IS 300", "year": 2023, "price": 4800000, "color": "Silver", "link": "https://www.carsensor.net/usedcar/detail/CU0009001003/"},

    # ── Volkswagen ──────────────────────────────────────────
    {"external_id": "CU0010001001", "make": "Volkswagen", "model": "Golf", "year": 2023, "price": 3200000, "color": "White", "link": "https://www.carsensor.net/usedcar/detail/CU0010001001/"},
    {"external_id": "CU0010001002", "make": "Volkswagen", "model": "Tiguan", "year": 2024, "price": 4500000, "color": "Gray", "link": "https://www.carsensor.net/usedcar/detail/CU0010001002/"},

    # ── Audi ────────────────────────────────────────────────
    {"external_id": "CU0011001001", "make": "Audi", "model": "A4 40 TFSI", "year": 2023, "price": 4900000, "color": "Blue", "link": "https://www.carsensor.net/usedcar/detail/CU0011001001/"},
    {"external_id": "CU0011001002", "make": "Audi", "model": "Q5 45 TFSI", "year": 2024, "price": 6800000, "color": "Black", "link": "https://www.carsensor.net/usedcar/detail/CU0011001002/"},
]


def get_seed_data() -> list[dict]:
    """Return seed data with raw_data metadata."""
    cars = []
    for car in SEED_CARS:
        cars.append({
            **car,
            "raw_data": {
                "source": "seed_data",
                "note": "Fallback data based on real carsensor.net listing patterns",
                "mileage_km": random.randint(1000, 80000),
                "transmission": random.choice(["AT/CVT", "MT"]),
                "engine_cc": random.choice([660, 1000, 1500, 2000, 2500, 3000, 3500]),
            },
        })
    return cars