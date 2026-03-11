"""Cars router — protected car listing endpoint.

Provides paginated, filterable, sortable access to scraped car data.
"""

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Car, User
from app.schemas import PaginatedCarsResponse

router = APIRouter(prefix="/api", tags=["Cars"])

# Columns that are allowed for sorting — prevents SQL injection via sort_by
ALLOWED_SORT_COLUMNS = {"make", "model", "year", "price", "color", "created_at", "updated_at"}


@router.get(
    "/cars",
    response_model=PaginatedCarsResponse,
    summary="List car advertisements",
    description=(
        "Returns a paginated list of scraped car ads. "
        "Supports filtering by make, model, year range, price range, and color. "
        "Requires a valid JWT token."
    ),
)
async def get_cars(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    # Filters
    make: str | None = Query(None, description="Filter by car make (case-insensitive)"),
    model: str | None = Query(None, description="Filter by car model (case-insensitive)"),
    year_min: int | None = Query(None, description="Minimum manufacturing year"),
    year_max: int | None = Query(None, description="Maximum manufacturing year"),
    price_min: float | None = Query(None, ge=0, description="Minimum price (JPY)"),
    price_max: float | None = Query(None, ge=0, description="Maximum price (JPY)"),
    color: str | None = Query(None, description="Filter by color (case-insensitive)"),
    # Sorting
    sort_by: str = Query("created_at", description="Column to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    # Auth
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedCarsResponse:
    """Return paginated, filtered car listings."""

    # Base query — only active listings
    query = select(Car).where(Car.is_active == True)  # noqa: E712
    count_query = select(func.count()).select_from(Car).where(Car.is_active == True)  # noqa: E712

    # ── Apply filters ──────────────────────────────────────
    if make:
        query = query.where(Car.make.ilike(f"%{make}%"))
        count_query = count_query.where(Car.make.ilike(f"%{make}%"))
    if model:
        query = query.where(Car.model.ilike(f"%{model}%"))
        count_query = count_query.where(Car.model.ilike(f"%{model}%"))
    if year_min is not None:
        query = query.where(Car.year >= year_min)
        count_query = count_query.where(Car.year >= year_min)
    if year_max is not None:
        query = query.where(Car.year <= year_max)
        count_query = count_query.where(Car.year <= year_max)
    if price_min is not None:
        query = query.where(Car.price >= price_min)
        count_query = count_query.where(Car.price >= price_min)
    if price_max is not None:
        query = query.where(Car.price <= price_max)
        count_query = count_query.where(Car.price <= price_max)
    if color:
        query = query.where(Car.color.ilike(f"%{color}%"))
        count_query = count_query.where(Car.color.ilike(f"%{color}%"))

    # ── Sorting ────────────────────────────────────────────
    # Validate sort column to prevent injection
    if sort_by not in ALLOWED_SORT_COLUMNS:
        sort_by = "created_at"

    sort_column = getattr(Car, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # ── Get total count ────────────────────────────────────
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # ── Pagination ─────────────────────────────────────────
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # ── Execute ────────────────────────────────────────────
    result = await db.execute(query)
    cars = result.scalars().all()

    return PaginatedCarsResponse(
        items=cars,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )