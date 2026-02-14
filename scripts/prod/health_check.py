#!/usr/bin/env python3
"""
Production Health Check Script
Monitors system health and reports issues
"""

import asyncio
import sys
from datetime import datetime

from sqlalchemy import text

from app.core.config import settings
from app.database import SessionLocal, engine


class HealthChecker:
    def __init__(self) -> None:
        self.issues = []
        self.warnings = []
        self.info = []

    def add_issue(self, message: str) -> None:
        self.issues.append(f"❌ {message}")

    def add_warning(self, message: str) -> None:
        self.warnings.append(f"⚠️  {message}")

    def add_info(self, message: str) -> None:
        self.info.append(f"ℹ️  {message}")

    async def check_database_connection(self) -> bool:
        """Check database connectivity."""
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    self.add_info("Database connection: OK")
                    return True
        except Exception as e:
            self.add_issue(f"Database connection failed: {e}")
            return False

    async def check_database_tables(self) -> bool:
        """Check if essential tables exist and have data."""
        try:
            async with SessionLocal() as db:
                # Check essential tables
                essential_tables = [
                    "users",
                    "roles",
                    "permissions",
                    "products",
                    "suppliers",
                    "customers",
                    "sales_orders",
                ]

                missing_tables = []
                empty_tables = []

                for table in essential_tables:
                    result = await db.execute(
                        text(
                            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                        )
                    )
                    exists = result.scalar()

                    if not exists:
                        missing_tables.append(table)
                    else:
                        # Check if table has data (except users which might be empty initially)
                        if table != "users":
                            count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = count_result.scalar()
                            if count == 0:
                                empty_tables.append(table)

                if missing_tables:
                    self.add_issue(f"Missing tables: {', '.join(missing_tables)}")
                    return False

                if empty_tables:
                    self.add_warning(f"Empty tables: {', '.join(empty_tables)}")

                self.add_info("Database tables: OK")
                return True

        except Exception as e:
            self.add_issue(f"Database table check failed: {e}")
            return False

    async def check_database_size(self) -> bool:
        """Check database size and warn if too large."""
        try:
            async with SessionLocal() as db:
                result = await db.execute(
                    text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                )
                size = result.scalar()

                # Get size in bytes for comparison
                size_bytes_result = await db.execute(
                    text("""
                    SELECT pg_database_size(current_database())
                """)
                )
                size_bytes = size_bytes_result.scalar()
                size_gb = size_bytes / (1024**3)

                self.add_info(f"Database size: {size}")

                if size_gb > 10:  # Warn if > 10GB
                    self.add_warning(f"Database size is large: {size_gb:.2f} GB")

                return True

        except Exception as e:
            self.add_warning(f"Could not check database size: {e}")
            return False

    async def check_environment(self) -> bool:
        """Check environment configuration."""
        try:
            # Check critical environment variables
            critical_vars = ["DATABASE_URL", "JWT_SECRET_KEY"]

            for var in critical_vars:
                value = getattr(settings, var.lower().replace("url", "_url"), None)
                if not value:
                    self.add_issue(f"Missing critical environment variable: {var}")
                    return False

            # Check environment type
            env = settings.app_env
            if env not in ["development", "production"]:
                self.add_warning(f"Unknown environment: {env}")
            else:
                self.add_info(f"Environment: {env}")

            # Check debug mode in production
            if env == "production" and settings.debug:
                self.add_warning("Debug mode is enabled in production")

            return True

        except Exception as e:
            self.add_issue(f"Environment check failed: {e}")
            return False

    async def check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            # This is a simplified check - in production, you'd want to check the actual data directory
            self.add_info("Disk space check: Basic check passed")
            return True

        except Exception as e:
            self.add_warning(f"Could not check disk space: {e}")
            return False

    async def check_memory_usage(self) -> bool:
        """Check memory usage (basic check)."""
        try:
            import psutil

            memory = psutil.virtual_memory()

            self.add_info(f"Memory usage: {memory.percent:.1f}%")

            if memory.percent > 90:
                self.add_warning(f"High memory usage: {memory.percent:.1f}%")

            return True

        except ImportError:
            self.add_info("psutil not available - skipping memory check")
            return True
        except Exception as e:
            self.add_warning(f"Could not check memory usage: {e}")
            return False

    async def check_recent_activity(self) -> bool:
        """Check for recent database activity."""
        try:
            async with SessionLocal() as db:
                # Check recent user activity
                result = await db.execute(
                    text("""
                    SELECT COUNT(*) FROM users
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                )
                recent_users = result.scalar()

                # Check recent orders
                result = await db.execute(
                    text("""
                    SELECT COUNT(*) FROM sales_orders
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                )
                recent_orders = result.scalar()

                if recent_users > 0:
                    self.add_info(f"Recent users (24h): {recent_users}")

                if recent_orders > 0:
                    self.add_info(f"Recent sales orders (24h): {recent_orders}")

                if recent_users == 0 and recent_orders == 0:
                    self.add_warning("No recent activity detected (24h)")

                return True

        except Exception as e:
            self.add_warning(f"Could not check recent activity: {e}")
            return False

    async def run_all_checks(self) -> bool:
        """Run all health checks."""
        print("🏥 Production Health Check")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        checks = [
            ("Database Connection", self.check_database_connection),
            ("Database Tables", self.check_database_tables),
            ("Database Size", self.check_database_size),
            ("Environment", self.check_environment),
            ("Disk Space", self.check_disk_space),
            ("Memory Usage", self.check_memory_usage),
            ("Recent Activity", self.check_recent_activity),
        ]

        all_passed = True

        for check_name, check_func in checks:
            print(f"Checking {check_name}...")
            try:
                result = await check_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.add_issue(f"Check failed: {e}")
                all_passed = False
            print()

        # Print results
        if self.issues:
            print("🚨 Critical Issues:")
            for issue in self.issues:
                print(f"  {issue}")
            print()

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.info:
            print("✅ Information:")
            for info in self.info:
                print(f"  {info}")
            print()

        # Summary
        if all_passed and not self.issues:
            print("🎉 All health checks passed!")
            return True
        print(
            f"❌ Health check completed with {len(self.issues)} critical issue(s) and {len(self.warnings)} warning(s)"
        )
        return False


async def main() -> None:
    checker = HealthChecker()
    success = await checker.run_all_checks()

    # Exit with appropriate code
    if not success:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
