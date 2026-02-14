"""Sales management API endpoints"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import require_permissions
from app.models import Customer, Product, SalesOrder, SalesOrderItem, User
from app.schemas.sales import (
    SalesOrderCreate,
    SalesOrderList,
    SalesOrderRead,
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/orders", response_model=SalesOrderList)
async def get_sales_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    customer_id: UUID | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("sales:read")),
) -> SalesOrderList:
    """Get list of sales orders with pagination and filters"""
    query = select(SalesOrder).options(
        selectinload(SalesOrder.items).selectinload(SalesOrderItem.product),
        selectinload(SalesOrder.customer),
    )

    # Apply filters
    if customer_id:
        query = query.where(SalesOrder.customer_id == customer_id)
    if status:
        query = query.where(SalesOrder.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    orders = (await db.scalars(query)).all()

    return SalesOrderList(
        sales_orders=[SalesOrderRead.model_validate(order) for order in orders],
        total=total or 0,
        page=page,
        size=size,
    )


@router.get("/orders/{order_id}", response_model=SalesOrderRead)
async def get_sales_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("sales:read")),
) -> SalesOrder:
    """Get a specific sales order by ID"""
    stmt = (
        select(SalesOrder)
        .options(
            selectinload(SalesOrder.items).selectinload(SalesOrderItem.product),
            selectinload(SalesOrder.customer),
        )
        .where(SalesOrder.id == order_id)
    )
    order = (await db.scalars(stmt)).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")

    return order


@router.post("/orders", response_model=SalesOrderRead, status_code=status.HTTP_201_CREATED)
async def create_sales_order(
    order_data: SalesOrderCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("sales:create")),
) -> SalesOrder:
    """Create a new sales order"""
    import uuid

    # Verify customer exists
    customer = await db.get(Customer, order_data.customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Verify all products exist
    product_ids = [item.product_id for item in order_data.items]
    products_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in products_result.scalars().all()}

    if len(products) != len(product_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more products not found")

    # Generate SO number if not provided
    if not order_data.so_number:
        last_so = await db.execute(select(SalesOrder).order_by(SalesOrder.so_number.desc()).limit(1))
        last_so_number = last_so.scalar_one_or_none()
        if last_so_number and last_so_number.so_number:
            try:
                last_num = int(last_so_number.so_number.replace("SO", ""))
                new_so_number = f"SO{last_num + 1:06d}"
            except ValueError:
                new_so_number = "SO000001"
        else:
            new_so_number = "SO000001"
    else:
        new_so_number = order_data.so_number

    # Create sales order
    db_order = SalesOrder(
        id=uuid.uuid4(),
        so_number=new_so_number,
        customer_id=order_data.customer_id,
        status=order_data.status or "draft",
        order_date=order_data.order_date,
        expected_date=order_data.expected_date,
        notes=order_data.notes,
    )

    # Add items
    total_amount = Decimal("0")
    for item_data in order_data.items:
        products[item_data.product_id]
        item_total = item_data.quantity * item_data.unit_price
        total_amount += item_total

        db_item = SalesOrderItem(
            id=uuid.uuid4(),
            so_id=db_order.id,
            product_id=item_data.product_id,
            qty_ordered=item_data.quantity,
            unit_price=item_data.unit_price,
            notes=item_data.notes,
        )
        db_order.items.append(db_item)

    db_order.total_amount = total_amount
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)

    return db_order


@router.get("/customers", response_model=list[dict])
async def get_customers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("sales:read")),
) -> list[dict]:
    """Get list of all customers for dropdown"""
    from app.models.master_data import Customer

    customers = await db.execute(select(Customer).where(Customer.is_active).order_by(Customer.name))
    return [{"id": str(c.id), "code": c.code, "name": c.name} for c in customers.scalars().all()]


@router.get("/products", response_model=list[dict])
async def get_products(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("sales:read")),
) -> list[dict]:
    """Get list of all products for dropdown"""
    query = select(Product).where(Product.is_active)
    if category:
        query = query.where(Product.category == category)

    products = await db.execute(query.order_by(Product.name))
    return [
        {
            "id": str(p.id),
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "unit_price": float(p.unit_price),
        }
        for p in products.scalars().all()
    ]
