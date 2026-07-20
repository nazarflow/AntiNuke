# tests/conftest.py
# Shared pytest fixtures.
# Sets up a fresh in-memory SQLite database for every test session.

import os
import asyncio
import pytest
import pytest_asyncio

# Point at in-memory SQLite before any application module is imported
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("TOKEN", "fake-token")

from src.database import init_db


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables once before any test runs."""
    await init_db()
