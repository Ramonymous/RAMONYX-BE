#!/usr/bin/env python3
"""
Production Data Cleanup Script
Archives or removes old data to maintain system performance
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta

from sqlalchemy import text

from app.database import SessionLocal


class DataCleaner:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.actions: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def add_action(self, message: str, count: int = 0) -> None:
        prefix = "Would" if self.dry_run else "Will"
        self.actions.append(f"🔧 {prefix} {message} ({count} records)" if count else f"🔧 {prefix} {message}")

    def add_warning(self, message: str) -> None:
        self.warnings.append(f"⚠️  {message}")

    def add_info(self, message: str) -> None:
        self.info.append(f"ℹ️  {message}")

    async def archive_old_stock_ledgers(self, days_to_keep: int = 365) -> int:
        """Archive old stock ledger entries."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            async with SessionLocal() as db:
                # Count old entries
                result = await db.execute(
                    text("""
                    SELECT COUNT(*) FROM stock_ledgers
                    WHERE created_at < :cutoff_date
                """),
                    {"cutoff_date": cutoff_date},
                )
                old_count = result.scalar() or 0

                if old_count == 0:
                    self.add_info("No old stock ledger entries to archive")
                    return 0

                self.add_action(f"archive stock ledger entries older than {days_to_keep} days", old_count)

                if not self.dry_run:
                    # Create archive table if it doesn't exist
                    await db.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS stock_ledgers_archive (
                            LIKE stock_ledgers INCLUDING ALL
                        )
                    """)
                    )

                    # Move old entries to archive
                    await db.execute(
                        text("""
                        INSERT INTO stock_ledgers_archive
                        SELECT * FROM stock_ledgers
                        WHERE created_at < :cutoff_date
                    """),
                        {"cutoff_date": cutoff_date},
                    )

                    # Delete old entries
                    await db.execute(
                        text("""
                        DELETE FROM stock_ledgers
                        WHERE created_at < :cutoff_date
                    """),
                        {"cutoff_date": cutoff_date},
                    )

                    await db.commit()

                return old_count

        except Exception as e:
            self.add_warning(f"Failed to archive stock ledgers: {e}")
            return 0

    async def cleanup_old_sessions(self, days_to_keep: int = 30) -> int:
        """Clean up old session data (if sessions table exists)."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            async with SessionLocal() as db:
                # Check if sessions table exists
                result = await db.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'sessions'
                    )
                """)
                )
                sessions_exist = result.scalar()

                if not sessions_exist:
                    self.add_info("No sessions table found")
                    return 0

                # Count old sessions
                result = await db.execute(
                    text("""
                    SELECT COUNT(*) FROM sessions
                    WHERE created_at < :cutoff_date OR expires_at < NOW()
                """),
                    {"cutoff_date": cutoff_date},
                )
                old_count = result.scalar() or 0

                if old_count == 0:
                    self.add_info("No old sessions to clean up")
                    return 0

                self.add_action(f"delete sessions older than {days_to_keep} days or expired", old_count)

                if not self.dry_run:
                    await db.execute(
                        text("""
                        DELETE FROM sessions
                        WHERE created_at < :cutoff_date OR expires_at < NOW()
                    """),
                        {"cutoff_date": cutoff_date},
                    )

                    await db.commit()

                return old_count

        except Exception as e:
            self.add_warning(f"Failed to cleanup sessions: {e}")
            return 0

    async def cleanup_temp_files(self, days_to_keep: int = 7) -> int:
        """Clean up temporary files and logs (placeholder)."""
        try:
            # This would typically clean up temporary files, old logs, etc.
            # For now, just log what would be done
            self.add_action(f"clean temporary files older than {days_to_keep} days")
            self.add_info("Temp file cleanup would be implemented based on your file structure")
            return 0

        except Exception as e:
            self.add_warning(f"Failed to cleanup temp files: {e}")
            return 0

    async def cleanup_audit_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit logs (if audit_logs table exists)."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            async with SessionLocal() as db:
                # Check if audit_logs table exists
                result = await db.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'audit_logs'
                    )
                """)
                )
                audit_exists = result.scalar()

                if not audit_exists:
                    self.add_info("No audit_logs table found")
                    return 0

                # Count old audit entries
                result = await db.execute(
                    text("""
                    SELECT COUNT(*) FROM audit_logs
                    WHERE created_at < :cutoff_date
                """),
                    {"cutoff_date": cutoff_date},
                )
                old_count = result.scalar() or 0

                if old_count == 0:
                    self.add_info("No old audit logs to clean up")
                    return 0

                self.add_action(f"archive audit logs older than {days_to_keep} days", old_count)

                if not self.dry_run:
                    # Create archive table
                    await db.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS audit_logs_archive (
                            LIKE audit_logs INCLUDING ALL
                        )
                    """)
                    )

                    # Archive old entries
                    await db.execute(
                        text("""
                        INSERT INTO audit_logs_archive
                        SELECT * FROM audit_logs
                        WHERE created_at < :cutoff_date
                    """),
                        {"cutoff_date": cutoff_date},
                    )

                    # Delete old entries
                    await db.execute(
                        text("""
                        DELETE FROM audit_logs
                        WHERE created_at < :cutoff_date
                    """),
                        {"cutoff_date": cutoff_date},
                    )

                    await db.commit()

                return old_count

        except Exception as e:
            self.add_warning(f"Failed to cleanup audit logs: {e}")
            return 0

    async def optimize_database(self) -> None:
        """Run database optimization commands."""
        try:
            self.add_action("update database statistics")
            self.add_action("rebuild indexes (if needed)")

            if not self.dry_run:
                async with SessionLocal() as db:
                    # Update statistics
                    await db.execute(text("ANALYZE"))

                    # This would typically include VACUUM operations
                    # but those might require superuser privileges
                    await db.commit()

        except Exception as e:
            self.add_warning(f"Failed to optimize database: {e}")

    async def get_storage_savings(self) -> dict[str, int]:
        """Estimate storage savings from cleanup."""
        try:
            async with SessionLocal() as db:
                savings = {}

                # Estimate stock ledger savings
                result = await db.execute(
                    text(
                        """
                        SELECT
                            COUNT(*) as total_entries,
                            COUNT(*) FILTER (
                                WHERE created_at < NOW() - INTERVAL '365 days'
                            ) as old_entries,
                            pg_size_pretty(pg_total_relation_size('stock_ledgers')) as total_size
                        FROM stock_ledgers
                        """
                    )
                )
                ledger_stats = result.fetchone()

                if ledger_stats and ledger_stats.total_entries > 0:
                    old_ratio = ledger_stats.old_entries / ledger_stats.total_entries
                    # Rough estimate of space savings
                    savings["stock_ledgers"] = int(old_ratio * 100)  # percentage

                return savings

        except Exception as e:
            self.add_warning(f"Could not estimate storage savings: {e}")
            return {}

    async def run_cleanup(self, options: dict[str, int]) -> bool:
        """Run the cleanup process."""
        mode = "DRY RUN" if self.dry_run else "LIVE"
        print(f"🧹 Production Data Cleanup ({mode})")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        total_cleaned = 0

        # Run cleanup tasks
        if options.get("stock_ledgers", 0) > 0:
            print("Cleaning old stock ledgers...")
            total_cleaned += await self.archive_old_stock_ledgers(options["stock_ledgers"])
            print()

        if options.get("sessions", 0) > 0:
            print("Cleaning old sessions...")
            total_cleaned += await self.cleanup_old_sessions(options["sessions"])
            print()

        if options.get("audit_logs", 0) > 0:
            print("Cleaning old audit logs...")
            total_cleaned += await self.cleanup_audit_logs(options["audit_logs"])
            print()

        if options.get("temp_files", 0) > 0:
            print("Cleaning temporary files...")
            total_cleaned += await self.cleanup_temp_files(options["temp_files"])
            print()

        # Always optimize
        print("Optimizing database...")
        await self.optimize_database()
        print()

        # Get storage savings estimate
        savings = await self.get_storage_savings()

        # Print results
        if self.actions:
            print("Actions to be performed:" if self.dry_run else "Actions performed:")
            for action in self.actions:
                print(f"  {action}")
            print()

        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.info:
            print("Information:")
            for info in self.info:
                print(f"  {info}")
            print()

        if savings:
            print("Estimated storage savings:")
            for table, percentage in savings.items():
                print(f"  {table}: ~{percentage}% reduction")
            print()

        # Summary
        if self.dry_run:
            print(f"📋 Dry run completed. Would clean approximately {total_cleaned} records.")
            print("   Run with --execute to perform actual cleanup.")
        else:
            print(f"✅ Cleanup completed. Processed {total_cleaned} records.")

        return True


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Production data cleanup utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_old_data.py                    # Dry run with default settings
  python cleanup_old_data.py --execute         # Actually perform cleanup
  python cleanup_old_data.py --stock-ledgers 180  # Custom retention periods
  python cleanup_old_data.py --sessions 7 --audit-logs 30
        """,
    )

    parser.add_argument("--execute", action="store_true", help="Actually perform cleanup (default: dry run)")

    parser.add_argument(
        "--stock-ledgers",
        type=int,
        default=365,
        help="Days to keep stock ledger entries (default: 365)",
    )

    parser.add_argument("--sessions", type=int, default=30, help="Days to keep sessions (default: 30)")

    parser.add_argument("--audit-logs", type=int, default=90, help="Days to keep audit logs (default: 90)")

    parser.add_argument("--temp-files", type=int, default=7, help="Days to keep temp files (default: 7)")

    args = parser.parse_args()

    # Safety check for production
    if not args.execute:
        print("⚠️  RUNNING IN DRY RUN MODE - NO DATA WILL BE MODIFIED")
        print("   Use --execute to perform actual cleanup")
        print()

    cleaner = DataCleaner(dry_run=not args.execute)

    options = {
        "stock_ledgers": args.stock_ledgers,
        "sessions": args.sessions,
        "audit_logs": args.audit_logs,
        "temp_files": args.temp_files,
    }

    success = await cleaner.run_cleanup(options)

    if not success:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
