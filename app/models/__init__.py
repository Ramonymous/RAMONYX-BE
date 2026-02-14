"""
Models package untuk ERP backend.
Mengumpulkan semua models dari sub-modules.
"""

# Import Base terlebih dahulu
# Import Auth models
from .auth import Permission, Role, User, role_permissions, user_roles
from .base import Base, TimestampMixin

# Import Enums
from .enums import (
    BOMItemType,
    LocationType,
    POStatus,
    ProductCategory,
    ProductionStatus,
    RefType,
    SOStatus,
    TransactionType,
    WorkCenterType,
)

# Import Inventory models
from .inventory import Location, Product, StockBalance, StockLedger

# Import Master Data
from .master_data import Customer, Supplier

# Import Production models
from .production import BOM, BOMItem, ProductionOrder, WorkCenter

# Import Purchasing models
from .purchasing import PurchaseOrder, PurchaseOrderItem

# Import Sales models
from .sales import SalesOrder, SalesOrderItem

# Export semua untuk memudahkan import
__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Enums
    "LocationType",
    "ProductCategory",
    "WorkCenterType",
    "BOMItemType",
    "POStatus",
    "SOStatus",
    "ProductionStatus",
    "TransactionType",
    "RefType",
    # Auth
    "Permission",
    "Role",
    "User",
    "user_roles",
    "role_permissions",
    # Master Data
    "Supplier",
    "Customer",
    # Inventory
    "Location",
    "Product",
    "StockLedger",
    "StockBalance",
    # Production
    "WorkCenter",
    "BOM",
    "BOMItem",
    "ProductionOrder",
    # Purchasing
    "PurchaseOrder",
    "PurchaseOrderItem",
    # Sales
    "SalesOrder",
    "SalesOrderItem",
]
