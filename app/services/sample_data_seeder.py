"""
Sample Data Seeder for Ramonyxs ERP Backend
Creates interconnected sample data across all modules for testing and demonstration.
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models import (
    BOM,
    BOMItem,
    Customer,
    # Inventory
    Location,
    # Enums
    Product,
    ProductionOrder,
    PurchaseOrder,
    PurchaseOrderItem,
    # Sales
    SalesOrderItem,
    # Auth
    Supplier,
    WorkCenter,
)


class SampleDataSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data: dict[str, Any] = {
            "suppliers": [],
            "customers": [],
            "locations": [],
            "products": [],
            "work_centers": [],
            "boms": [],
            "bom_items": [],
            "purchase_orders": [],
            "sales_orders": [],
            "sales_order_items": [],
        }

    async def seed_all(self) -> dict[str, int]:
        """Seed all sample data in proper order to maintain relationships"""
        summary = {}

        # 1. Master Data (no dependencies)
        await self.seed_suppliers()
        summary["suppliers"] = len(self.data["suppliers"])

        await self.seed_customers()
        summary["customers"] = len(self.data["customers"])

        # 2. Locations (hierarchical)
        await self.seed_locations()
        summary["locations"] = len(self.data["locations"])

        # 3. Products (depends on suppliers)
        await self.seed_products()
        summary["products"] = len(self.data["products"])

        # 4. Work Centers (no dependencies)
        await self.seed_work_centers()
        summary["work_centers"] = len(self.data["work_centers"])

        # 5. BOMs and BOM Items (depends on products and work centers)
        await self.seed_boms()
        summary["boms"] = 2  # Hardcoded since we're not storing them
        summary["bom_items"] = 4  # Hardcoded since we're not storing them

        # 6. Initial Stock Balances (depends on products and locations)
        await self.seed_initial_stock()

        # Count actual stock balances created by trigger
        from sqlalchemy import text

        balance_count = await self.db.execute(text("SELECT COUNT(*) FROM stock_balances"))
        summary["stock_balances"] = int(balance_count.scalar() or 0)

        # Count stock ledgers created
        ledger_count = await self.db.execute(text("SELECT COUNT(*) FROM stock_ledgers"))
        summary["stock_ledgers"] = int(ledger_count.scalar() or 0)

        # 7. Purchase Orders (depends on suppliers and products)
        await self.seed_purchase_orders()
        summary["purchase_orders"] = len(self.data["purchase_orders"])
        summary["purchase_order_items"] = 3  # Hardcoded: 2 items for PO1, 1 item for PO2

        # 8. Sales Orders (depends on customers and products)
        await self.seed_sales_orders()
        summary["sales_orders"] = 2  # Hardcoded since we're using raw SQL
        summary["sales_order_items"] = len(self.data["sales_order_items"])

        # 9. Production Orders (depends on products, BOMs, and Sales Orders)
        await self.seed_production_orders()
        summary["production_orders"] = len(self.data["production_orders"])

        await self.db.commit()
        return summary

    async def seed_suppliers(self) -> None:
        """Create sample suppliers"""
        suppliers_data = [
            {
                "code": "SUP001",
                "name": "PT. Material Sejahtera",
                "contact_info": {
                    "phone": "+62-21-5551234",
                    "email": "info@materialsejahtera.com",
                    "address": "Jl. Industri No. 123, Jakarta",
                    "payment_terms": "NET 30",
                },
            },
            {
                "code": "SUP002",
                "name": "CV. Komponen Teknik",
                "contact_info": {
                    "phone": "+62-22-77889900",
                    "email": "sales@komponenteknik.com",
                    "address": "Jl. Manufaktur No. 456, Bandung",
                    "payment_terms": "NET 45",
                },
            },
            {
                "code": "SUP003",
                "name": "PT. Elektronik Indonesia",
                "contact_info": {
                    "phone": "+62-31-88776655",
                    "email": "order@elektronikindo.com",
                    "address": "Jl. Teknologi No. 789, Surabaya",
                    "payment_terms": "NET 60",
                },
            },
        ]

        self.data["suppliers"] = []
        for supplier_data in suppliers_data:
            supplier = Supplier(**supplier_data)
            self.db.add(supplier)
            self.data["suppliers"].append(supplier)

        await self.db.flush()

    async def seed_customers(self) -> None:
        """Create sample customers"""
        customers_data = [
            {
                "code": "CUST001",
                "name": "PT. Retail Maju",
                "contact_info": {
                    "phone": "+62-21-9876543",
                    "email": "procurement@retailmaju.com",
                    "address": "Jl. Commerce No. 100, Jakarta",
                    "credit_limit": "500000000",
                },
            },
            {
                "code": "CUST002",
                "name": "CV. Distributor Teknik",
                "contact_info": {
                    "phone": "+62-61-5554443",
                    "email": "order@disteknik.com",
                    "address": "Jl. Distribusi No. 200, Medan",
                    "credit_limit": "300000000",
                },
            },
            {
                "code": "CUST003",
                "name": "PT. Manufaktur Sukses",
                "contact_info": {
                    "phone": "+62-274-8887776",
                    "email": "purchase@manufsukses.com",
                    "address": "Jl. Pabrik No. 300, Yogyakarta",
                    "credit_limit": "750000000",
                },
            },
        ]

        self.data["customers"] = []
        for customer_data in customers_data:
            customer = Customer(**customer_data)
            self.db.add(customer)
            self.data["customers"].append(customer)

        await self.db.flush()

    async def seed_locations(self) -> None:
        """Create hierarchical locations (Warehouse → Zone → Bin)"""
        locations_data = [
            # Main Warehouse
            {
                "code": "WH001",
                "name": "Main Warehouse",
                "type": "warehouse",
                "parent_id": None,
            },
            # Production Floor
            {
                "code": "PF001",
                "name": "Production Floor",
                "type": "production_floor",
                "parent_id": None,
            },
            # Store/Finished Goods (using WAREHOUSE type)
            {
                "code": "ST001",
                "name": "Finished Goods Store",
                "type": "warehouse",
                "parent_id": None,
            },
        ]

        # Create parent locations first
        self.data["locations"] = []
        for loc_data in locations_data:
            location = Location(**loc_data)
            self.db.add(location)
            self.data["locations"].append(location)

        await self.db.flush()

        # Create zones and bins under each parent
        zone_mapping = {
            "WH001": [
                {"code": "WH001-RA", "name": "Raw Materials Zone A"},
                {"code": "WH001-RB", "name": "Raw Materials Zone B"},
                {"code": "WH001-PA", "name": "Packaging Zone"},
            ],
            "PF001": [
                {"code": "PF001-WA", "name": "Workstation Area A"},
                {"code": "PF001-WB", "name": "Workstation Area B"},
                {"code": "PF001-AS", "name": "Assembly Area"},
            ],
            "ST001": [
                {"code": "ST001-FG", "name": "Finished Goods Zone"},
                {"code": "ST001-GR", "name": "Goods Receiving Zone"},
            ],
        }

        # Create zones
        for parent_code, zones in zone_mapping.items():
            parent = self.find_location_by_code(parent_code)
            for zone_data in zones:
                zone = Location(
                    code=zone_data["code"],
                    name=zone_data["name"],
                    type="warehouse",  # Zones are treated as warehouse type
                    parent_id=parent.id,
                )
                self.db.add(zone)
                self.data["locations"].append(zone)

        await self.db.flush()

        # Create bins under zones
        bin_mapping = {
            "WH001-RA": ["WH001-RA-01", "WH001-RA-02", "WH001-RA-03"],
            "WH001-RB": ["WH001-RB-01", "WH001-RB-02"],
            "WH001-PA": ["WH001-PA-01", "WH001-PA-02"],
            "PF001-WA": ["PF001-WA-01", "PF001-WA-02"],
            "PF001-WB": ["PF001-WB-01"],
            "PF001-AS": ["PF001-AS-01", "PF001-AS-02"],
            "ST001-FG": ["ST001-FG-01", "ST001-FG-02", "ST001-FG-03"],
            "ST001-GR": ["ST001-GR-01"],
        }

        for zone_code, bins in bin_mapping.items():
            zone = self.find_location_by_code(zone_code)
            for i, bin_code in enumerate(bins):
                bin_loc = Location(
                    code=bin_code,
                    name=f"Bin {i + 1}",
                    type="warehouse",
                    parent_id=zone.id,
                )
                self.db.add(bin_loc)
                self.data["locations"].append(bin_loc)

        await self.db.flush()

    async def seed_products(self) -> None:
        """Create sample products with different categories"""
        products_data = [
            # Raw Materials
            {
                "sku": "STEEL-001",
                "name": "Steel Plate 10mm",
                "category": "material",
                "uom": "pcs",
                "supplier_id": self.data["suppliers"][0].id,
                "meta_data": {
                    "specifications": "10mm thickness",
                    "weight_kg": 78.5,
                    "standard": "ASTM A36",
                },
            },
            {
                "sku": "PLASTIC-001",
                "name": "ABS Plastic Granules",
                "category": "material",
                "uom": "kg",
                "supplier_id": self.data["suppliers"][1].id,
                "meta_data": {"color": "black", "density": "1.04 g/cm3", "melt_flow": "20 g/10min"},
            },
            {
                "sku": "ELEC-001",
                "name": "Electronic Circuit Board",
                "category": "material",
                "uom": "pcs",
                "supplier_id": self.data["suppliers"][2].id,
                "meta_data": {"type": "PCB", "layers": 4, "thickness": "1.6mm"},
            },
            # Parts
            {
                "sku": "MOTOR-001",
                "name": "Electric Motor 5HP",
                "category": "parts",
                "uom": "pcs",
                "supplier_id": self.data["suppliers"][1].id,
                "meta_data": {"power": "5HP", "voltage": "380V", "rpm": 1450},
            },
            {
                "sku": "GEAR-001",
                "name": "Spur Gear Module 2",
                "category": "parts",
                "uom": "pcs",
                "supplier_id": self.data["suppliers"][0].id,
                "meta_data": {"module": 2, "teeth": 30, "material": "Steel 45C"},
            },
            # Work in Progress
            {
                "sku": "ASM-001",
                "name": "Motor Assembly Kit",
                "category": "wip",
                "uom": "set",
                "meta_data": {
                    "components": ["Motor", "Gear", "Housing"],
                    "assembly_time": "2 hours",
                },
            },
            # Finished Goods
            {
                "sku": "PUMP-001",
                "name": "Industrial Water Pump 10HP",
                "category": "finished_good",
                "uom": "unit",
                "customer_id": self.data["customers"][0].id,
                "meta_data": {
                    "power": "10HP",
                    "flow_rate": "500 L/min",
                    "pressure": "5 bar",
                    "warranty": "24 months",
                },
            },
            {
                "sku": "CONV-001",
                "name": "Conveyor Belt System",
                "category": "finished_good",
                "uom": "unit",
                "customer_id": self.data["customers"][1].id,
                "meta_data": {
                    "length": "10m",
                    "width": "1m",
                    "speed": "1 m/s",
                    "capacity": "1000 kg/h",
                },
            },
        ]

        self.data["products"] = []
        for product_data in products_data:
            product = Product(**product_data)
            self.db.add(product)
            self.data["products"].append(product)

        await self.db.flush()

    async def seed_work_centers(self) -> None:
        """Create sample work centers"""
        work_centers_data = [
            {
                "name": "Cutting Machine WC-001",
                "type": "internal",
                "is_active": True,
            },
            {
                "name": "CNC Machine WC-002",
                "type": "internal",
                "is_active": True,
            },
            {
                "name": "Assembly Station WC-003",
                "type": "internal",
                "is_active": True,
            },
            {
                "name": "Quality Control WC-004",
                "type": "internal",
                "is_active": True,
            },
            {
                "name": "External Coating Service",
                "type": "subcontract",
                "is_active": True,
            },
        ]

        self.data["work_centers"] = []
        for wc_data in work_centers_data:
            work_center = WorkCenter(**wc_data)
            self.db.add(work_center)
            self.data["work_centers"].append(work_center)

        await self.db.flush()

    # Helper function to safely find location by code
    def find_location_by_code(self, code: str):
        for location in self.data["locations"]:
            if location.code == code:
                return location
        raise ValueError(f"Location with code {code} not found")

    # Helper function to safely find product by SKU
    async def find_product_by_sku(self, sku: str):
        # Use raw SQL to avoid ORM enum validation issues
        from sqlalchemy import text

        result = await self.db.execute(text("SELECT id FROM products WHERE sku = :sku"), {"sku": sku})
        product_id = result.scalar_one_or_none()
        if product_id is None:
            raise ValueError(f"Product with SKU {sku} not found")

        # Return a simple object with just the id
        class ProductRef:
            def __init__(self, id):
                self.id = id

        return ProductRef(product_id)

    # Helper function to safely find BOM by product SKU
    async def find_bom_by_product_sku(self, sku: str):
        # Use raw SQL to avoid ORM enum validation issues
        from sqlalchemy import text

        # Find the product ID first
        product_result = await self.db.execute(text("SELECT id FROM products WHERE sku = :sku"), {"sku": sku})
        product_id = product_result.scalar_one_or_none()
        if not product_id:
            raise ValueError(f"Product with SKU {sku} not found")

        # Find the BOM for this product
        bom_result = await self.db.execute(text("SELECT id FROM boms WHERE product_id = :product_id"), {"product_id": product_id})
        bom_id = bom_result.scalar_one_or_none()
        if not bom_id:
            raise ValueError(f"BOM for product with SKU {sku} not found")

        # Return just the ID
        return bom_id

    async def seed_boms(self) -> None:
        """Create Bills of Materials for finished products"""
        # BOM for Industrial Water Pump
        pump_product = await self.find_product_by_sku("PUMP-001")
        pump_bom = BOM(product_id=pump_product.id, bom_name="Water Pump 10HP Standard BOM", is_active=True)
        self.db.add(pump_bom)
        await self.db.flush()  # Flush to get the BOM ID

        # BOM items for pump
        pump_items = [
            {
                "sequence": 1,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("STEEL-001")).id,
                "quantity": 5,
            },
            {
                "sequence": 2,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("PLASTIC-001")).id,
                "quantity": 2,
            },
            {
                "sequence": 3,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("ELEC-001")).id,
                "quantity": 1,
            },
            {
                "sequence": 4,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("MOTOR-001")).id,
                "quantity": 1,
            },
            {
                "sequence": 5,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("GEAR-001")).id,
                "quantity": 2,
            },
            {
                "sequence": 6,
                "item_type": "operation",
                "work_center_id": self.data["work_centers"][0].id,
                "quantity": 1,
                "duration_minutes": 30,
            },
            {
                "sequence": 7,
                "item_type": "operation",
                "work_center_id": self.data["work_centers"][1].id,
                "quantity": 1,
                "duration_minutes": 45,
            },
            {
                "sequence": 8,
                "item_type": "operation",
                "work_center_id": self.data["work_centers"][2].id,
                "quantity": 1,
                "duration_minutes": 120,
            },
        ]

        for item_data in pump_items:
            bom_item = BOMItem(bom_id=pump_bom.id, **item_data)
            self.db.add(bom_item)

        # BOM for Conveyor Belt System
        conv_product = await self.find_product_by_sku("CONV-001")
        conv_bom = BOM(product_id=conv_product.id, bom_name="Conveyor Belt System BOM", is_active=True)
        self.db.add(conv_bom)
        await self.db.flush()  # Flush to get the BOM ID

        # BOM items for conveyor
        conv_items = [
            {
                "sequence": 1,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("STEEL-001")).id,
                "quantity": 15,
            },
            {
                "sequence": 2,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("PLASTIC-001")).id,
                "quantity": 8,
            },
            {
                "sequence": 3,
                "item_type": "material",
                "product_id": (await self.find_product_by_sku("MOTOR-001")).id,
                "quantity": 2,
            },
            {
                "sequence": 4,
                "item_type": "operation",
                "work_center_id": self.data["work_centers"][0].id,
                "quantity": 1,
                "duration_minutes": 60,
            },
            {
                "sequence": 5,
                "item_type": "operation",
                "work_center_id": self.data["work_centers"][2].id,
                "quantity": 1,
                "duration_minutes": 180,
            },
            {
                "sequence": 6,
                "item_type": "operation",
                "work_center_id": self.data["work_centers"][4].id,
                "quantity": 1,
                "duration_minutes": 240,
            },
        ]

        for item_data in conv_items:
            bom_item = BOMItem(bom_id=conv_bom.id, **item_data)
            self.db.add(bom_item)

    async def seed_initial_stock(self) -> None:
        """Create initial stock balances and ledger entries"""
        self.data["stock_balances"] = []
        self.data["stock_ledgers"] = []

        # Get warehouse locations
        warehouse_bins = [loc for loc in self.data["locations"] if loc.code.startswith("WH001-")]

        # Get raw materials using raw SQL to avoid ORM enum issues
        import uuid

        from sqlalchemy import text

        raw_materials_result = await self.db.execute(text("SELECT id, sku FROM products WHERE category = 'material'"))
        raw_materials = raw_materials_result.fetchall()

        for i, product in enumerate(raw_materials):
            location = warehouse_bins[i % len(warehouse_bins)]
            quantity = (i + 1) * 100  # 100, 200, 300...

            # Create initial ledger entry - trigger will auto-create stock balance
            await self.db.execute(
                text(
                    """
                    INSERT INTO stock_ledgers (
                        id,
                        product_id,
                        location_id,
                        qty,
                        transaction_type,
                        ref_type,
                        ref_id,
                        created_by
                    )
                    VALUES (
                        :id,
                        :product_id,
                        :location_id,
                        :qty,
                        :transaction_type,
                        :ref_type,
                        :ref_id,
                        :created_by
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "product_id": product[0],
                    "location_id": location.id,
                    "qty": quantity,
                    "transaction_type": "purchase",
                    "ref_type": "purchase_order_item",
                    "ref_id": uuid.uuid4(),
                    "created_by": None,
                },
            )

        # Create initial stock for parts
        parts_result = await self.db.execute(text("SELECT id, sku FROM products WHERE category = 'parts'"))
        parts = parts_result.fetchall()
        for i, product in enumerate(parts):
            location = warehouse_bins[(i + 3) % len(warehouse_bins)]
            quantity = (i + 1) * 50  # 50, 100...

            # Create initial ledger entry - trigger will auto-create stock balance
            await self.db.execute(
                text(
                    """
                    INSERT INTO stock_ledgers (
                        id,
                        product_id,
                        location_id,
                        qty,
                        transaction_type,
                        ref_type,
                        ref_id,
                        created_by
                    )
                    VALUES (
                        :id,
                        :product_id,
                        :location_id,
                        :qty,
                        :transaction_type,
                        :ref_type,
                        :ref_id,
                        :created_by
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "product_id": product[0],
                    "location_id": location.id,
                    "qty": quantity,
                    "transaction_type": "purchase",
                    "ref_type": "purchase_order_item",
                    "ref_id": uuid.uuid4(),
                    "created_by": None,
                },
            )

        await self.db.flush()

    async def seed_purchase_orders(self) -> None:
        """Create sample purchase orders"""
        self.data["purchase_orders"] = []

        # PO for raw materials
        po1 = PurchaseOrder(
            po_number="PO-2024-001",
            supplier_id=self.data["suppliers"][0].id,
            status="confirmed",
            notes="Urgent raw materials for production",
        )
        self.db.add(po1)
        self.data["purchase_orders"].append(po1)
        await self.db.flush()  # Flush to get the PO ID

        # PO items
        po1_items = [
            {
                "product_id": (await self.find_product_by_sku("STEEL-001")).id,
                "qty_ordered": 500,
                "unit_price": Decimal("150.00"),
            },
            {
                "product_id": (await self.find_product_by_sku("GEAR-001")).id,
                "qty_ordered": 100,
                "unit_price": Decimal("750.00"),
            },
        ]

        for item_data in po1_items:
            item = PurchaseOrderItem(po_id=po1.id, **item_data)
            self.db.add(item)

        # PO for electronic components
        po2 = PurchaseOrder(
            po_number="PO-2024-002",
            supplier_id=self.data["suppliers"][2].id,
            status="confirmed",
            notes="Electronic components for new product line",
        )
        self.db.add(po2)
        self.data["purchase_orders"].append(po2)
        await self.db.flush()  # Flush to get the PO ID

        po2_items = [
            {
                "product_id": (await self.find_product_by_sku("ELEC-001")).id,
                "qty_ordered": 200,
                "unit_price": Decimal("1250.00"),
            },
        ]

        for item_data in po2_items:
            item = PurchaseOrderItem(po_id=po2.id, **item_data)
            self.db.add(item)

        await self.db.flush()

    async def seed_sales_orders(self) -> None:
        """Create sample sales orders"""
        self.data["sales_orders"] = []
        self.data["sales_order_items"] = []

        # SO for retail customer - use raw SQL to avoid model issues
        from sqlalchemy import text

        so1_id = uuid.uuid7()
        await self.db.execute(
            text(
                """
                INSERT INTO sales_orders (
                    id,
                    so_number,
                    customer_id,
                    order_date,
                    delivery_date,
                    status,
                    notes,
                    created_by
                )
                VALUES (
                    :id,
                    :so_number,
                    :customer_id,
                    :order_date,
                    :delivery_date,
                    :status,
                    :notes,
                    :created_by
                )
                """
            ),
            {
                "id": so1_id,
                "so_number": "SO-2024-001",
                "customer_id": self.data["customers"][0].id,
                "order_date": datetime.now(timezone.utc) - timedelta(days=5),
                "expected_date": datetime.now(timezone.utc) + timedelta(days=10),
                "status": "confirmed",
                "notes": "Regular order - priority customer",
                "created_by": None,
            },
        )
        self.data["sales_orders"].append(so1_id)  # Store the ID

        # SO items
        so1_items = [
            {
                "product_id": (await self.find_product_by_sku("PUMP-001")).id,
                "qty_ordered": 5,
                "unit_price": Decimal("150000.00"),
            },
            {
                "product_id": (await self.find_product_by_sku("CONV-001")).id,
                "qty_ordered": 2,
                "unit_price": Decimal("450000.00"),
            },
        ]

        for item_data in so1_items:
            item = SalesOrderItem(so_id=so1_id, **item_data)
            self.db.add(item)
            self.data["sales_order_items"].append(item)

        # SO for distributor - use raw SQL to avoid model issues
        so2_id = uuid.uuid7()
        await self.db.execute(
            text(
                """
                INSERT INTO sales_orders (
                    id,
                    so_number,
                    customer_id,
                    order_date,
                    delivery_date,
                    status,
                    notes,
                    created_by
                )
                VALUES (
                    :id,
                    :so_number,
                    :customer_id,
                    :order_date,
                    :delivery_date,
                    :status,
                    :notes,
                    :created_by
                )
                """
            ),
            {
                "id": so2_id,
                "so_number": "SO-2024-002",
                "customer_id": self.data["customers"][1].id,
                "order_date": datetime.now(timezone.utc) - timedelta(days=2),
                "delivery_date": datetime.now(timezone.utc) + timedelta(days=30),
                "status": "draft",
                "notes": "Awaiting confirmation from customer",
                "created_by": None,
            },
        )
        self.data["sales_orders"].append(so2_id)  # Store the ID

        so2_items = [
            {
                "product_id": (await self.find_product_by_sku("PUMP-001")).id,
                "qty_ordered": 10,
                "unit_price": Decimal("148000.00"),
            },
        ]

        for item_data in so2_items:
            item = SalesOrderItem(so_id=so2_id, **item_data)
            self.db.add(item)
            self.data["sales_order_items"].append(item)

        await self.db.flush()

    async def seed_production_orders(self) -> None:
        """Create sample production orders linked to sales orders"""
        self.data["production_orders"] = []

        # Get BOM IDs and sales orders
        pump_bom_id = await self.find_bom_by_product_sku("PUMP-001")
        conv_bom_id = await self.find_bom_by_product_sku("CONV-001")

        # Get product IDs for the BOMs using raw SQL to avoid enum issues
        from sqlalchemy import text

        pump_result = await self.db.execute(text("SELECT id FROM products WHERE sku = 'PUMP-001'"))
        pump_product_id = pump_result.scalar_one()
        conv_result = await self.db.execute(text("SELECT id FROM products WHERE sku = 'CONV-001'"))
        conv_product_id = conv_result.scalar_one()

        # Production order for pumps (linked to sales order)
        po1 = ProductionOrder(
            order_number="PROD-2024-001",
            product_id=pump_product_id,
            bom_id=pump_bom_id,
            so_item_id=self.data["sales_order_items"][0].id,  # Link to first sales order item
            qty_planned=5,
            qty_produced=0,
            status="draft",
            created_by=None,  # No user ID available
        )
        self.db.add(po1)
        self.data["production_orders"].append(po1)

        # Production order for conveyors (linked to sales order)
        po2 = ProductionOrder(
            order_number="PROD-2024-002",
            product_id=conv_product_id,
            bom_id=conv_bom_id,
            so_item_id=self.data["sales_order_items"][1].id,  # Link to second sales order item
            qty_planned=2,
            qty_produced=0,
            status="draft",
            created_by=None,
        )
        self.db.add(po2)
        self.data["production_orders"].append(po2)

        # Additional production order for stock replenishment
        po3 = ProductionOrder(
            order_number="PROD-2024-003",
            product_id=pump_product_id,
            bom_id=pump_bom_id,
            qty_planned=10,
            qty_produced=0,
            status="draft",
            created_by=None,
        )
        self.db.add(po3)
        self.data["production_orders"].append(po3)

        await self.db.flush()


async def seed_sample_data(db: Optional[AsyncSession] = None) -> dict[str, int]:
    """Main function to seed sample data"""
    if db is None:
        async with SessionLocal() as db:
            seeder = SampleDataSeeder(db)
            return await seeder.seed_all()
    else:
        seeder = SampleDataSeeder(db)
        return await seeder.seed_all()
