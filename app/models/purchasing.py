from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    from .master_data import Supplier


# ---------------------------------------------------------------------------
# Purchasing: Purchase Order
# ---------------------------------------------------------------------------
class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    supplier: Mapped[Supplier] = relationship(back_populates="purchase_orders")
    # PERBAIKAN: hapus lazy="selectin" dari model — strategi loading
    # sebaiknya ditentukan per-query via options(selectinload(...)) agar
    # tidak mempengaruhi semua query secara global.
    items: Mapped[list[PurchaseOrderItem]] = relationship(back_populates="po", cascade="all, delete-orphan")
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])

    __table_args__ = (Index("idx_po_status_created", "status", "created_at"),)


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    po_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_received: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    po: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    __table_args__ = (
        # PERBAIKAN: qty_ordered > 0 (bukan >= 0) karena item tanpa qty tidak valid
        CheckConstraint("qty_ordered > 0", name="ck_po_item_qty_ordered_positive"),
        CheckConstraint("qty_received >= 0", name="ck_po_item_qty_received_non_negative"),
        CheckConstraint("qty_received <= qty_ordered", name="ck_po_item_qty_received_not_exceed"),
        CheckConstraint("unit_price >= 0", name="ck_po_item_unit_price_non_negative"),
    )


# ---------------------------------------------------------------------------
# Sales: Sales Order
# ---------------------------------------------------------------------------
