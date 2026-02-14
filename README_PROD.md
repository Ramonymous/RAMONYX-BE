# ERP Backend API - Production Guide

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

## Production Deployment

### Prerequisites
- PostgreSQL database (version 13+)
- Python 3.11+ with uv package manager
- SSL certificate for HTTPS
- Reverse proxy (nginx recommended)
- Process manager (systemd recommended)

### 1. Environment Setup

```bash
# Clone repository
git clone <your-repo>
cd backend

# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
```

### 2. Production Environment Configuration

Edit `.env` file:

```bash
# Environment
APP_ENV=production
DEBUG=False
APP_NAME=ERP Backend

# Database (use SSL in production)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/erp_db?ssl=require

# Security (generate strong keys)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-min-32-chars
BOOTSTRAP_KEY=your-super-secure-bootstrap-key-min-16-chars

# CORS (restrict to your domain)
ALLOWED_ORIGINS=https://your-domain.com

# Registration (disable in production)
ALLOW_REGISTRATION=False
ALLOW_BOOTSTRAP_WHEN_USERS_EXIST=False
```

### 3. Database Setup & Triggers

```bash
# Run migrations (includes automatic trigger creation)
uv run alembic upgrade head

# Seed RBAC data
uv run erp-bootstrap --seed-rbac

# Create admin user
uv run erp-bootstrap --bootstrap-admin --username admin --email admin@your-domain.com --password "YourSecurePassword123!"
```

**Database Triggers Included:**
- ✅ **Auto Stock Balance Updates** - Trigger `trg_update_stock_balance` on `stock_ledgers`
- ✅ **Auto Timestamp Updates** - Triggers `trg_*_updated_at` on all timestamp tables
- ✅ **Production Safe** - All triggers tested and production-ready

### 4. Production Server

Using systemd service:

```ini
# /etc/systemd/system/erp-backend.service
[Unit]
Description=ERP Backend API
After=network.target postgresql.service

[Service]
Type=exec
User=erp
Group=erp
WorkingDirectory=/opt/erp/backend
Environment=PATH=/opt/erp/backend/.venv/bin
ExecStart=/opt/erp/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable erp-backend
sudo systemctl start erp-backend
```

## Production Maintenance

### Daily Health Checks

```bash
# System health monitoring
uv run python scripts/prod/health_check.py

# Data integrity validation (includes trigger validation)
uv run python scripts/prod/check_data_integrity.py
```

### Backup Strategy

```bash
# Daily backup with 30-day retention
uv run python scripts/prod/backup_db.py --dir /backups --retention 30

# List backups
uv run python scripts/prod/backup_db.py --list
```

### Data Cleanup

```bash
# Dry run to see what would be cleaned
uv run python scripts/prod/cleanup_old_data.py

# Execute cleanup (run monthly)
uv run python scripts/prod/cleanup_old_data.py --execute
```

## Database Triggers in Production

### Active Triggers

**Stock Balance Management:**
- `fn_update_stock_balance()` - Function for stock balance calculations
- `trg_update_stock_balance` - Trigger AFTER INSERT on `stock_ledgers`

**Timestamp Management:**
- `fn_set_updated_at()` - Function for timestamp updates
- `trg_*_updated_at` - Triggers BEFORE UPDATE on 8 tables (users, suppliers, customers, products, boms, purchase_orders, sales_orders, production_orders)

### Trigger Monitoring

```bash
# Check trigger status
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

### Trigger Performance

- ✅ **Optimized** - Minimal overhead on INSERT/UPDATE operations
- ✅ **Tested** - Validated with production data volumes
- ✅ **Safe** - Includes error handling and rollback protection
- ✅ **Monitored** - Health checks include trigger validation

## Security Configuration

### SSL/TLS Setup

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Headers

```python
# Add to main.py for production
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)
```

## Monitoring & Logging

### Application Logging

Configure logging in production:

```python
# Add to main.py
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("/var/log/erp/app.log", maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Database Monitoring

Monitor:
- Connection pool usage
- Query performance
- Database size growth
- Index usage
- Trigger execution performance

## Production Checklist

### Pre-deployment
- [ ] Generate strong JWT_SECRET_KEY and BOOTSTRAP_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_ORIGINS for your domain
- [ ] Enable SSL for database connection
- [ ] Setup SSL certificate for HTTPS
- [ ] Configure reverse proxy
- [ ] Setup process manager (systemd)
- [ ] Configure logging and monitoring
- [ ] Verify database triggers will be created

### Post-deployment
- [ ] Verify health checks pass
- [ ] Test authentication flow
- [ ] Validate data integrity
- [ ] Confirm triggers are working (stock balance updates)
- [ ] Setup backup schedule
- [ ] Configure monitoring alerts
- [ ] Document emergency procedures

### Security Hardening
- [ ] Disable debug endpoints
- [ ] Implement rate limiting
- [ ] Setup firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement intrusion detection

## Production Scripts

### Maintenance Scripts (`scripts/prod/`)
**Production-safe** - Include dry-run modes and safety checks

- `backup_db.py` - Database backup with compression & retention
- `health_check.py` - System health monitoring (includes trigger checks)
- `check_data_integrity.py` - Data validation & consistency
- `cleanup_old_data.py` - Data cleanup & archiving

### Recommended Schedule

**Daily:**
- Health check: `python scripts/prod/health_check.py`
- Data integrity: `python scripts/prod/check_data_integrity.py`

**Weekly:**
- Backup: `python scripts/prod/backup_db.py`
- Cleanup dry run: `python scripts/prod/cleanup_old_data.py`

**Monthly:**
- Execute cleanup: `python scripts/prod/cleanup_old_data.py --execute`
- Review backup retention
- Update security patches
- Trigger performance review

## Emergency Procedures

### Service Recovery

```bash
# Check service status
sudo systemctl status erp-backend

# Restart service
sudo systemctl restart erp-backend

# View logs
sudo journalctl -u erp-backend -f
```

### Database Recovery

```bash
# List available backups
uv run python scripts/prod/backup_db.py --list

# Restore from backup (manual process)
pg_restore -h host -U user -d erp_db backup_file.sql

# Re-run migrations to ensure triggers
uv run alembic upgrade head
```

### Trigger Issues

```bash
# Check trigger status
uv run python -c "
import asyncio
from sqlalchemy import text
from app.database import SessionLocal

async def check_triggers():
    db = SessionLocal()
    result = await db.execute(text('SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_name LIKE \'trg_%\''))
    triggers = result.fetchall()
    for t in triggers:
        print(f'{t[0]} on {t[1]}')
    await db.close()

asyncio.run(check_triggers())
"

# Recreate triggers if needed
uv run alembic downgrade base
uv run alembic upgrade head
```

### Security Incident

1. Immediately change JWT_SECRET_KEY
2. Review access logs
3. Invalidate all user sessions
4. Force password reset for all users
5. Review and update security configurations

## Performance Optimization

### Database Optimization

```sql
-- Update statistics
ANALYZE;

-- Rebuild indexes (periodically)
REINDEX DATABASE erp_db;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Monitor trigger performance
SELECT trigger_name, calls, total_time, mean_time 
FROM pg_stat_user_triggers 
ORDER BY total_time DESC;
```

### Application Optimization

- Use connection pooling
- Implement caching (Redis)
- Optimize queries
- Monitor memory usage
- Scale horizontally with load balancer
- Monitor trigger execution time

## Support

For production issues:
1. Check health status: `python scripts/prod/health_check.py`
2. Review application logs
3. Verify database connectivity
4. Check trigger status
5. Check system resources
6. Contact support with logs and diagnostics

## License

MIT

---

## 📋 Version History

For detailed changes and migration history, see [`CHANGELOG.md`](../CHANGELOG.md)
