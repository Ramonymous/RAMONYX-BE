# ERP Backend API - Development

Backend API untuk sistem ERP dengan fitur lengkap:
- ✅ **Authentication & Authorization** (Users, Roles, Permissions)
- ✅ **Master Data** (Suppliers, Customers, Products, Locations)
- ✅ **Inventory Management** (Stock Balances, Stock Ledgers, Stock Movements)
- ✅ **Production** (BOM, Work Centers, Production Orders)
- ✅ **Purchasing** (Suppliers, Purchase Orders, Receiving)
- ✅ **Sales** (Sales Orders, Sales Order Items)
- ✅ **Warehouse Management** (Location Hierarchy, Tree Structure)
- ✅ **User Management** (RBAC, Role Assignment, Security)
- ✅ **Database Triggers** (Auto Stock Balance, Auto Timestamps)
- ✅ **Comprehensive Reporting** (Analytics, Summaries, Alerts)
- ✅ **75+ API Endpoints** - Complete CRUD operations for all modules
- ✅ **UUID v7** for all primary and foreign keys
- ✅ **Type-safe Data** (Integer quantities, Decimal(15,2) prices)

## 🚀 Quick Start

### Option 1: Simple Install (Recommended for Development)

For a brand new installation, simply run:

```bash
# 1. Clone the repository
git clone <your-repo>
cd backend

# 2. Install dependencies
uv sync

# 3. Setup environment
cp .env.example .env
# Edit .env with your database settings

# 4. Run database migrations
uv run alembic upgrade head

# 5. Seed sample data (optional)
uv run python -c "
import asyncio
from app.services.sample_data_seeder import seed_sample_data
from app.database import SessionLocal
db = SessionLocal()
asyncio.run(seed_sample_data(db))
print('Sample data seeded successfully!')
"

# 6. Start the server
uv run uvicorn app.main:app --reload
```

**What's Included:**
- ✅ **Database Schema** - All tables, indexes, and constraints
- ✅ **Database Triggers** - Auto stock balance & timestamp updates
- ✅ **Sample Data** - Complete test data for development
- ✅ **API Endpoints** - All 75+ endpoints ready to use

### Option 2: Interactive Install (Recommended for Production)

```bash
# 1. Clone the repository
git clone <your-repo>
cd backend

# 2. Install dependencies
uv sync

# 3. Run interactive installation
uv run erp-install

# 4. Start the server
uv run uvicorn app.main:app --reload
```

The interactive wizard will guide you through everything including:
- Environment configuration
- Database setup and testing
- Security configuration
- Admin user creation
- Sample data seeding

## 🛠️ Development Setup

### 1. Install uv (jika belum)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone & Install Dependencies

```bash
git clone <your-repo>
cd backend
uv sync
```

### 3. Environment Setup

```bash
cp .env.example .env
# Edit .env dengan pengaturan database Anda
```

### 4. Database Setup

**Simple Setup:**
```bash
uv run alembic upgrade head
```

**Interactive Setup:**
```bash
uv run erp-install
```

### 5. Data Seeding (Optional)

**Sample Data Only:**
```bash
uv run python -c "
import asyncio
from app.services.sample_data_seeder import seed_sample_data
from app.database import SessionLocal
db = SessionLocal()
asyncio.run(seed_sample_data(db))
"
```

**RBAC + Admin User:**
```bash
uv run erp-bootstrap --seed-rbac --bootstrap-admin --username admin --email admin@example.com --password yourpassword
```

**Complete Data:**
```bash
uv run erp-bootstrap --seed-rbac --seed-sample-data --bootstrap-admin --username admin --email admin@example.com --password yourpassword
```

### 6. Run Development Server

```bash
uv run uvicorn app.main:app --reload
```

API akan berjalan di http://localhost:8000

## �️ CLI Commands

### erp-install (Interactive Installation)
```bash
uv run erp-install
```
Interactive wizard for complete setup including environment, database, security, and admin user creation.

### erp-bootstrap (Manual Data Management)
```bash
# Seed RBAC permissions and roles
uv run erp-bootstrap --seed-rbac

# Seed sample data (suppliers, customers, products, etc.)
uv run erp-bootstrap --seed-sample-data

# Create admin user
uv run erp-bootstrap --bootstrap-admin --username admin --email admin@example.com --password yourpassword

# Complete setup (RBAC + Sample Data + Admin)
uv run erp-bootstrap --seed-rbac --seed-sample-data --bootstrap-admin --username admin --email admin@example.com --password yourpassword
```

### Database Management
```bash
# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Clean database (development only)
uv run python scripts/dev/clean_db.py
```

## �️ Database Triggers

The system includes automatic database triggers for data consistency:

### Stock Balance Management
- **Trigger**: `trg_update_stock_balance` 
- **Function**: `fn_update_stock_balance()`
- **Action**: Automatically updates `stock_balances` when new `stock_ledgers` entries are inserted
- **Benefit**: Real-time inventory tracking without manual calculations

### Timestamp Management  
- **Trigger**: `trg_*_updated_at` (on 8 tables)
- **Function**: `fn_set_updated_at()`
- **Tables**: users, suppliers, customers, products, boms, purchase_orders, sales_orders, production_orders
- **Action**: Automatically updates `updated_at` timestamp on row updates
- **Benefit**: Accurate audit trails without manual timestamp management

### Trigger Status Check
```bash
# Check active triggers
uv run python -c "
import asyncio
from sqlalchemy import text
from app.database import SessionLocal

async def check_triggers():
    db = SessionLocal()
    result = await db.execute(text('SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_name LIKE \'trg_%\''))
    count = result.scalar()
    print(f'Active triggers: {count}')
    await db.close()

asyncio.run(check_triggers())
"
```

## ��️ API Modules Overview

### **📦 Inventory Management** (`/api/v1/inventory/`)
- **Stock Balances**: GET, POST, PUT - Real-time inventory tracking
- **Stock Ledgers**: GET, POST - Complete transaction history
- **Stock Movements**: POST - Transfer stock between locations
- **Reports**: GET - Inventory summary, low stock alerts

### **🛒 Purchasing** (`/api/v1/purchasing/`)
- **Suppliers**: GET, POST, PUT, DELETE - Complete supplier management
- **Purchase Orders**: GET, POST, PUT - Full PO lifecycle
- **Receiving**: POST - Goods receipt processing
- **Reports**: GET - Purchasing analytics and summaries

### **🏭 Production** (`/api/v1/production/`)
- **Work Centers**: GET, POST, PUT - Manufacturing resources
- **BOMs**: GET, POST, PUT - Bill of Materials with items
- **Production Orders**: GET, POST, PUT - Manufacturing workflow
- **Operations**: POST - Start/complete production orders
- **Reports**: GET - Production analytics and efficiency

### **🏪 Warehouse Management** (`/api/v1/warehouse/`)
- **Locations**: GET, POST, PUT, DELETE - Hierarchical locations
- **Tree Structure**: GET - Parent-child relationships
- **Hierarchy**: GET - Location paths and levels
- **Reports**: GET - Warehouse utilization analysis

### **👥 User Management** (`/api/v1/users/`)
- **Users**: GET, POST, PUT - Complete user CRUD
- **Roles**: GET, POST, PUT, DELETE - Role-based access control
- **Permissions**: GET - Granular permission system
- **Assignments**: POST, DELETE - User-role management
- **Security**: POST - Password management, user activation

### **🔐 Authentication** (`/api/v1/auth/`)
- **Login**: POST - JWT token authentication
- **Register**: POST - User registration
- **Refresh**: POST - Token refresh mechanism
- **Profile**: GET - User profile information

### **📊 Sales & Products** (`/api/v1/`)
- **Products**: Complete product catalog management
- **Sales Orders**: Full sales order processing
- **Customers**: Customer relationship management

## 📈 API Statistics

- **Total Endpoints**: 75+
- **Modules**: 8 complete business modules
- **CRUD Operations**: Full Create, Read, Update, Delete for all entities
- **Business Logic**: Production workflow, stock transfers, PO receiving
- **Reporting**: 10+ comprehensive reports with analytics
- **Security**: JWT authentication + RBAC authorization
- **Data Validation**: Pydantic schemas + business rules
- **Database Triggers**: Automatic stock balance and timestamp updates

## 🛠️ Development Scripts

### Debug Scripts (`scripts/dev/`)
⚠️ **Development only** - These scripts can delete data

- `clean_db.py` - Truncates all data tables (for development reset)
  ```bash
  uv run python scripts/dev/clean_db.py
  ```

- `check_enum.py` - Debug enum values and current data
  ```bash
  uv run python scripts/dev/check_enum.py
  ```

- `check_tables.py` - Debug specific table issues
  ```bash
  uv run python scripts/dev/check_tables.py
  ```

### Interactive Installation Command

The `erp-install` command provides an interactive installation wizard by default:

```bash
# Interactive installation (recommended for first-time setup)
uv run erp-install

# Show all options
uv run erp-install --help

# Non-interactive mode (for automation)
uv run erp-install --non-interactive [options]
```

**Interactive Wizard Features:**
- Step-by-step guidance with clear prompts
- Database connection testing
- Automatic key generation for security
- Default values for easy setup
- Confirmation before each major step
- Progress reporting with emoji indicators

**Non-Interactive Options:**
- `--env {development,production}` - Set environment type
- `--debug` - Enable debug mode
- `--db-url URL` - Database connection string
- `--jwt-secret KEY` - JWT secret key
- `--bootstrap-key KEY` - Bootstrap key
- `--seed-rbac` - Seed RBAC data
- `--seed-sample-data` - Seed sample data
- `--create-admin` - Create admin user
- `--admin-*` - Admin user details
- `--no-seed` - Skip all data seeding
- `--force` - Skip confirmations

## 📊 Database Schema

### Data Types & Standards
- **Primary Keys**: UUID v7 (time-ordered, sortable)
- **Quantities**: Integer (for precise counting)
- **Prices**: Decimal(15,2) (for accurate financial calculations)
- **Timestamps**: Auto-updated via database triggers
- **Soft Deletes**: Users use `deleted_at` column

### Enums
- `LocationType`: warehouse, production_floor, subcontract, transit
- `ProductCategory`: material, parts, wip, finished_good
- `POStatus`: draft, confirmed, partial, received, cancelled
- `SOStatus`: draft, confirmed, partial, shipped, cancelled
- `ProductionStatus`: draft, in_progress, completed, cancelled
- `TransactionType`: purchase, sale, transfer, adjustment, production, return

## 🧪 Testing & Development

### Seed Sample Data

```bash
# Interactive seeding (recommended)
uv run erp-install

# Or clean and reseed everything
uv run python scripts/dev/clean_db.py
uv run erp-install --non-interactive --seed-rbac --seed-sample-data --force
```

The sample data seeder creates:
- 3 suppliers, 3 customers
- 27 locations (warehouse hierarchy)
- 8 products (materials, parts, finished goods)
- 5 work centers
- 2 BOMs with materials and operations
- Stock balances and ledgers
- 2 purchase orders with items
- 2 sales orders with items
- 3 production orders

### Development Commands

```bash
# Run tests
uv run pytest

# Code formatting
uv run --group dev black .

# Linting
uv run --group dev ruff check .

# Type checking
uv run --group dev mypy app/
```

## 📁 Project Structure

```
erp_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── database.py             # Async database engine/session
│   ├── core/                   # App config + security utils
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── dependencies/           # FastAPI dependencies (auth/RBAC)
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── services/               # Business services (bootstrap/seed)
│   │   ├── __init__.py
│   │   ├── bootstrap.py
│   │   └── sample_data_seeder.py
│   ├── cli/                    # Operational CLI commands
│   │   ├── __init__.py
│   │   └── install.py          # Interactive installation wizard
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py             # Base & TimestampMixin
│   │   ├── enums.py            # Python Enums
│   │   ├── auth.py             # User, Role, Permission
│   │   ├── master_data.py      # Supplier, Customer
│   │   ├── inventory.py        # Product, Location, Stock
│   │   ├── production.py       # BOM, ProductionOrder
│   │   ├── purchasing.py       # PurchaseOrder
│   │   └── sales.py            # SalesOrder
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── product.py
│   │   ├── sales.py
│   │   ├── inventory.py         # Inventory data models
│   │   ├── purchasing.py        # Purchasing data models
│   │   ├── production.py        # Production data models
│   │   ├── warehouse.py         # Warehouse data models
│   │   └── users.py             # User management data models
│   └── routers/                # API endpoints
│       ├── __init__.py
│       ├── auth.py              # Authentication endpoints
│       ├── products.py          # Product management
│       ├── sales.py             # Sales order endpoints
│       ├── inventory.py         # 12 inventory endpoints
│       ├── purchasing.py        # 15 purchasing endpoints
│       ├── production.py        # 18 production endpoints
│       ├── warehouse.py         # 10 warehouse endpoints
│       └── users.py             # 20 user management endpoints
├── migrations/                 # Alembic migrations
│   └── versions/
├── scripts/                    # Utility scripts
│   ├── dev/                   # Development scripts
│   └── prod/                  # Production scripts
├── .env.example                # Environment variables template
├── pyproject.toml              # Project dependencies
├── .gitignore                  # Git ignore file
├── README.md                   # This file (Development)
└── README_PRODUCTION.md        # Production guide
```

## 🚀 Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (AsyncSession)
- **Database**: PostgreSQL
- **Auth**: OAuth2 Password Flow + Bearer JWT (access/refresh)
- **Authorization**: RBAC (roles + permissions)
- **Package Manager**: uv
- **Migrations**: Alembic
- **Code Quality**: Black, Ruff, Pre-commit hooks

## 🎯 Key Features

### 1. Complete ERP Functionality
- **75+ API Endpoints** covering all business operations
- **8 Business Modules**: Inventory, Purchasing, Production, Warehouse, Sales, Auth, Products, Users
- **Full CRUD Operations** for all entities with business logic validation
- **Real-time Stock Tracking** with automatic balance updates via database triggers
- **Production Workflow** from BOM to finished goods
- **Purchase Order Management** from creation to receiving
- **Hierarchical Warehouse Structure** with tree management

### 2. Modern Data Standards
- **UUID v7**: Time-ordered UUIDs for all primary and foreign keys
- **Type-safe**: Integer quantities, Decimal(15,2) prices for accuracy
- **Consistent**: Unified data types across all models
- **Database Triggers**: Automatic stock balance and timestamp updates

### 3. Interactive Installation
- Step-by-step wizard for easy setup
- Database connection testing
- Automatic key generation
- Environment configuration

### 4. Security & Authorization
- **JWT Authentication** with access/refresh tokens
- **RBAC System** with roles and permissions
- **Password Management** with secure hashing
- **User Activation/Deactivation** capabilities

### 5. Comprehensive Reporting
- **Inventory Analytics**: Stock levels, low stock alerts
- **Production Reports**: Order status, completion rates
- **Purchasing Analytics**: Order values, supplier performance
- **Warehouse Utilization**: Location usage analysis
- **User Management Reports**: Active users, role distribution

### 6. Environment-aware Documentation
- **Development**: Swagger UI (`/docs`) and ReDoc (`/redoc`) are enabled
- **Production**: Documentation endpoints are automatically disabled for security

### 7. Code Quality
- **Black**: Consistent code formatting
- **Ruff**: Fast Python linter
- **Pre-commit**: Automated quality checks
- **Type hints**: Full type annotation coverage
- **Pydantic Schemas**: Comprehensive data validation

## 📋 Version History

For detailed changes and migration history, see [`CHANGELOG.md`](../CHANGELOG.md)

## � License

MIT
