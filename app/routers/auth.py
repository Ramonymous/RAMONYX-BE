import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Role, User
from app.schemas.auth import (
    BootstrapAdminRequest,
    BootstrapAdminResponse,
    RBACSeedSummary,
    RefreshTokenRequest,
    TokenPair,
    UserRead,
)
from app.services import BootstrapError, bootstrap_admin_user, seed_rbac

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap-admin", response_model=BootstrapAdminResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_admin(
    payload: BootstrapAdminRequest,
    db: AsyncSession = Depends(get_db),
) -> BootstrapAdminResponse:
    if not settings.bootstrap_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bootstrap key is not configured",
        )

    if payload.bootstrap_key != settings.bootstrap_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bootstrap key",
        )

    user_count = await db.scalar(select(func.count()).select_from(User))
    if user_count and user_count > 0 and not settings.allow_bootstrap_when_users_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bootstrap disabled because users already exist",
        )

    existing_target = await db.scalar(select(User).where(or_(User.username == payload.username, User.email == payload.email)))
    if existing_target:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bootstrap username or email already exists",
        )

    seed_summary_dict = {
        "permissions_created": 0,
        "roles_created": 0,
        "role_permission_links_added": 0,
    }
    if payload.seed_rbac:
        seed_summary_dict = await seed_rbac(db)

    try:
        user = await bootstrap_admin_user(
            db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role_name=payload.role_name,
        )
    except BootstrapError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return BootstrapAdminResponse(
        user=UserRead.model_validate(user),
        rbac_seed=RBACSeedSummary(**seed_summary_dict),
    )


@router.post("/login", response_model=TokenPair)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    stmt = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.username == form_data.username)
    user = (await db.scalars(stmt)).first()

    if not user or user.deleted_at is not None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    permission_codes = sorted({p.code for role in user.roles for p in role.permissions})
    role_names = sorted({role.name for role in user.roles})

    access_token = create_access_token(
        subject=str(user.id),
        claims={"roles": role_names, "permissions": permission_codes},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = uuid.UUID(token_payload["sub"])
    except (TokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id)
    user = (await db.scalars(stmt)).first()

    if not user or user.deleted_at is not None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not available for refresh",
        )

    permission_codes = sorted({p.code for role in user.roles for p in role.permissions})
    role_names = sorted({role.name for role in user.roles})

    return TokenPair(
        access_token=create_access_token(
            subject=str(user.id),
            claims={"roles": role_names, "permissions": permission_codes},
        ),
        refresh_token=create_refresh_token(subject=str(user.id)),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
