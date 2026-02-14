from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .inventory import Product
    from .purchasing import PurchaseOrder
    from .sales import SalesOrder


# ---------------------------------------------------------------------------
# Master Data: Supplier, Customer
# ---------------------------------------------------------------------------
class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    purchase_orders: Mapped[list[PurchaseOrder]] = relationship(back_populates="supplier")
    products: Mapped[list[Product]] = relationship(back_populates="supplier")


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sales_orders: Mapped[list[SalesOrder]] = relationship(back_populates="customer")


# ---------------------------------------------------------------------------
# Location (Hierarchical: Warehouse → Zone → Bin)
# ---------------------------------------------------------------------------
