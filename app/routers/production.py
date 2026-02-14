"""Production management API endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permissions
from app.models import User
from app.models.production import BOM, ProductionOrder, WorkCenter
from app.schemas.production import (
    BOM as BOMSchema,
    BOMCreate,
    ProductionOrder as ProductionOrderSchema,
    WorkCenter as WorkCenterSchema,
    WorkCenterCreate,
)

router = APIRouter()


# Work Center endpoints
@router.get("/work-centers/", response_model=list[WorkCenterSchema])
async def get_work_centers(
    is_active: bool | None = Query(None, description="Filter by active status"),
    work_center_type: str | None = Query(None, description="Filter by work center type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:read")),
):
    """Get work centers with optional filtering"""
    query = select(WorkCenter)

    if is_active is not None:
        query = query.where(WorkCenter.is_active == is_active)
    if work_center_type:
        query = query.where(WorkCenter.type == work_center_type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/work-centers/{work_center_id}", response_model=WorkCenterSchema)
async def get_work_center(
    work_center_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:read")),
):
    """Get specific work center by ID"""
    result = await db.execute(select(WorkCenter).where(WorkCenter.id == work_center_id))
    work_center = result.scalar_one_or_none()

    if not work_center:
        raise HTTPException(status_code=404, detail="Work center not found")

    return work_center


@router.post("/work-centers/", response_model=WorkCenterSchema)
async def create_work_center(
    work_center: WorkCenterCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:create")),
):
    """Create a new work center"""
    import uuid

    db_work_center = WorkCenter(
        id=uuid.uuid7(),
        code=work_center.code,
        name=work_center.name,
        type=work_center.type,
        capacity=work_center.capacity,
        is_active=work_center.is_active,
    )
    db.add(db_work_center)
    await db.commit()
    await db.refresh(db_work_center)

    return db_work_center


# BOM endpoints
@router.get("/boms/", response_model=list[BOMSchema])
async def get_boms(
    is_active: bool | None = Query(None, description="Filter by active status"),
    product_id: UUID | None = Query(None, description="Filter by product ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:read")),
):
    """Get BOMs with optional filtering"""
    query = select(BOM)

    if is_active is not None:
        query = query.where(BOM.is_active == is_active)
    if product_id:
        query = query.where(BOM.product_id == product_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/boms/", response_model=BOMSchema)
async def create_bom(
    bom: BOMCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:create")),
):
    """Create a new BOM"""
    import uuid

    db_bom = BOM(
        id=uuid.uuid7(),
        product_id=bom.product_id,
        bom_name=bom.bom_name,
        version=bom.version,
        is_active=bom.is_active,
    )
    db.add(db_bom)
    await db.commit()
    await db.refresh(db_bom)

    return db_bom


# Production Order endpoints
@router.get("/production-orders/", response_model=list[ProductionOrderSchema])
async def get_production_orders(
    status: str | None = Query(None, description="Filter by status"),
    work_center_id: UUID | None = Query(None, description="Filter by work center ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:read")),
):
    """Get production orders with optional filtering"""
    query = select(ProductionOrder)

    if status:
        query = query.where(ProductionOrder.status == status)
    if work_center_id:
        query = query.where(ProductionOrder.work_center_id == work_center_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/production-orders/", response_model=ProductionOrderSchema)
async def create_production_order(
    production_order: ProductionOrderSchema,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("production:create")),
):
    """Create a new production order"""
    import uuid

    db_production_order = ProductionOrder(
        id=uuid.uuid7(),
        order_number=production_order.order_number,
        bom_id=production_order.bom_id,
        work_center_id=production_order.work_center_id,
        planned_quantity=production_order.planned_quantity,
        status=production_order.status,
        planned_start_date=production_order.planned_start_date,
        planned_end_date=production_order.planned_end_date,
    )
    db.add(db_production_order)
    await db.commit()
    await db.refresh(db_production_order)

    return db_production_order
