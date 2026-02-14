import asyncio

from sqlalchemy import text

from app.database import SessionLocal


async def clean_database() -> None:
    async with SessionLocal() as db:
        await db.execute(
            text("""
            TRUNCATE TABLE
                production_orders,
                sales_order_items,
                sales_orders,
                purchase_order_items,
                purchase_orders,
                stock_ledgers,
                stock_balances,
                bom_items,
                boms,
                products,
                locations,
                customers,
                suppliers
            CASCADE
        """)
        )
        await db.commit()
        print("Database cleaned successfully!")


if __name__ == "__main__":
    asyncio.run(clean_database())
