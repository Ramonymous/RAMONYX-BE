"""Purchasing management API endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permissions
from app.models import User
from app.models.master_data import Supplier
from app.models.purchasing import PurchaseOrder
from app.schemas.purchasing import (
    PurchaseOrder as PurchaseOrderSchema,
    PurchaseOrderCreate,
    Supplier as SupplierSchema,
    SupplierCreate,
    SupplierUpdate,
)

router = APIRouter()


# Supplier endpoints
@router.get("/suppliers/", response_model=list[SupplierSchema])
async def get_suppliers(
    is_active: bool | None = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:read")),
):
    """Get suppliers with optional filtering"""
    query = select(Supplier)

    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/suppliers/{supplier_id}", response_model=SupplierSchema)
async def get_supplier(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:read")),
):
    """Get specific supplier by ID"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return supplier


@router.post("/suppliers/", response_model=SupplierSchema)
async def create_supplier(
    supplier: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:create")),
):
    """Create a new supplier"""
    import uuid

    db_supplier = Supplier(
        id=uuid.uuid4(),
        code=supplier.code,
        name=supplier.name,
        contact_person=supplier.contact_person,
        email=supplier.email,
        phone=supplier.phone,
        address=supplier.address,
        is_active=supplier.is_active,
    )
    db.add(db_supplier)
    await db.commit()
    await db.refresh(db_supplier)

    return db_supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierSchema)
async def update_supplier(
    supplier_id: UUID,
    supplier_update: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:update")),
):
    """Update supplier"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    await db.commit()
    await db.refresh(supplier)

    return supplier


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:delete")),
):
    """Delete supplier (soft delete)"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_active = False
    await db.commit()

    return {"message": "Supplier deactivated successfully"}


# Purchase Order endpoints
@router.get("/purchase-orders/", response_model=list[PurchaseOrderSchema])
async def get_purchase_orders(
    supplier_id: UUID | None = Query(None, description="Filter by supplier ID"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:read")),
):
    """Get purchase orders with optional filtering"""
    query = select(PurchaseOrder)

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderSchema)
async def get_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:read")),
):
    """Get specific purchase order by ID"""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return po


@router.post("/purchase-orders/", response_model=PurchaseOrderSchema)
async def create_purchase_order(
    po: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("purchasing:create")),
):
    """Create a new purchase order"""
    import uuid

    db_po = PurchaseOrder(
        id=uuid.uuid4(),
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        status=po.status,
        order_date=po.order_date,
        expected_date=po.expected_date,
        total_amount=po.total_amount,
    )
    db.add(db_po)
    await db.commit()
    await db.refresh(db_po)

    return db_po
