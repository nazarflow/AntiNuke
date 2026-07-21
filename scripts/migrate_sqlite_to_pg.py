"""
scripts/migrate_sqlite_to_pg.py
--------------------------------
One-time migration script to transfer all data from the existing SQLite database
to a PostgreSQL database using SQLAlchemy.

Usage:
    1. Make sure the target PostgreSQL database is running and empty.
    2. Set SOURCE_DATABASE_URL and TARGET_DATABASE_URL in your environment or edit them below.
    3. Run: python scripts/migrate_sqlite_to_pg.py

The script will:
    - Apply all Alembic migrations to the target PostgreSQL DB (creates schema).
    - Read every row from every table in the source SQLite file.
    - Insert those rows into the PostgreSQL tables.
    - Print a summary at the end.
"""

import asyncio
import os
import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# ------------------------------------------------------------------------------------------------ #
# Configuration
# ------------------------------------------------------------------------------------------------ #

SOURCE_URL = os.getenv(
    "SOURCE_DATABASE_URL",
    "sqlite+aiosqlite:///./database.db",    # existing SQLite file
)
TARGET_URL = os.getenv(
    "TARGET_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/antinuke",  # target PG
)

# Tables to migrate, in insertion order (respects FK constraints if any are added later).
TABLES = [
    "admins",
    "tracked_users",
    "guild_configs",
    "guild_roles",
    "guild_log_channels",
    "guild_limits",
    "custom_role_limits",
    "server_owners",
    "custom_user_limits",
]


# ------------------------------------------------------------------------------------------------ #
# Migration logic
# ------------------------------------------------------------------------------------------------ #

async def migrate() -> None:
    print("=" * 60)
    print("  AntiNuke -- SQLite to PostgreSQL Migration")
    print("=" * 60)

    # Step 1: Apply Alembic migrations to the target DB to create the schema.
    print("\n[1/3] Applying Alembic migrations to target database...")
    env = os.environ.copy()
    env["DATABASE_URL"] = TARGET_URL
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  ❌ Alembic failed:")
        print(result.stderr)
        sys.exit(1)
    print("  ✅ Schema applied.")

    source_engine = create_async_engine(SOURCE_URL, echo=False)
    target_engine = create_async_engine(TARGET_URL, echo=False)

    SessionFactory = async_sessionmaker(bind=target_engine, expire_on_commit=False)

    print("\n[2/3] Migrating data table by table...")
    total_rows = 0

    async with source_engine.connect() as src_conn:
        async with SessionFactory() as tgt_session:
            for table in TABLES:
                rows = (await src_conn.execute(text(f"SELECT * FROM {table}"))).mappings().all()
                if not rows:
                    print(f"  ⏭️  {table}: empty, skipping.")
                    continue

                # Convert RowMapping objects to plain dicts
                dicts = []
                for row in rows:
                    d = dict(row)
                    if table == "guild_roles":
                        d.pop("dvp_id", None)
                    dicts.append(d)

                # Build a parameterised INSERT … ON CONFLICT DO NOTHING
                columns = list(dicts[0].keys())
                col_str = ", ".join(columns)
                val_str = ", ".join(f":{c}" for c in columns)
                stmt = text(
                    f"INSERT INTO {table} ({col_str}) VALUES ({val_str}) ON CONFLICT DO NOTHING"
                )
                await tgt_session.execute(stmt, dicts)
                print(f"  ✅ {table}: {len(dicts)} rows migrated.")
                total_rows += len(dicts)

            await tgt_session.commit()

    await source_engine.dispose()
    await target_engine.dispose()

    print(f"\n[3/3] Done! Total rows migrated: {total_rows}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate())
