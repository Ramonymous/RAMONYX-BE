from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import FetchedValue


class Base(DeclarativeBase):
    """Base class untuk semua models SQLAlchemy"""

    pass


class TimestampMixin:
    """
    Mixin created_at + updated_at untuk semua model yang perlu audit timestamp.

    - created_at  : di-set otomatis oleh DB via server_default=NOW(), tidak pernah diubah.
    - updated_at  : di-set via server_default dan di-refresh oleh trigger DB.
                    server_onupdate=FetchedValue() memberitahu SQLAlchemy untuk
                    EXPIRE kolom ini setelah UPDATE, sehingga nilai terbaru
                    di-fetch dari DB saat diakses berikutnya.

    PENTING: onupdate=lambda di Python TIDAK bekerja untuk server_default berbasis
    DB. Gunakan trigger PostgreSQL (lihat catatan SQL di migration) agar
    updated_at selalu konsisten, termasuk untuk UPDATE yang dilakukan langsung
    via raw SQL atau tool lain di luar SQLAlchemy.
    """

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=FetchedValue(),
        nullable=False,
    )
