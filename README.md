# ERP Backend API

Backend API untuk sistem ERP dengan fitur lengkap:
- ✅ **Authentication & Authorization** (Users, Roles, Permissions)
- ✅ **Master Data** (Suppliers, Customers, Products, Locations)
- ✅ **Inventory Management** (Stock Balances, Stock Ledgers, Auto-trigger Updates)
- ✅ **Production** (BOM, Work Centers, Production Orders)
- ✅ **Purchasing** (Suppliers, Purchase Orders, Receiving)
- ✅ **Sales** (Sales Orders, Sales Order Items)
- ✅ **Warehouse Management** (Location Hierarchy, Tree Structure)
- ✅ **Database Triggers** (Auto Stock Balance, Auto Timestamp Updates)
- ✅ **User Management** (RBAC, Role Assignment, Security)
- ✅ **Comprehensive Reporting** (Analytics, Summaries, Alerts)
- ✅ **75+ API Endpoints** - Complete CRUD operations for all modules
- ✅ **UUID v7** for all primary and foreign keys
- ✅ **Type-safe Data** (Integer quantities, Decimal(15,2) prices)
- ✅ **Clean Migration** - Single migration file with all schema and triggers

## 🚀 Quick Start

Choose your environment:

### 🛠️ Development Setup
**File:** [`README_DEV.md`](./README_DEV.md)

For developers working on the ERP backend:
- Quick start guide with simple & interactive install options
- Development scripts and tools
- API documentation (Swagger/ReDoc)
- Debugging and testing guides
- Sample data seeding
- Database triggers documentation
- CLI commands reference

### 🏭 Production Deployment
**File:** [`README_PROD.md`](./README_PROD.md)

For production deployment and maintenance:
- Production deployment guide
- Security configuration
- Maintenance scripts and schedules
- Backup and recovery procedures
- Performance optimization
- Emergency procedures
- Database triggers in production

---

## 🎯 Quick Decision

| Your Goal | Read This |
|-----------|-----------|
| I'm a developer setting up the project | [`README_DEV.md`](./README_DEV.md) |
| I need a simple development setup | [`README_DEV.md`](./README_DEV.md) → Option 1: Simple Install |
| I prefer interactive installation | [`README_DEV.md`](./README_DEV.md) → Option 2: Interactive Install |
| I'm deploying to production | [`README_PROD.md`](./README_PROD.md) |
| I need to maintain a production system | [`README_PROD.md`](./README_PROD.md) |
| I need CLI commands reference | [`README_DEV.md`](./README_DEV.md) → CLI Commands |
| I need to debug or test features | [`README_DEV.md`](./README_DEV.md) |

## 📁 Project Structure

```
backend/
├── README.md                 # Main landing page ⬅️ Start here
├── README_DEV.md            # Development guide
├── README_PROD.md           # Production guide
├── scripts/                 # Utility scripts
│   ├── dev/                # Development tools
│   └── prod/               # Production tools
├── migrations/              # Database migrations
│   └── versions/           # Migration files (single clean migration)
└── app/                    # Application code
    ├── cli/                # CLI commands (erp-install, erp-bootstrap)
    ├── models/             # SQLAlchemy models
    ├── services/           # Business logic
    └── routers/            # API endpoints
```

## 🛠️ Installation Overview

### Development (Recommended)
```bash
# Clone and setup
git clone <your-repo>
cd backend
uv sync
cp .env.example .env

# Simple install (recommended for development)
uv run alembic upgrade head
uv run python -c "seed_sample_data()"
uv run uvicorn app.main:app --reload
```

### Production
```bash
# Clone and setup
git clone <your-repo>
cd backend
uv sync
cp .env.example .env

# Interactive install (recommended for production)
uv run erp-install
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🗄️ Database Features

- **✅ Single Clean Migration** - One migration file with complete schema
- **✅ Database Triggers** - Auto stock balance & timestamp updates
- **✅ UUID v7 Keys** - Modern distributed primary keys
- **✅ Type-safe Data** - Integer quantities, Decimal(15,2) prices
- **✅ No Enum Types** - All converted to strings for simplicity

## 📚 API Documentation

Once server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🆘 Need Help?

- **Development Issues**: See [`README_DEV.md`](./README_DEV.md)
- **Production Issues**: See [`README_PROD.md`](./README_PROD.md)
- **CLI Commands**: See [`README_DEV.md`](./README_DEV.md) → CLI Commands section
- **Script Usage**: See [`scripts/README.md`](./scripts/README.md)
- **Version History**: See [`CHANGELOG.md`](./CHANGELOG.md)

---

**Last Updated**: 2026-02-14  
**Version**: 1.0.0 - Clean Migration with Database Triggers & Simple Install Options

## License

MIT
