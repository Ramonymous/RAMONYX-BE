"""Pydantic schemas for purchasing management"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SupplierBase(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool | None = None


class Supplier(SupplierBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    notes: str | None = None


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItem(PurchaseOrderItemBase):
    id: UUID
    purchase_order_id: UUID
    received_quantity: int = Field(ge=0)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    po_number: str = Field(max_length=50)
    supplier_id: UUID
    status: str
    order_date: datetime
    expected_date: datetime | None = None
    total_amount: float = Field(ge=0)
    notes: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderUpdate(BaseModel):
    status: str | None = None
    expected_date: datetime | None = None
    notes: str | None = None


class PurchaseOrder(PurchaseOrderBase):
    id: UUID
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItem] = []

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderSummary(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    received_orders: int
    total_value: float
