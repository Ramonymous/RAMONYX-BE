import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Note: We don't import SessionLocal here because we need to create it
# AFTER we update the DATABASE_URL environment variable
from app.models import User
from app.services import BootstrapError, bootstrap_admin_user, seed_rbac
from app.services.sample_data_seeder import seed_sample_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="erp-install",
        description="Interactive installation wizard for Ramonyxs ERP backend.",
    )

    # Non-interactive mode options
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (requires all parameters)",
    )

    # Environment settings
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        help="Set environment type",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    # Database settings
    parser.add_argument(
        "--db-url",
        type=str,
        help="Database URL",
    )

    # Security settings
    parser.add_argument(
        "--jwt-secret",
        type=str,
        help="JWT secret key",
    )
    parser.add_argument(
        "--bootstrap-key",
        type=str,
        help="Bootstrap key for admin creation",
    )

    # Data seeding options
    parser.add_argument(
        "--seed-rbac",
        action="store_true",
        help="Seed RBAC data",
    )
    parser.add_argument(
        "--seed-sample-data",
        action="store_true",
        help="Seed sample data",
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip all data seeding",
    )

    # Admin user creation
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create admin user",
    )
    parser.add_argument("--admin-username", type=str, help="Admin username")
    parser.add_argument("--admin-email", type=str, help="Admin email")
    parser.add_argument("--admin-password", type=str, help="Admin password")
    parser.add_argument(
        "--admin-role",
        type=str,
        default="super_admin",
        help="Role assigned to admin",
    )

    # Confirmation flags
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts",
    )

    return parser


def generate_random_key(length: int = 32) -> str:
    """Generate a random key for JWT or bootstrap."""
    import secrets

    return secrets.token_urlsafe(length)


def update_env_file(settings: dict) -> None:
    """Update .env file with provided settings."""
    env_file = Path(".env")
    env_example = Path(".env.example")

    # Create .env from .env.example if it doesn't exist
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Created .env from .env.example")

    if not env_file.exists():
        print("⚠️  Warning: No .env file found. Creating new one.")
        env_file.write_text(
            "# Database\nDATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/erp_db\n\n"
        )

    # Read existing content
    content = env_file.read_text()
    lines = content.splitlines()

    # Update or add settings
    for key, value in settings.items():
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                key_found = True
                break
        if not key_found:
            lines.append(f"{key}={value}")

    # Write back
    env_file.write_text("\n".join(lines) + "\n")
    print("✅ Updated .env file")


def get_input(prompt: str, default: Optional[str] = None, password: bool = False) -> str:
    """Get user input with optional default value."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    if password:
        import getpass

        value = getpass.getpass(prompt)
    else:
        value = input(prompt)

    return value.strip() or default if default else value.strip()


def encode_for_url(value: str) -> str:
    """URL encode special characters in connection string values."""
    from urllib.parse import quote_plus

    return quote_plus(value)


def get_db_session(db_url: str) -> AsyncSession:
    """Create a fresh database session with the correct database URL."""
    engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )
    return SessionLocal()


def confirm(prompt: str, default: bool = True) -> bool:
    """Get yes/no confirmation from user."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} ({default_str}): ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


async def test_database_connection(url: str, db_name: Optional[str] = None) -> tuple[bool, str]:
    """
    Test database connection.

    Returns:
        tuple[bool, str]: (success, error_message)
    """
    try:
        engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.execute(select(1))
        await engine.dispose()
        return True, ""
    except Exception as e:
        return False, str(e)


async def create_database(
    postgres_url: str, database_name: str, host: str, port: str, username: str
) -> tuple[bool, str]:
    """
    Create a new database.

    Returns:
        tuple[bool, str]: (success, error_message)
    """
    try:
        # Use AUTOCOMMIT isolation level for CREATE DATABASE
        engine = create_async_engine(
            postgres_url, echo=False, isolation_level="AUTOCOMMIT", pool_pre_ping=True
        )

        async with engine.connect() as conn:
            # Check if database already exists using proper SQLAlchemy text()
            check_query = text("SELECT 1 FROM pg_database WHERE datname = :db_name")
            result = await conn.execute(check_query, {"db_name": database_name})
            exists = result.scalar()

            if not exists:
                # Create database using text() for raw SQL
                create_query = text(f'CREATE DATABASE "{database_name}"')
                await conn.execute(create_query)

        await engine.dispose()
        return True, ""
    except Exception as e:
        return False, str(e)


async def interactive_install() -> int:
    """Run interactive installation process."""
    print("🚀 Welcome to Ramonyxs ERP Backend Installation Wizard")
    print("=" * 60)
    print()

    # Step 1: Environment Configuration
    print("📋 Step 1: Environment Configuration")
    print("-" * 40)

    env = get_input(
        "Environment type",
        default="development",
    )
    while env not in ["development", "production"]:
        print("❌ Please enter 'development' or 'production'")
        env = get_input(
            "Environment type",
            default="development",
        )

    debug = confirm("Enable debug mode", default=(env == "development"))

    print()

    # Step 2: Database Configuration
    print("🗄️  Step 2: Database Configuration")
    print("-" * 40)

    # Database configuration loop - allow retry
    db_url = None
    while db_url is None:
        print("Please enter your database connection details:")

        host = get_input("Database host", default="localhost")
        port = get_input("Database port", default="5432")
        username = get_input("Database username", default="postgres")
        password = get_input("Database password", password=True)
        database = get_input("Database name", default="erp_db")

        # Ask about SSL for production
        use_ssl = False
        if env == "production":
            use_ssl = confirm("Use SSL connection?", default=True)

        # URL encode credentials to handle special characters
        encoded_password = encode_for_url(password)
        encoded_username = encode_for_url(username)

        # Construct database URLs
        ssl_param = "?ssl=require" if use_ssl else ""
        postgres_test_url = f"postgresql+asyncpg://{encoded_username}:{encoded_password}@{host}:{port}/postgres{ssl_param}"
        target_db_url = f"postgresql+asyncpg://{encoded_username}:{encoded_password}@{host}:{port}/{database}{ssl_param}"

        # Test database connection
        print("\n🔍 Testing database connection...")

        # Step 1: Verify credentials against postgres database
        print("   → Verifying credentials...")
        success, error = await test_database_connection(postgres_test_url, "postgres")

        if not success:
            print(f"❌ Authentication failed: {error}")
            print("\n🔑 Common issues:")
            print("   - Incorrect password")
            print("   - User doesn't exist")
            print("   - PostgreSQL not running")
            print("   - Connection refused (check host/port)")
            print(f"\n💡 Try manually: psql -h {host} -p {port} -U {username} -d postgres")

            if not confirm("\nRetry with different credentials?", default=True):
                if confirm("Continue anyway? (Not recommended)", default=False):
                    db_url = target_db_url
                    break
                print("Installation cancelled.")
                return 1
            # Loop continues to retry
            print("\n" + "=" * 50 + "\n")
            continue

        print("✅ Credentials verified")

        # Step 2: Test connection to target database
        print(f"   → Connecting to database '{database}'...")
        success, error = await test_database_connection(target_db_url, database)

        if not success:
            error_lower = error.lower()

            # Check if database doesn't exist
            if "database" in error_lower and (
                "does not exist" in error_lower or f'"{database}"' in error_lower
            ):
                print(f"⚠️  Database '{database}' does not exist")

                if confirm(f"Create database '{database}'?", default=True):
                    print(f"🔧 Creating database '{database}'...")

                    create_success, create_error = await create_database(
                        postgres_test_url, database, host, port, username
                    )

                    if create_success:
                        print(f"✅ Database '{database}' created successfully!")

                        # Verify connection to new database
                        print("   → Verifying new database connection...")
                        verify_success, verify_error = await test_database_connection(
                            target_db_url, database
                        )

                        if verify_success:
                            print(f"✅ Connection to '{database}' verified!")
                            db_url = target_db_url
                            break
                        print(f"❌ Failed to connect to new database: {verify_error}")
                        if not confirm("Retry?", default=True):
                            print("Installation cancelled.")
                            return 1
                    else:
                        print(f"❌ Failed to create database: {create_error}")
                        print("\n💡 You can create it manually:")
                        print(f"   createdb -h {host} -p {port} -U {username} {database}")
                        print(
                            f"   OR: psql -h {host} -p {port} -U {username} -d postgres -c 'CREATE DATABASE \"{database}\";'"
                        )

                        if not confirm("Retry?", default=True):
                            if confirm("Continue without database?", default=False):
                                db_url = target_db_url
                                break
                            print("Installation cancelled.")
                            return 1
                else:
                    print("❌ Database is required for installation.")
                    if not confirm("Retry?", default=True):
                        print("Installation cancelled.")
                        return 1
            else:
                # Other connection errors
                print(f"❌ Database connection failed: {error}")
                print("\n🔧 Troubleshooting:")
                print("   1. Ensure PostgreSQL is running")
                print("   2. Check firewall/network settings")
                print("   3. Verify pg_hba.conf allows connections")
                print(f"   4. Test manually: psql -h {host} -p {port} -U {username} -d {database}")

                if not confirm("Retry with different settings?", default=True):
                    if confirm("Continue anyway?", default=False):
                        db_url = target_db_url
                        break
                    print("Installation cancelled.")
                    return 1

            # Loop continues to retry
            print("\n" + "=" * 50 + "\n")
        else:
            print(f"✅ Successfully connected to database '{database}'!")
            db_url = target_db_url
            break

    print()

    # Step 3: Security Configuration
    print("🔐 Step 3: Security Configuration")
    print("-" * 40)

    generate_jwt = confirm("Generate new JWT secret key", default=True)
    if generate_jwt:
        jwt_secret = generate_random_key()
        print("✅ Generated new JWT secret key")
    else:
        jwt_secret = get_input("JWT secret key")

    generate_bootstrap = confirm("Generate new bootstrap key", default=True)
    if generate_bootstrap:
        bootstrap_key = generate_random_key()
        print("✅ Generated new bootstrap key")
    else:
        bootstrap_key = get_input("Bootstrap key")

    print()

    # Step 4: Update Environment File
    print("⚙️  Step 4: Update Configuration")
    print("-" * 40)

    env_settings = {
        "APP_ENV": env,
        "DEBUG": str(debug),
        "DATABASE_URL": db_url,
        "JWT_SECRET_KEY": jwt_secret,
        "BOOTSTRAP_KEY": bootstrap_key,
    }

    if confirm("Update .env file with these settings?", default=True):
        update_env_file(env_settings)
        # Update environment variable for current session
        os.environ["DATABASE_URL"] = db_url
    else:
        print("⚠️  Skipping .env file update")
        # Still set for current session
        os.environ["DATABASE_URL"] = db_url

    print()

    # Step 5: Database Operations
    print("🗃️  Step 5: Database Setup")
    print("-" * 40)

    # Check if we need to run migrations
    if confirm("Run database migrations?", default=True):
        print("\n🔄 Running migrations...")
        try:
            import subprocess  # nosec B404 - subprocess needed for alembic migration

            result = subprocess.run(  # nosec
                ["uv", "run", "alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                env={**os.environ, "DATABASE_URL": db_url},
            )
            if result.returncode == 0:
                print("✅ Migrations completed successfully!")
                if result.stdout:
                    print(f"   {result.stdout.strip()}")
            else:
                print("❌ Migration failed:")
                if result.stderr:
                    print(f"   {result.stderr.strip()}")
                if result.stdout:
                    print(f"   {result.stdout.strip()}")
                if not confirm("Continue without migrations?"):
                    return 1
        except FileNotFoundError:
            print("❌ Error: 'uv' command not found")
            print("💡 Install uv or run migrations manually:")
            print("   alembic upgrade head")
            if not confirm("Continue without migrations?"):
                return 1
        except Exception as e:
            print(f"❌ Error running migrations: {e}")
            if not confirm("Continue without migrations?"):
                return 1

    print()

    # Step 6: Data Seeding
    print("🌱 Step 6: Data Seeding")
    print("-" * 40)

    seed_rbac_data = confirm("Seed RBAC data (permissions, roles)?", default=True)
    seed_sample = confirm("Seed sample data (suppliers, customers, products)?", default=True)

    if not (seed_rbac_data or seed_sample):
        print("⚠️  Skipping all data seeding")
    else:
        if confirm("Proceed with data seeding?", default=True):
            # Create fresh session with correct database URL
            db = get_db_session(db_url)
            try:
                if seed_rbac_data:
                    print("\n📋 Seeding RBAC data...")
                    summary = await seed_rbac(db)
                    print(
                        f"✅ RBAC seed complete: "
                        f"permissions={summary['permissions_created']}, "
                        f"roles={summary['roles_created']}, "
                        f"links={summary['role_permission_links_added']}"
                    )

                if seed_sample:
                    print("\n🌱 Seeding sample data...")
                    summary = await seed_sample_data(db)
                    print("✅ Sample data seed complete:")
                    for key, value in summary.items():
                        print(f"   • {key}: {value}")

            except Exception as exc:
                print(f"❌ Data seeding failed: {exc}")
                import traceback

                traceback.print_exc()
                if not confirm("Continue despite seeding errors?"):
                    return 4
            finally:
                await db.close()

    print()

    # Step 7: Admin User Creation
    print("👤 Step 7: Admin User Creation")
    print("-" * 40)

    create_admin = confirm("Create admin user?", default=True)

    if create_admin:
        print("\nPlease provide admin user details:")

        while True:
            username = get_input("Username")
            if username and len(username) >= 3:
                break
            print("❌ Username must be at least 3 characters")

        while True:
            email = get_input("Email")
            if email and "@" in email and "." in email.split("@")[1]:
                break
            print("❌ Valid email is required (e.g., admin@example.com)")

        while True:
            password = get_input("Password", password=True)
            if not password:
                print("❌ Password is required")
                continue
            if len(password) < 8:
                print("❌ Password must be at least 8 characters")
                continue

            password_confirm = get_input("Confirm password", password=True)
            if password == password_confirm:
                break
            print("❌ Passwords do not match")

        role = get_input("Role", default="super_admin")

        print(f"\n🔍 Creating admin user: {username} ({email}) with role '{role}'")

        # Create fresh session with correct database URL
        db = get_db_session(db_url)
        try:
            # Check if users already exist
            user_count = await db.scalar(select(func.count()).select_from(User))
            if user_count and user_count > 0:
                print(f"⚠️  Warning: {user_count} user(s) already exist in the database")
                if not confirm("Continue creating admin user?", default=True):
                    print("Admin creation skipped.")
                else:
                    await bootstrap_admin_user(
                        db,
                        username=username,
                        email=email,
                        password=password,
                        role_name=role,
                    )
                    print(f"✅ Admin user created: {username}")
            else:
                await bootstrap_admin_user(
                    db,
                    username=username,
                    email=email,
                    password=password,
                    role_name=role,
                )
                print(f"✅ Admin user created: {username}")

        except BootstrapError as exc:
            print(f"❌ Admin creation failed: {exc}")
            if not confirm("Continue anyway?", default=True):
                return 1
        except Exception as exc:
            print(f"❌ Unexpected error during admin creation: {exc}")
            import traceback

            traceback.print_exc()
            if not confirm("Continue anyway?", default=True):
                return 1
        finally:
            await db.close()

    print()

    # Step 8: Installation Complete
    print("🎉 Installation Completed Successfully!")
    print("=" * 60)
    print()
    print("📝 Summary:")
    print(f"   • Environment: {env}")
    print(f"   • Debug mode: {'Enabled' if debug else 'Disabled'}")
    print(f"   • Database: {database}@{host}:{port}")
    print(f"   • SSL: {'Enabled' if use_ssl else 'Disabled'}")
    print()
    print("🚀 Next steps:")
    print("   1. Review your .env file")
    print("   2. Start the server:")
    print("      uv run uvicorn app.main:app --reload")
    if env == "development":
        print("   3. Access API documentation:")
        print("      http://localhost:8000/docs")
        print("   4. Login with your admin credentials")
    print()
    print("Your ERP backend is ready to use! 🚀")

    return 0


def _require_admin_args(args: argparse.Namespace) -> None:
    """Check if required admin arguments are provided."""
    missing = [
        flag
        for flag, value in {
            "--admin-username": args.admin_username,
            "--admin-email": args.admin_email,
            "--admin-password": args.admin_password,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing required args for --create-admin: {', '.join(missing)}")


async def _run_non_interactive(args: argparse.Namespace) -> int:
    """Run non-interactive installation with provided arguments."""
    print("🚀 Starting ERP Backend Installation (Non-Interactive)...\n")

    # Prepare environment settings
    env_settings = {}

    if args.env:
        env_settings["APP_ENV"] = args.env
        print(f"Environment: {args.env}")

    if args.debug is not None:
        env_settings["DEBUG"] = str(args.debug)
        print(f"Debug mode: {args.debug}")

    if args.db_url:
        env_settings["DATABASE_URL"] = args.db_url
        print("Database URL: [CONFIGURED]")
        # Test connection if URL provided
        print("🔍 Testing database connection...")
        success, error = await test_database_connection(args.db_url)
        if success:
            print("✅ Database connection successful")
        else:
            print(f"⚠️  Database connection failed: {error}")
            if not args.force:
                print("❌ Aborting. Use --force to continue anyway.")
                return 1

    if args.jwt_secret:
        env_settings["JWT_SECRET_KEY"] = args.jwt_secret
        print("JWT secret: [PROVIDED]")
    else:
        jwt_secret = generate_random_key()
        env_settings["JWT_SECRET_KEY"] = jwt_secret
        print("JWT secret: [GENERATED]")

    if args.bootstrap_key:
        env_settings["BOOTSTRAP_KEY"] = args.bootstrap_key
        print("Bootstrap key: [PROVIDED]")
    else:
        bootstrap_key = generate_random_key()
        env_settings["BOOTSTRAP_KEY"] = bootstrap_key
        print("Bootstrap key: [GENERATED]")

    # Update .env file
    if env_settings:
        update_env_file(env_settings)
        # Set DATABASE_URL for current session
        if "DATABASE_URL" in env_settings:
            os.environ["DATABASE_URL"] = env_settings["DATABASE_URL"]

    print("\n" + "=" * 50)

    # Check if we should proceed with database operations
    if args.no_seed:
        print("⚠️  Skipping all database operations (--no-seed flag)")
        return 0

    # Create database session
    db_url = env_settings.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ No database URL configured")
        return 1

    db = get_db_session(db_url)
    try:
        # Seed RBAC
        if args.seed_rbac:
            print("\n📋 Seeding RBAC...")
            summary = await seed_rbac(db)
            print(
                f"✅ RBAC seed complete: "
                f"permissions={summary['permissions_created']}, "
                f"roles={summary['roles_created']}, "
                f"links={summary['role_permission_links_added']}"
            )

        # Seed sample data
        if args.seed_sample_data:
            print("\n🌱 Seeding sample data...")
            summary = await seed_sample_data(db)
            print("✅ Sample data seed complete:")
            for key, value in summary.items():
                print(f"   • {key}: {value}")

        # Create admin user
        if args.create_admin:
            print("\n👤 Creating admin user...")
            _require_admin_args(args)

            try:
                user = await bootstrap_admin_user(
                    db,
                    username=args.admin_username,
                    email=args.admin_email,
                    password=args.admin_password,
                    role_name=args.admin_role,
                )
                print(
                    f"✅ Admin user created: "
                    f"username={user.username}, "
                    f"email={user.email}, "
                    f"role={args.admin_role}"
                )
            except BootstrapError as exc:
                print(f"❌ Admin creation failed: {exc}")
                return 3

    except Exception as exc:
        print(f"❌ Installation failed: {exc}")
        import traceback

        traceback.print_exc()
        return 4
    finally:
        await db.close()

    print("\n🎉 Installation completed successfully!")
    print("\n🚀 Next steps:")
    print("   1. Review your .env file")
    print("   2. Start the server:")
    print("      uv run uvicorn app.main:app --reload")
    print("   3. Access API documentation:")
    print("      http://localhost:8000/docs")

    return 0


async def _run(args: argparse.Namespace) -> int:
    # Handle conflicting options
    if args.no_seed and (args.seed_rbac or args.seed_sample_data or args.create_admin):
        print(
            "❌ Error: --no-seed conflicts with --seed-rbac, --seed-sample-data, or --create-admin"
        )
        sys.exit(1)

    # Choose installation mode
    if args.non_interactive:
        return await _run_non_interactive(args)
    return await interactive_install()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        code = asyncio.run(_run(args))
        raise SystemExit(code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        raise SystemExit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
