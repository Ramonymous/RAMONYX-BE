"""Inventory management API endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permissions
from app.models import User
from app.models.inventory import Location, Product, StockBalance, StockLedger
from app.schemas.inventory import (
    InventoryReport,
    InventorySummary,
    StockBalance as StockBalanceSchema,
    StockLedger as StockLedgerSchema,
    StockLedgerCreate,
    StockMovementRequest,
    StockMovementResponse,
)

router = APIRouter()


@router.get("/stock-balances/", response_model=list[StockBalanceSchema])
async def get_stock_balances(
    product_id: UUID | None = Query(None, description="Filter by product ID"),
    location_id: UUID | None = Query(None, description="Filter by location ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("inventory:read")),
) -> list[StockBalanceSchema]:
    """Get stock balances with optional filtering"""
    query = select(StockBalance)

    if product_id:
        query = query.where(StockBalance.product_id == product_id)
    if location_id:
        query = query.where(StockBalance.location_id == location_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    balances = result.scalars().all()
    return [StockBalanceSchema.model_validate(balance) for balance in balances]


@router.get("/stock-ledgers/", response_model=list[StockLedgerSchema])
async def get_stock_ledgers(
    product_id: UUID | None = Query(None, description="Filter by product ID"),
    location_id: UUID | None = Query(None, description="Filter by location ID"),
    transaction_type: str | None = Query(None, description="Filter by transaction type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("inventory:read")),
):
    """Get stock ledger entries with optional filtering"""
    query = select(StockLedger)

    if product_id:
        query = query.where(StockLedger.product_id == product_id)
    if location_id:
        query = query.where(StockLedger.location_id == location_id)
    if transaction_type:
        query = query.where(StockLedger.transaction_type == transaction_type)

    query = query.order_by(StockLedger.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/stock-ledgers/", response_model=StockLedgerSchema)
async def create_stock_ledger(
    ledger: StockLedgerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("inventory:create")),
):
    """Create a new stock ledger entry (trigger will update balance)"""
    ledger_data = ledger.model_dump(exclude={"notes"})
    db_ledger = StockLedger(**ledger_data)
    db.add(db_ledger)
    await db.commit()
    await db.refresh(db_ledger)

    return db_ledger


@router.post("/stock-movements/", response_model=StockMovementResponse)
async def create_stock_movement(
    movement: StockMovementRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("inventory:create")),
):
    """Create stock movement (transfer between locations)"""
    import uuid

    try:
        # Create ledger entries
        ledger_entries = []

        # If this is a transfer from one location to another
        if movement.from_location_id:
            # Create OUT entry
            out_ledger = StockLedger(
                id=uuid.uuid4(),
                product_id=movement.product_id,
                location_id=movement.from_location_id,
                transaction_type="OUT",
                quantity=-movement.quantity,
                reference_type="STOCK_MOVEMENT",
                reference_id=str(uuid.uuid4()),
                notes=f"Transfer to location {movement.to_location_id}",
            )
            ledger_entries.append(out_ledger)

        # Create IN entry
        in_ledger = StockLedger(
            id=uuid.uuid4(),
            product_id=movement.product_id,
            location_id=movement.to_location_id,
            transaction_type="IN",
            quantity=movement.quantity,
            reference_type="STOCK_MOVEMENT",
            reference_id=str(uuid.uuid4()),
            notes=f"Transfer from location {movement.from_location_id}" if movement.from_location_id else "Stock in",
        )
        ledger_entries.append(in_ledger)

        # Save all ledger entries
        for ledger in ledger_entries:
            db.add(ledger)

        await db.commit()

        return {
            "success": True,
            "message": f"Stock movement completed: {movement.quantity} units",
            "movement_id": str(uuid.uuid4()),
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Stock movement failed: {str(e)}")


@router.get("/reports/inventory/", response_model=InventorySummary)
async def get_inventory_report(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("inventory:read")),
):
    """Get comprehensive inventory report"""

    # Get inventory data with product and location info
    query = (
        select(
            StockBalance,
            Product.sku,
            Product.name,
            Location.name,
        )
        .join(Product, StockBalance.product_id == Product.id)
        .join(Location, StockBalance.location_id == Location.id)
    )

    result = await db.execute(query)
    inventory_data = result.all()

    # Calculate summary
    total_products = len(set(item[0].product_id for item in inventory_data))
    total_locations = len(set(item[0].location_id for item in inventory_data))
    total_value = sum(item[0].current_qty for item in inventory_data)

    low_stock_items = [item for item in inventory_data if item[0].current_qty < 10]
    out_of_stock_items = [item for item in inventory_data if item[0].current_qty == 0]

    report_data = [
        InventoryReport(
            product_id=item[0].product_id,
            product_sku=item[1],
            product_name=item[2],
            location_id=item[0].location_id,
            location_name=item[3],
            current_qty=item[0].current_qty,
            last_updated=item[0].last_updated,
            total_value=item[0].current_qty * 100.0,  # Assuming unit price of 100
        )
        for item in inventory_data
    ]

    return InventorySummary(
        total_products=total_products,
        total_locations=total_locations,
        total_stock_value=total_value,
        low_stock_items=len(low_stock_items),
        out_of_stock_items=len(out_of_stock_items),
        report_data=report_data,
    )


@router.get("/reports/low-stock/", response_model=list[InventoryReport])
async def get_low_stock_report(
    threshold: int = Query(10, ge=0, description="Low stock threshold"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("inventory:read")),
):
    """Get low stock items report"""
    query = (
        select(
            StockBalance,
            Product.sku,
            Product.name,
            Location.name,
        )
        .join(Product, StockBalance.product_id == Product.id)
        .join(Location, StockBalance.location_id == Location.id)
        .where(StockBalance.current_qty <= threshold)
        .order_by(StockBalance.current_qty.asc())
    )

    result = await db.execute(query)
    low_stock_items = result.all()

    return [
        InventoryReport(
            product_id=item[0].product_id,
            product_sku=item[1],
            product_name=item[2],
            location_id=item[0].location_id,
            location_name=item[3],
            current_qty=item[0].current_qty,
            last_updated=item[0].last_updated,
            total_value=item[0].current_qty * 100.0,  # Assuming unit price of 100
        )
        for item in low_stock_items
    ]
