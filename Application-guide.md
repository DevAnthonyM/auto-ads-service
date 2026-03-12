🚗 Auto-Ads Service
     
A full-stack auto-advertising service that scrapes used car listings from carsensor.net, stores them in PostgreSQL, exposes a JWT-secured REST API, renders a protected Next.js SPA, and powers a Telegram bot with LLM function calling for natural language car search.

Architecture
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ Scraper  │───▶│PostgreSQL│◀───│  FastAPI Backend  │  │
│  │(Playwright│    │   :5432  │    │     :8000         │  │
│  │+ httpx)  │    └──────────┘    └────────┬─────────┘  │
│  └──────────┘         ▲                   │             │
│                        │           ┌──────▼──────┐      │
│  ┌──────────┐          │           │  Next.js    │      │
│  │Telegram  │──────────┘           │  Frontend   │      │
│  │   Bot    │  (direct DB)         │   :3000     │      │
│  │(LLM+kw)  │                      └─────────────┘      │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘




User Flow:
Browser ──▶ localhost:3000 (Next.js) ──▶ localhost:8000 (FastAPI) ──▶ PostgreSQL
Telegram ──▶ Bot ──▶ LLM Function Calling ──▶ PostgreSQL ──▶ Formatted Response
Scraper ──▶ carsensor.net ──▶ Parse & Transform ──▶ Upsert to PostgreSQL

Quick Start
Requirements: Docker Desktop, Git
# 1. Clone
git clone https://github.com/DevAnthonyM/auto-ads-service.git
cd auto-ads-service

# 2. Configure environment
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, JWT_SECRET, TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY

# 3. Launch everything
docker-compose up --build
Wait ~2 minutes for the scraper to complete its first cycle, then open:
Service	URL
Frontend	http://localhost:3000
API (Swagger)	http://localhost:8000/docs
Health Check	http://localhost:8000/health




Default Credentials
Username: admin
Password: admin123


API Documentation
Method	Endpoint	Auth	Description
POST	/api/login	None	Login, returns JWT token
GET	/api/cars	Bearer JWT	Paginated car listing with filters
GET	/health	None	Service health check

GET /api/cars — Query Parameters
Parameter	Type	Description
page	int	Page number (default: 1)
per_page	int	Results per page (default: 20, max: 100)
make	string	Filter by manufacturer (case-insensitive)
model	string	Filter by model name
year_min	int	Minimum manufacturing year
year_max	int	Maximum manufacturing year
price_min	float	Minimum price in JPY
price_max	float	Maximum price in JPY
color	string	Filter by color
sort_by	string	Sort field (default: created_at)
sort_order	string	asc or desc (default: desc)
Example API Usage
# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get cars with token
curl http://localhost:8000/api/cars \
  -H "Authorization: Bearer <your-token>"

# Filter: Toyota under 1 million yen
curl "http://localhost:8000/api/cars?make=Toyota&price_max=1000000" \
  -H "Authorization: Bearer <your-token>"

Telegram Bot
Setup
1.	Open Telegram → search @Auto_Ads_Bot

Command	Description
/start	Welcome message + usage examples
/help	Show example queries
/latest	Show 5 most recently added cars

Natural Language Queries
For example
You: Find a red BMW under 2 million
Bot: 🔍 Found 3 cars matching your criteria...
     🚗 BMW 3 Series (2019) — ¥1.8M | Red | View listing

You: Show me Toyota cars from 2020
Bot: 🚗 Toyota Corolla (2020) — ¥1.2M | White | View listing
     🚗 Toyota Prius (2020) — ¥1.9M | Silver | View listing

You: Blue Honda under 500,000
Bot: 🔍 Found 2 cars matching your criteria...

Scraper
•	Target: carsensor.net — Japan's largest used car marketplace
•	Method: Playwright (headless Chromium) for JavaScript-rendered pages, with httpx fallback
•	Brands scraped: Toyota, Honda, Nissan, Mazda, Subaru, Mitsubishi, Daihatsu, Suzuki, Lexus, BMW, Mercedes
•	Schedule: Runs on startup, then every 30 minutes (configurable via SCRAPE_INTERVAL_MINUTES)
•	Upsert logic: PostgreSQL INSERT ... ON CONFLICT (external_id) DO UPDATE — no duplicates, price/color always current
•	Retry logic: Exponential backoff (1s → 2s → 4s), max 3 attempts per page
•	Seed fallback: If scraping fails (geo-block, rate-limit), falls back to 50 realistic seed cars so the app always has data

Tech Stack
Layer	Technology	Version
Backend Framework	FastAPI	0.109.0
ORM	SQLAlchemy (async)	2.0.25
Migrations	Alembic	1.13.1
Database	PostgreSQL	16
Scraper HTTP	httpx + Playwright	0.26.0 / 1.41+
HTML Parsing	BeautifulSoup4	4.12.3
Scheduler	APScheduler	3.10.4
Auth	python-jose + passlib/bcrypt	3.3.0 / 1.7.4
Frontend	Next.js + TypeScript	14
UI	Tailwind CSS	3.x
State	Zustand + TanStack Query	latest
Telegram	python-telegram-bot	20.7
LLM	Anthropic/DeepSeek API	-
Containerization	Docker + Docker Compose	-

Environment Variables
Variable	Required	Description
POSTGRES_USER	Yes	PostgreSQL username
POSTGRES_PASSWORD	Yes	PostgreSQL password
POSTGRES_DB	Yes	Database name
DATABASE_URL	Yes	Full async DB connection string
JWT_SECRET	Yes	Secret key for JWT signing
JWT_ALGORITHM	No	Algorithm (default: HS256)
JWT_EXPIRATION_MINUTES	No	Token lifetime (default: 60)
ADMIN_USERNAME	No	Default admin username (default: admin)
ADMIN_PASSWORD	No	Default admin password (default: admin123)
SCRAPE_INTERVAL_MINUTES	No	Scrape frequency (default: 30)
SCRAPE_MAX_PAGES	No	Pages per brand per cycle (default: 5)
TELEGRAM_BOT_TOKEN	No*	Telegram bot token from @BotFather
ANTHROPIC_API_KEY	No*	LLM API key (bot falls back to keywords if missing)


Project Structure
auto-ads-service/
├── docker-compose.yml          # Orchestrates all 5 services
├── .env.example                # All required variables documented
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── entrypoint.sh           # migrate → seed → serve
│   ├── seed.py                 # Idempotent admin user seeder
│   ├── alembic/                # Database migrations
│   └── app/
│       ├── main.py             # FastAPI app, CORS, routers
│       ├── config.py           # Pydantic settings from env
│       ├── database.py         # Async SQLAlchemy engine
│       ├── models.py           # User + Car ORM models
│       ├── schemas.py          # Pydantic request/response models
│       ├── auth.py             # JWT creation & verification
│       ├── dependencies.py     # get_current_user dependency
│       └── routers/
│           ├── auth.py         # POST /api/login
│           └── cars.py         # GET /api/cars
├── scraper/
│   ├── Dockerfile
│   └── app/
│       ├── main.py             # Scheduler entry point
│       ├── scraper.py          # Playwright + httpx scraper
│       ├── upsert.py           # PostgreSQL ON CONFLICT upsert
│       ├── seed_data.py        # Fallback seed cars
│       └── config.py
├── frontend/
│   ├── Dockerfile              # Multi-stage Node build
│   └── src/
│       ├── app/
│       │   ├── page.tsx        # Protected car table
│       │   └── login/page.tsx  # Login form
│       ├── components/         # CarTable, FilterBar, Navbar, Pagination
│       ├── lib/
│       │   ├── api.ts          # Axios with JWT interceptor
│       │   └── auth.ts         # Zustand auth store
│       └── types/index.ts      # TypeScript interfaces
└── telegram-bot/
    ├── Dockerfile
    └── app/
        ├── main.py             # Bot polling entry point
        ├── handlers.py         # /start, /help, /latest, search
        ├── llm.py              # LLM function calling + keyword fallback
        ├── db.py               # Direct DB query layer
        └── config.py

Architectural Decisions
FastAPI over Django/Flask: Async-native, automatic OpenAPI/Swagger docs, Pydantic validation built-in, and fastest Python framework. Matches the job description stack requirements.
PostgreSQL ON CONFLICT upsert over ORM merge: Using SQLAlchemy's dialect-specific insert().on_conflict_do_update() gives atomic, single-query upserts. Avoids race conditions from SELECT-then-INSERT patterns common in ORM-level upserts.
Playwright for scraping: carsensor.net renders car listings via JavaScript. BeautifulSoup alone returns empty pages. Playwright runs headless Chromium to execute JavaScript before parsing, with httpx as a lightweight fallback for pages that do render server-side.
LLM Function Calling over regex parsing: Regex parsers break on unexpected phrasing. Function calling gives the LLM a typed schema and lets it handle synonyms, price formats (万円, millions, M), implicit filters, and multilingual input. The keyword fallback ensures the bot still works without an API key.
Polling over webhooks for Telegram bot: Webhooks require a public HTTPS endpoint with a valid SSL certificate. Polling works in any Docker environment without external infrastructure, making the reviewer's setup zero-friction.
Zustand + TanStack Query over Redux: Zustand for auth state (3 lines vs 50 with Redux). TanStack Query for server state with automatic caching, background refetch, and loading/error states. Right tool for each concern.
Alembic migrations over create_all(): Base.metadata.create_all() is not production-safe — it can't alter existing tables. Alembic gives version-controlled, reversible, auto-generated migrations matching how real production databases are managed.

Known Limitations
•	Japanese make/model data: carsensor.net listing titles contain full Japanese model descriptions. Make extraction relies on URL brand codes; model field retains Japanese characters. A production system would use a Japanese car make/model lookup table.
•	Scraper geo-sensitivity: Results may vary by IP region. The seed data fallback ensures the app always has cars to display.
•	LLM dependency: Without a funded API key, the bot uses keyword matching. Natural language understanding is reduced but functional for common queries.
•	No webhook support: Bot uses polling. For production, Telegram recommends webhooks with SSL.


Built as a technical assessment for Million Miles an international vehicle logistics holding company.

