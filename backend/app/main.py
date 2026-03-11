"""Auto-Ads Service — FastAPI application entry point.

Registers all routers, middleware, and system endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, cars

app = FastAPI(
    title="Auto-Ads Service",
    description="Car advertisement aggregation system with scraping, API, and Telegram bot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ─────────────────────────────────────────
# Allow frontend origins for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ───────────────────────────────────────
app.include_router(auth.router)
app.include_router(cars.router)


# ── System Endpoints ───────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {"status": "ok", "service": "auto-ads-backend"}