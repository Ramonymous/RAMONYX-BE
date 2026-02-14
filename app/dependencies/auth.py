import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import TokenError, decode_token, oauth2_scheme
from app.database import get_db
from app.models import Role, User


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_type="access")
        user_id = uuid.UUID(payload["sub"])
    except (TokenError, ValueError, KeyError):
        raise credentials_exception

    stmt = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id)
    user = (await db.scalars(stmt)).first()

    if not user or not user.is_active or user.deleted_at is not None:
        raise credentials_exception

    return user


def require_permissions(*required_permissions: str) -> Callable:
    async def permission_guard(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = {permission.code for role in current_user.roles for permission in role.permissions}

        if not set(required_permissions).issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return permission_guard
