from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models import Base

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency untuk mendapatkan database session.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    async with SessionLocal() as db:
        yield db


async def init_db() -> None:
    """
    Initialize database - create all tables.

    Usage:
        from app.database import init_db
        init_db()

    PENTING: Di production, gunakan Alembic untuk migrations!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
