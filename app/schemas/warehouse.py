"""Pydantic schemas for warehouse management"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    type: str
    parent_id: UUID | None = None
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=100)
    type: str | None = None
    parent_id: UUID | None = None
    is_active: bool | None = None


class Location(LocationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationHierarchy(BaseModel):
    location: Location
    path: str
    level: int
    children_count: int


class WarehouseSummary(BaseModel):
    total_locations: int
    warehouse_count: int
    production_floor_count: int
    subcontract_count: int
    transit_count: int
    active_locations: int
    inactive_locations: int
