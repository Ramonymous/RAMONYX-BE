"""User management API endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.database import get_db
from app.dependencies import require_permissions
from app.models.auth import Permission, Role, User
from app.schemas.users import (
    Permission as PermissionSchema,
    Role as RoleSchema,
    RoleCreate,
    User as UserSchema,
    UserCreate,
    UserProfile,
    UserSummary,
)

router = APIRouter()


# Permission endpoints
@router.get("/permissions/", response_model=list[PermissionSchema])
async def get_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get all permissions"""
    query = select(Permission).order_by(Permission.code).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/permissions/{permission_id}", response_model=PermissionSchema)
async def get_permission(
    permission_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get specific permission by ID"""
    result = await db.execute(select(Permission).where(Permission.id == permission_id))
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    return permission


# Role endpoints
@router.get("/roles/", response_model=list[RoleSchema])
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get all roles with their permissions"""
    query = select(Role).order_by(Role.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/roles/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get specific role by ID"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role


@router.post("/roles/", response_model=RoleSchema)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:create")),
):
    """Create a new role with permissions"""
    import uuid

    # Check if role name already exists
    existing = await db.execute(select(Role).where(Role.name == role.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role name already exists")

    # Create role
    db_role = Role(id=uuid.uuid4(), name=role.name, description=role.description, is_active=role.is_active)
    db.add(db_role)

    # Add permissions to role
    if role.permission_ids:
        for permission_id in role.permission_ids:
            # Verify permission exists
            permission_result = await db.execute(select(Permission).where(Permission.id == permission_id))
            if permission_result.scalar_one_or_none():
                db_role.permissions.append(permission_result.scalar_one())

    await db.commit()
    await db.refresh(db_role)

    return db_role


# User endpoints
@router.get("/users/", response_model=list[UserSchema])
async def get_users(
    is_active: bool | None = Query(None, description="Filter by active status"),
    role_name: str | None = Query(None, description="Filter by role name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get users with optional filtering"""
    query = select(User)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if role_name:
        query = query.join(User.roles).where(Role.name == role_name)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get user profile with roles and permissions"""
    result = await db.execute(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/users/", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:create")),
):
    """Create a new user"""
    import uuid

    # Check if username already exists
    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email already exists
    existing_email = await db.execute(select(User).where(User.email == user.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    db_user = User(
        id=uuid.uuid4(),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hash_password(user.password),
        is_active=user.is_active,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.get("/reports/users/", response_model=UserSummary)
async def get_user_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("users:read")),
):
    """Get user summary statistics"""

    # Count active and inactive users
    active_count_result = await db.execute(select(func.count(User.id)).where(User.is_active))
    active_count = active_count_result.scalar()

    inactive_count_result = await db.execute(select(func.count(User.id)).where(~User.is_active))
    inactive_count = inactive_count_result.scalar()

    # Count total users
    total_count_result = await db.execute(select(func.count(User.id)))
    total_count = total_count_result.scalar()

    # Count roles and permissions
    role_count_result = await db.execute(select(func.count(Role.id)))
    permission_count_result = await db.execute(select(func.count(Permission.id)))

    role_count = role_count_result.scalar()
    permission_count = permission_count_result.scalar()

    return UserSummary(
        total_users=total_count or 0,
        active_users=active_count or 0,
        inactive_users=inactive_count or 0,
        total_roles=role_count or 0,
        total_permissions=permission_count or 0,
    )
