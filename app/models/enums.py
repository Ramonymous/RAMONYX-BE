import enum


class LocationType(enum.Enum):
    WAREHOUSE = "warehouse"
    PRODUCTION_FLOOR = "production_floor"
    SUBCONTRACT = "subcontract"
    TRANSIT = "transit"


class ProductCategory(enum.Enum):
    MATERIAL = "material"
    PARTS = "parts"
    WIP = "wip"
    FINISHED_GOOD = "finished_good"


class WorkCenterType(enum.Enum):
    INTERNAL = "internal"
    SUBCONTRACT = "subcontract"


class BOMItemType(enum.Enum):
    MATERIAL = "material"
    OPERATION = "operation"


class POStatus(enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class SOStatus(enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class ProductionStatus(enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransactionType(enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    PRODUCTION = "production"
    RETURN = "return"


class RefType(enum.Enum):
    PURCHASE_ORDER_ITEM = "purchase_order_item"
    SALES_ORDER_ITEM = "sales_order_item"
    PRODUCTION_ORDER = "production_order"
    ADJUSTMENT = "adjustment"
