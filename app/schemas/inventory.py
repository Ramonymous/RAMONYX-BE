"""Pydantic schemas for inventory management"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StockBalanceBase(BaseModel):
    product_id: UUID
    location_id: UUID
    current_qty: int = Field(ge=0)


class StockBalanceCreate(StockBalanceBase):
    pass


class StockBalanceUpdate(BaseModel):
    current_qty: int | None = Field(None, ge=0)


class StockBalance(StockBalanceBase):
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class StockLedgerBase(BaseModel):
    product_id: UUID
    location_id: UUID
    qty: int = Field(ge=0)
    transaction_type: str
    ref_type: str | None = None
    ref_id: UUID | None = None
    notes: str | None = None


class StockLedgerCreate(StockLedgerBase):
    pass


class StockLedger(StockLedgerBase):
    id: UUID
    created_at: datetime
    created_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class StockMovementRequest(BaseModel):
    product_id: UUID
    from_location_id: UUID | None = None
    to_location_id: UUID
    quantity: int = Field(gt=0)
    transaction_type: str = "transfer"
    notes: str | None = None


class StockMovementResponse(BaseModel):
    success: bool
    message: str
    ledger_entries: list[StockLedger] = []
    updated_balances: list[StockBalance] = []


class InventoryReport(BaseModel):
    product_id: UUID
    product_sku: str
    product_name: str
    location_id: UUID
    location_name: str
    current_qty: int
    last_updated: datetime
    total_value: float | None = None


class InventorySummary(BaseModel):
    total_products: int
    total_locations: int
    total_stock_value: float | None = None
    low_stock_items: int
    out_of_stock_items: int
    report_data: list[InventoryReport]
