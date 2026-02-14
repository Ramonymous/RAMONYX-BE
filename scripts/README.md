# ERP Backend Scripts

This directory contains utility scripts for managing the ERP backend in different environments.

## 📁 Directory Structure

```
scripts/
├── dev/          # Development and debugging scripts
├── prod/         # Production maintenance scripts
└── README.md     # This file
```

---

## 🛠️ Development Scripts (`scripts/dev/`)

These scripts are for development, testing, and debugging purposes only. **DO NOT use in production.**

### Available Scripts

- **`clean_db.py`** - Truncates all data tables (suppliers, customers, products, orders, etc.)
  - ⚠️ **DANGEROUS** - Deletes all business data
  - Use only for development/testing reset
  - Usage: `uv run python scripts/dev/clean_db.py`

- **`check_enum.py`** - Checks enum values and current data in database
  - Used for debugging enum-related issues
  - Usage: `uv run python scripts/dev/check_enum.py`

- **`check_tables.py`** - Lists tables with specific patterns (e.g., BOM tables)
  - Specific debugging tool for development
  - Usage: `uv run python scripts/dev/check_tables.py`

---

## 🏭 Production Scripts (`scripts/prod/`)

These scripts are designed for production use and include safety checks, dry-run modes, and proper error handling.

### Available Scripts

#### 📊 **`backup_db.py`** - Database Backup
Creates compressed database backups with retention management.

```bash
# Create backup with default settings (30-day retention)
uv run python scripts/prod/backup_db.py

# Custom backup directory and retention
uv run python scripts/prod/backup_db.py --dir /backups --retention 7

# List existing backups
uv run python scripts/prod/backup_db.py --list
```

**Features:**
- Compressed backups (.sql.gz)
- Automatic retention management
- Database connection testing
- Backup size reporting
- Error handling and logging

#### 🏥 **`health_check.py`** - System Health Monitoring
Comprehensive health check for the ERP system.

```bash
# Run full health check
uv run python scripts/prod/health_check.py
```

**Checks Performed:**
- Database connectivity
- Database table existence and data
- Database size monitoring
- Environment configuration
- Disk space (basic check)
- Memory usage (if psutil available)
- Recent activity monitoring

#### 🔍 **`check_data_integrity.py`** - Data Integrity Validation
Validates data consistency across the ERP database.

```bash
# Run integrity checks
uv run python scripts/prod/check_data_integrity.py
```

**Validations:**
- Foreign key constraint violations
- Data consistency (quantities, prices)
- Duplicate records (customers, suppliers, products, users)
- Business rule compliance
- Data anomaly detection
- Summary statistics report

#### 🧹 **`cleanup_old_data.py`** - Data Cleanup and Archiving
Archives or removes old data to maintain system performance.

```bash
# Dry run (default - safe mode)
uv run python scripts/prod/cleanup_old_data.py

# Actually perform cleanup
uv run python scripts/prod/cleanup_old_data.py --execute

# Custom retention periods
uv run python scripts/prod/cleanup_old_data.py --execute \
  --stock-ledgers 180 --sessions 7 --audit-logs 30
```

**Cleanup Operations:**
- Archive old stock ledger entries (default: 365 days)
- Clean up expired sessions (default: 30 days)
- Archive old audit logs (default: 90 days)
- Clean up temporary files (default: 7 days)
- Database optimization

---

## 📅 Recommended Production Schedule

### Daily
- **Health Check**: `python scripts/prod/health_check.py`
- **Data Integrity**: `python scripts/prod/check_data_integrity.py`

### Weekly
- **Backup**: `python scripts/prod/backup_db.py`
- **Cleanup (dry run)**: `python scripts/prod/cleanup_old_data.py`

### Monthly
- **Cleanup (execute)**: `python scripts/prod/cleanup_old_data.py --execute`
- **Review backup retention**: Adjust backup retention if needed

### Quarterly
- **Full system review**: Check all scripts and logs
- **Update scripts**: Review and update cleanup thresholds

---

## 🚨 Safety Guidelines

### Production Scripts Safety Features
1. **Dry Run Mode**: Most scripts run in dry-run mode by default
2. **Confirmation Prompts**: Critical actions require confirmation
3. **Rollback Information**: Scripts provide information about what they'll do
4. **Error Handling**: Comprehensive error handling and logging
5. **Non-Destructive**: Scripts prefer archiving over deletion

### Before Running Production Scripts
1. **Test in Staging**: Always test scripts in a staging environment first
2. **Backup First**: Ensure you have a recent backup before cleanup operations
3. **Check Permissions**: Ensure the script has necessary database permissions
4. **Monitor Resources**: Monitor system resources during script execution
5. **Review Logs**: Check script output for any warnings or errors

### Emergency Procedures
1. **Stop Script**: Use Ctrl+C to stop any running script
2. **Check Database**: Run health check to verify system status
3. **Restore Backup**: If needed, restore from the most recent backup
4. **Review Logs**: Check application and script logs for issues

---

## 🛠️ Script Development Guidelines

When adding new scripts:

### Development Scripts
- Place in `scripts/dev/`
- Add clear warnings about production use
- Include simple error handling
- Use descriptive names

### Production Scripts
- Place in `scripts/prod/`
- Include dry-run mode
- Add comprehensive error handling
- Provide detailed logging
- Include safety checks
- Add usage examples in docstrings
- Update this README

### General Guidelines
- Use async/await for database operations
- Include proper type hints
- Add command-line argument parsing
- Provide helpful error messages
- Follow the existing code style

---

## 📞 Support

If you encounter issues with any script:

1. Check the script output for error messages
2. Verify database connectivity
3. Ensure proper permissions
4. Check environment variables
5. Review the script's help text: `python script_name.py --help`

For urgent issues, stop the script and perform a health check before proceeding.
