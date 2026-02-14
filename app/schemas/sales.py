from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SalesOrderItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    notes: str | None = None


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderItemRead(SalesOrderItemBase):
    id: UUID
    so_id: UUID
    qty_ordered: int
    qty_delivered: int

    model_config = ConfigDict(from_attributes=True)


class SalesOrderBase(BaseModel):
    customer_id: UUID
    order_date: datetime
    delivery_date: datetime
    notes: str | None = None


class SalesOrderCreate(SalesOrderBase):
    so_number: str | None = None
    status: str = "draft"
    expected_date: datetime | None = None
    items: list[SalesOrderItemCreate]


class SalesOrderUpdate(BaseModel):
    customer_id: UUID | None = None
    order_date: datetime | None = None
    delivery_date: datetime | None = None
    notes: str | None = None
    status: str | None = None


class SalesOrderRead(SalesOrderBase):
    id: UUID
    so_number: str
    customer_id: UUID
    order_date: datetime
    delivery_date: datetime
    status: str
    notes: str | None
    total_amount: Decimal
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalesOrderList(BaseModel):
    sales_orders: list[SalesOrderRead]
    total: int
    page: int
    size: int
