"""FastAPI dependencies — authentication and authorization.

Usage in routers:
    current_user: User = Depends(get_current_user)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_access_token
from app.database import get_db
from app.models import User

# OAuth2 scheme — tells Swagger UI to show the "Authorize" button
# tokenUrl must match the login endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token.

    Raises HTTPException 401 if the token is invalid, expired,
    or the user no longer exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Extract username from 'sub' claim
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Verify user still exists in database
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user