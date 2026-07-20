# src/database/engine.py
# Async SQLAlchemy engine and session factory.
# Reads DATABASE_URL from environment — supports both SQLite (dev) and PostgreSQL (prod).

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base

# ------------------------------------------------------------------------------------------------ #
# Engine setup
# ------------------------------------------------------------------------------------------------ #

# Default to local SQLite so the bot works out-of-the-box without Docker.
# Override with a PostgreSQL URL in .env for production:
#   DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/antinuke
_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

_engine = create_async_engine(
    _DATABASE_URL,
    echo=False,           # Set True to log all SQL (useful for debugging)
    pool_pre_ping=True,   # Verify connections before use (important for PG)
)

_SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ------------------------------------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------------------------------------ #

async def init_db() -> None:
    """Create all tables that do not yet exist. Safe to call on every startup."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Async context manager that yields a database session and handles commit/rollback."""
    async with _SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
