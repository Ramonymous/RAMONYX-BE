from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .auth import User
    from .inventory import Product
    from .sales import SalesOrderItem


# ---------------------------------------------------------------------------
# BOM (Bill of Materials)
# ---------------------------------------------------------------------------
class WorkCenter(Base):
    __tablename__ = "work_centers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    bom_items: Mapped[list[BOMItem]] = relationship(back_populates="work_center")


class BOM(Base, TimestampMixin):
    __tablename__ = "boms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    bom_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped[Product] = relationship(back_populates="boms")
    items: Mapped[list[BOMItem]] = relationship(back_populates="bom", cascade="all, delete-orphan")


class BOMItem(Base):
    __tablename__ = "bom_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    bom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("boms.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True)
    work_center_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_centers.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    bom: Mapped[BOM] = relationship(back_populates="items")
    product: Mapped[Product | None] = relationship()
    work_center: Mapped[WorkCenter | None] = relationship(back_populates="bom_items")

    __table_args__ = (
        UniqueConstraint("bom_id", "sequence", name="uq_bom_items_sequence"),
        Index("idx_bom_items_bom_seq", "bom_id", "sequence"),
        # PERBAIKAN: nilai string di CheckConstraint harus match .value enum
        # (bukan nama Python enum). PostgreSQL menyimpan string value-nya.
        # Misal: BOMItemType.MATERIAL.value == "material" → pakai 'material'
        CheckConstraint(
            "(item_type = 'material' AND product_id IS NOT NULL AND work_center_id IS NULL) OR (item_type = 'operation' AND work_center_id IS NOT NULL AND product_id IS NULL)",
            name="ck_bom_item_type_reference",
        ),
    )


class ProductionOrder(Base, TimestampMixin):
    __tablename__ = "production_orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    bom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("boms.id", ondelete="RESTRICT"), nullable=False, index=True)
    so_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sales_order_items.id", ondelete="SET NULL"), index=True)
    work_center_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_centers.id", ondelete="SET NULL"), index=True)
    planned_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_start_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    planned_end_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    qty_planned: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_produced: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    product: Mapped[Product] = relationship()
    bom: Mapped[BOM] = relationship()
    work_center: Mapped[WorkCenter | None] = relationship()
    so_item: Mapped[SalesOrderItem | None] = relationship(back_populates="production_orders")
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint("qty_planned > 0", name="ck_prod_order_qty_planned_positive"),
        CheckConstraint("qty_produced >= 0", name="ck_prod_order_qty_produced_non_negative"),
        Index("idx_prod_order_status_created", "status", "created_at"),
    )
