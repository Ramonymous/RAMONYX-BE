"""Pydantic schemas for production management"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkCenterBase(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    type: str
    capacity: int | None = Field(None, gt=0)
    is_active: bool = True


class WorkCenterCreate(WorkCenterBase):
    pass


class WorkCenterUpdate(BaseModel):
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=100)
    type: str | None = None
    capacity: int | None = Field(None, gt=0)
    is_active: bool | None = None


class WorkCenter(WorkCenterBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class BOMItemBase(BaseModel):
    sequence: int = Field(gt=0)
    item_type: str
    product_id: UUID | None = None
    work_center_id: UUID | None = None
    quantity: float = Field(gt=0)
    notes: str | None = None


class BOMItemCreate(BOMItemBase):
    pass


class BOMItem(BOMItemBase):
    id: UUID
    bom_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BOMBase(BaseModel):
    product_id: UUID
    bom_name: str | None = None
    version: str = "1.0"
    is_active: bool = True
    notes: str | None = None


class BOMCreate(BOMBase):
    items: list[BOMItemCreate]


class BOMUpdate(BaseModel):
    bom_name: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class BOM(BOMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionOrderBase(BaseModel):
    order_number: str = Field(max_length=50)
    product_id: UUID
    bom_id: UUID
    work_center_id: UUID | None = None
    so_item_id: UUID | None = None
    planned_quantity: int = Field(gt=0)
    planned_start_date: datetime | None = None
    planned_end_date: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    notes: str | None = None


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(BaseModel):
    status: str | None = None
    qty_produced: int | None = Field(None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    notes: str | None = None


class ProductionOrder(ProductionOrderBase):
    id: UUID
    qty_produced: int = Field(ge=0)
    status: str
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionSummary(BaseModel):
    total_orders: int
    draft_orders: int
    in_progress_orders: int
    completed_orders: int
    total_planned_qty: int
    total_produced_qty: int
    completion_rate: float
