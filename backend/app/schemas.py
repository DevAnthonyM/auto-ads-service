"""Pydantic schemas for API request/response validation.

These models enforce type safety and provide automatic OpenAPI documentation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Authentication ─────────────────────────────────────────


class LoginRequest(BaseModel):
    """POST /api/login request body."""

    username: str = Field(..., min_length=1, max_length=100, examples=["admin"])
    password: str = Field(..., min_length=1, max_length=128, examples=["admin123"])


class TokenResponse(BaseModel):
    """Successful login response containing JWT."""

    access_token: str
    token_type: str = "bearer"


# ── Cars ───────────────────────────────────────────────────


class CarResponse(BaseModel):
    """Single car listing returned by the API."""

    id: int
    external_id: str
    make: str
    model: str
    year: int
    price: float
    color: str | None = None
    link: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedCarsResponse(BaseModel):
    """Paginated list of car listings."""

    items: list[CarResponse]
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


# ── Errors ─────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str