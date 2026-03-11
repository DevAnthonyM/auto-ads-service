"""Authentication router — login endpoint.

Provides JWT token generation for valid credentials.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, verify_password
from app.database import get_db
from app.models import User
from app.schemas import ErrorResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        200: {"description": "Successfully authenticated, JWT returned"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
    summary="Authenticate and receive JWT token",
    description="Accepts username and password, returns a Bearer token for accessing protected endpoints.",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return JWT access token."""

    # Look up user by username
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()

    # Validate credentials — use constant-time comparison via bcrypt
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT with username in 'sub' claim
    access_token = create_access_token(data={"sub": user.username})

    return TokenResponse(access_token=access_token)