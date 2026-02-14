"""Warehouse management API endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permissions
from app.models import User
from app.models.inventory import Location
from app.schemas.warehouse import (
    Location as LocationSchema,
    LocationCreate,
    LocationUpdate,
)

router = APIRouter()


@router.get("/locations/", response_model=list[LocationSchema])
async def get_locations(
    location_type: str | None = Query(None, description="Filter by location type"),
    parent_id: UUID | None = Query(None, description="Filter by parent location"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("warehouse:read")),
):
    """Get locations with optional filtering"""
    query = select(Location)

    if location_type:
        query = query.where(Location.type == location_type)
    if parent_id:
        query = query.where(Location.parent_id == parent_id)
    if is_active is not None:
        query = query.where(Location.is_active == is_active)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/locations/{location_id}", response_model=LocationSchema)
async def get_location(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("warehouse:read")),
):
    """Get specific location by ID"""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return location


@router.post("/locations/", response_model=LocationSchema)
async def create_location(
    location: LocationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("warehouse:create")),
):
    """Create a new location"""
    db_location = Location(**location.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)

    return db_location


@router.put("/locations/{location_id}", response_model=LocationSchema)
async def update_location(
    location_id: UUID,
    location_update: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("warehouse:update")),
):
    """Update location"""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    update_data = location_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    await db.commit()
    await db.refresh(location)

    return location


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("warehouse:delete")),
) -> dict[str, str]:
    """Delete location (soft delete)"""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    location.is_active = False
    await db.commit()

    return {"message": "Location deactivated successfully"}
