#!/usr/bin/env python3
"""
Production Database Backup Script
Creates backups of the ERP database with compression and retention management
"""

import argparse
import asyncio
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from app.core.config import settings


def parse_db_url(url: str) -> dict:
    """Parse database URL to extract connection parameters."""
    if not url:
        raise ValueError("DATABASE_URL is not set")

    # Parse postgresql+asyncpg://user:pass@host:port/db
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")

    # Simple parsing - in production, consider using urllib.parse
    parts = url.replace("postgresql://", "").split("@")
    if len(parts) != 2:
        raise ValueError("Invalid database URL format")

    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")

    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host_port = host_db[0].split(":")
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    database = host_db[1] if len(host_db) > 1 else "erp_db"

    return {"user": user, "password": password, "host": host, "port": port, "database": database}


async def create_backup(backup_dir: Path, retention_days: int = 30) -> bool:
    """Create database backup with compression."""
    try:
        # Parse database URL
        db_config = parse_db_url(settings.database_url)

        # Create backup directory if it doesn't exist
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"erp_backup_{timestamp}.sql"
        compressed_file = backup_dir / f"erp_backup_{timestamp}.sql.gz"

        print(f"Creating database backup: {backup_file}")

        # Set PGPASSWORD environment variable for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = db_config["password"]

        # Create backup using pg_dump
        cmd = [
            "pg_dump",
            "-h",
            db_config["host"],
            "-p",
            db_config["port"],
            "-U",
            db_config["user"],
            "-d",
            db_config["database"],
            "--verbose",
            "--no-password",
            "--format=custom",
            "--file",
            str(backup_file),
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Backup failed: {result.stderr}")
            return False

        # Compress the backup
        print("Compressing backup...")
        compress_cmd = ["gzip", str(backup_file)]
        compress_result = subprocess.run(compress_cmd, capture_output=True, text=True)

        if compress_result.returncode != 0:
            print(f"❌ Compression failed: {compress_result.stderr}")
            return False

        # Get backup size
        backup_size = compressed_file.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Backup created successfully: {compressed_file}")
        print(f"   Size: {backup_size:.2f} MB")

        # Clean old backups
        await cleanup_old_backups(backup_dir, retention_days)

        return True

    except Exception as e:
        print(f"❌ Backup error: {e}")
        return False


async def cleanup_old_backups(backup_dir: Path, retention_days: int) -> None:
    """Remove backups older than retention period."""
    try:
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        deleted_count = 0

        for backup_file in backup_dir.glob("erp_backup_*.sql.gz"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                deleted_count += 1
                print(f"   Deleted old backup: {backup_file.name}")

        if deleted_count > 0:
            print(f"✅ Cleaned up {deleted_count} old backup(s)")

    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


async def list_backups(backup_dir: Path) -> None:
    """List all available backups."""
    print("\nAvailable backups:")
    print("-" * 60)

    backups = sorted(backup_dir.glob("erp_backup_*.sql.gz"), reverse=True)

    if not backups:
        print("No backups found.")
        return

    for backup in backups:
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{backup.name:40} {size_mb:8.2f} MB  {mtime.strftime('%Y-%m-%d %H:%M')}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Production database backup utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backup_db.py                    # Create backup with default settings
  python backup_db.py --dir /backups     # Custom backup directory
  python backup_db.py --retention 7      # Keep backups for 7 days
  python backup_db.py --list             # List existing backups
        """,
    )

    parser.add_argument("--dir", type=str, default="backups", help="Backup directory (default: backups)")
    parser.add_argument("--retention", type=int, default=30, help="Retention period in days (default: 30)")
    parser.add_argument("--list", action="store_true", help="List existing backups")

    args = parser.parse_args()

    backup_dir = Path(args.dir)

    if args.list:
        await list_backups(backup_dir)
        return

    print("🗄️  Production Database Backup")
    print("=" * 50)

    success = await create_backup(backup_dir, args.retention)

    if success:
        print("\n✅ Backup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Backup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
