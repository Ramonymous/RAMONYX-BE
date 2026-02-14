import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permissions
from app.models import Product, ProductCategory, User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("products:create")),
) -> Product:
    """
    Membuat product baru.

    - **sku**: Kode SKU unik
    - **name**: Nama produk
    - **category**: Kategori (material, parts, wip, finished_good)
    - **uom**: Unit of measure (pcs, kg, m, dll)
    """
    # Check jika SKU sudah ada
    existing = await db.scalar(select(Product).where(Product.sku == product.sku))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product.sku}' already exists",
        )

    # Create product
    db_product = Product(
        sku=product.sku,
        name=product.name,
        category=product.category,
        uom=product.uom,
        supplier_id=product.supplier_id,
        customer_id=product.customer_id,
        meta_data=product.meta_data or {},
    )

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category: ProductCategory | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("products:read")),
) -> list[Product]:
    """
    List semua products dengan pagination dan filter.

    - **skip**: Offset untuk pagination
    - **limit**: Limit jumlah hasil (max 100)
    - **category**: Filter by category (optional)
    """
    stmt = select(Product)

    if category:
        stmt = stmt.where(Product.category == category)

    stmt = stmt.offset(skip).limit(min(limit, 100))
    products = (await db.scalars(stmt)).all()
    return list(products)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("products:read")),
) -> Product:
    """
    Get detail product by ID.
    """
    product = await db.scalar(select(Product).where(Product.id == product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found",
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("products:update")),
) -> Product:
    """
    Update product.
    """
    product = await db.scalar(select(Product).where(Product.id == product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found",
        )

    # Update fields yang diberikan
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("products:delete")),
) -> None:
    """
    Delete product.

    Note: Akan gagal jika product masih digunakan di BOM, PO, atau SO
    karena foreign key constraint RESTRICT.
    """
    product = await db.scalar(select(Product).where(Product.id == product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found",
        )

    try:
        await db.delete(product)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Cannot delete product: {str(e)}"
        )
