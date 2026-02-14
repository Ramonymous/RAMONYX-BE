from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC as Numeric, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import FetchedValue

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .auth import User
    from .master_data import Customer, Supplier
    from .production import BOM


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped[Location | None] = relationship(back_populates="children", remote_side="Location.id")
    children: Mapped[list[Location]] = relationship(back_populates="parent")

    __table_args__ = (Index("idx_location_parent", "parent_id"),)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    uom: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    meta_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    supplier: Mapped[Supplier | None] = relationship(back_populates="products")
    customer: Mapped[Customer | None] = relationship()
    boms: Mapped[list[BOM]] = relationship(back_populates="product")
    stock_entries: Mapped[list[StockLedger]] = relationship(back_populates="product")
    stock_balances: Mapped[list[StockBalance]] = relationship(back_populates="product")

    __table_args__ = (
        # GIN index untuk query arbitrary key di JSONB
        Index("idx_product_meta_data_gin", "meta_data", postgresql_using="gin"),
    )


# ---------------------------------------------------------------------------
# Inventory: StockLedger (append-only) dan StockBalance (denormalized summary)
# ---------------------------------------------------------------------------


class StockLedger(Base):
    __tablename__ = "stock_ledgers"
    # Untuk volume besar, pertimbangkan table partitioning di PostgreSQL
    # berdasarkan created_at (monthly). Implementasikan via Alembic migration.

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    # Positif = stok masuk, negatif = stok keluar
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ref_type: Mapped[str | None] = mapped_column(String(50))
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    product: Mapped[Product] = relationship(back_populates="stock_entries")
    location: Mapped[Location] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_ledger_product_location", "product_id", "location_id"),
        Index("idx_ledger_ref", "ref_type", "ref_id"),
        Index("idx_ledger_product_location_created", "product_id", "location_id", "created_at"),
    )


class StockBalance(Base):
    __tablename__ = "stock_balances"
    # Di-update via trigger PostgreSQL (lihat catatan SQL di migration).

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True)
    current_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=FetchedValue(),
    )

    product: Mapped[Product] = relationship(back_populates="stock_balances")
    location: Mapped[Location] = relationship()
