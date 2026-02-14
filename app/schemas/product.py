import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProductCategory


class ProductBase(BaseModel):
    """Base schema untuk Product"""

    sku: str = Field(..., min_length=1, max_length=50, description="Stock Keeping Unit")
    name: str = Field(..., min_length=1, max_length=255, description="Nama produk")
    category: ProductCategory = Field(..., description="Kategori produk")
    uom: str = Field(
        ..., min_length=1, max_length=20, description="Unit of Measure (pcs, kg, m, dll)"
    )
    supplier_id: uuid.UUID | None = Field(None, description="ID supplier (jika ada)")
    customer_id: uuid.UUID | None = Field(None, description="ID customer (jika ada)")
    meta_data: dict = Field(default_factory=dict, description="Metadata tambahan dalam JSON")


class ProductCreate(ProductBase):
    """Schema untuk membuat Product baru"""

    pass


class ProductUpdate(BaseModel):
    """Schema untuk update Product (semua field optional)"""

    sku: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=255)
    category: ProductCategory | None = None
    uom: str | None = Field(None, min_length=1, max_length=20)
    supplier_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    meta_data: dict | None = None


class ProductResponse(ProductBase):
    """Schema untuk response Product (include ID dan timestamps)"""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListItem(BaseModel):
    """Schema simplified untuk list products"""

    id: uuid.UUID
    sku: str
    name: str
    category: ProductCategory
    uom: str

    model_config = ConfigDict(from_attributes=True)
