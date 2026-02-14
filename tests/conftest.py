"""
Test configuration and fixtures for the ERP backend.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.auth import Permission, Role, User
from app.models.base import Base


# Load test database URL from .env.test file
def load_test_env():
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.test")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value


# Load environment variables
load_test_env()

# Test database URL from environment variable or fallback
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:IPkmqb1V@localhost:5432/erp_test_db")

# Create test engine with connection pooling
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=StaticPool,
    pool_pre_ping=True,
    connect_args={"server_settings": {"application_name": "erp_test_suite"}},
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create a new engine for each test to avoid connection conflicts
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=StaticPool,
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""

    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    from httpx import ASGITransport

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with super_admin role."""
    # Create permissions
    permissions = [
        Permission(id=uuid4(), code="users:read", description="Can read users"),
        Permission(id=uuid4(), code="users:create", description="Can create users"),
        Permission(id=uuid4(), code="users:update", description="Can update users"),
        Permission(id=uuid4(), code="users:delete", description="Can delete users"),
        Permission(id=uuid4(), code="inventory:read", description="Can read inventory"),
        Permission(id=uuid4(), code="inventory:create", description="Can create inventory"),
        Permission(id=uuid4(), code="inventory:update", description="Can update inventory"),
        Permission(id=uuid4(), code="inventory:delete", description="Can delete inventory"),
    ]

    for permission in permissions:
        db_session.add(permission)

    # Create role
    super_admin_role = Role(
        id=uuid4(),
        name="super_admin",
        description="Super Administrator",
    )
    super_admin_role.permissions.extend(permissions)
    db_session.add(super_admin_role)

    # Create user
    test_user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=True,
    )
    test_user.roles.append(super_admin_role)
    db_session.add(test_user)

    await db_session.commit()
    await db_session.refresh(test_user)

    return test_user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    from app.core.security import create_access_token

    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
from sqlalchemy import select

async def sample_permissions(db_session: AsyncSession) -> list[Permission]:
    """Create sample permissions for testing."""
    permissions_data = [
        ("inventory:read", "Can read inventory data"),
        ("inventory:create", "Can create inventory data"),
        ("inventory:update", "Can update inventory data"),
        ("inventory:delete", "Can delete inventory data"),
        ("sales:create", "Can create sales data"),
        ("sales:update", "Can update sales data"),
        ("sales:delete", "Can delete sales data"),
        ("warehouse:read", "Can read warehouse data"),
    ]

    permissions = []
    for code, description in permissions_data:
        result = await db_session.execute(
            select(Permission).where(Permission.code == code)
        )
        existing = result.scalars().first()
        if not existing:
            permission = Permission(id=uuid4(), code=code, description=description)
            db_session.add(permission)
            permissions.append(permission)
        else:
            permissions.append(existing)

    await db_session.commit()
    return permissions


@pytest_asyncio.fixture(scope="function")
async def sample_role(db_session: AsyncSession, sample_permissions: list[Permission]) -> Role:
    """Create a sample role with inventory permissions."""
    inventory_permissions = [p for p in sample_permissions if p.code.startswith("inventory:")]

    role = Role(
        id=uuid4(),
        name="inventory_manager",
        description="Inventory Manager",
    )
    role.permissions.extend(inventory_permissions)
    db_session.add(role)

    await db_session.commit()
    await db_session.refresh(role)

    return role


@pytest_asyncio.fixture(scope="function")
async def inventory_user(db_session: AsyncSession, sample_role: Role) -> User:
    """Create a user with inventory manager role."""
    user = User(
        id=uuid4(),
        username="inventory_user",
        email="inventory@example.com",
        hashed_password=hash_password("inventory_password"),
        is_active=True,
    )
    user.roles.append(sample_role)
    db_session.add(user)

    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def inventory_auth_headers(inventory_user: User) -> dict:
    """Create authentication headers for inventory user."""
    from app.core.security import create_access_token

    access_token = create_access_token(subject=str(inventory_user.id))
    return {"Authorization": f"Bearer {access_token}"}


# Markers for different test categories
pytest_plugins: list[str] = []


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line("markers", "inventory: mark test as inventory related")
    config.addinivalue_line("markers", "production: mark test as production related")
    config.addinivalue_line("markers", "purchasing: mark test as purchasing related")
    config.addinivalue_line("markers", "sales: mark test as sales related")
    config.addinivalue_line("markers", "users: mark test as user management related")
    config.addinivalue_line("markers", "warehouse: mark test as warehouse related")
