from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .auth import User
    from .inventory import Product
    from .master_data import Customer
    from .production import ProductionOrder


# ---------------------------------------------------------------------------
# Sales: Sales Order
# ---------------------------------------------------------------------------
class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    so_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    order_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    delivery_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    customer: Mapped[Customer] = relationship(back_populates="sales_orders")
    items: Mapped[list[SalesOrderItem]] = relationship(
        back_populates="so", cascade="all, delete-orphan"
    )
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])

    __table_args__ = (Index("idx_so_customer_status", "customer_id", "status"),)


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    so_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_delivered: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    so: Mapped[SalesOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
    production_orders: Mapped[list[ProductionOrder]] = relationship(back_populates="so_item")

    __table_args__ = (
        CheckConstraint("qty_ordered > 0", name="ck_so_item_qty_ordered_positive"),
        CheckConstraint("qty_delivered >= 0", name="ck_so_item_qty_delivered_non_negative"),
        CheckConstraint("qty_delivered <= qty_ordered", name="ck_so_item_qty_delivered_not_exceed"),
        CheckConstraint("unit_price >= 0", name="ck_so_item_unit_price_non_negative"),
    )


# ---------------------------------------------------------------------------
# Production: Production Order
# ---------------------------------------------------------------------------
