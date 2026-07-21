# Epic 1: Database ORM Migration & PostgreSQL Readiness

**Goal:** Replace the synchronous, raw `sqlite3` queries with an asynchronous ORM (SQLAlchemy 2.0). This resolves event-loop blocking issues and creates a database-agnostic repository layer, paving the way for PostgreSQL integration in Docker.

## User Stories

### Story 1.1: Define ORM Models
- **As a** developer,
- **I want** to define database tables as SQLAlchemy declarative models,
- **So that** the database schema is managed in code and is independent of the underlying SQL dialect.
- **Tasks:**
  - Create `src/database/models.py`.
  - Define `Admin`, `TrackedUser`, `GuildConfig`, `GuildRole`, `GuildLogChannel`, `GuildLimit`, `CustomRoleLimit`, `ServerOwner`, `CustomUserLimit` models.

### Story 1.2: Implement Repository Pattern
- **As a** developer,
- **I want** to create a Repository layer to handle all database operations,
- **So that** no raw SQL exists in the application and business logic is decoupled from data access.
- **Tasks:**
  - Create `src/database/repository.py`.
  - Implement async CRUD operations using SQLAlchemy sessions (e.g., `get_admin()`, `save_guild_roles()`).

### Story 1.3: Data Migration (Optional/As Needed)
- **As a** developer,
- **I want** to ensure existing data can be migrated or we gracefully transition to the new schema,
- **So that** the bot's state is preserved if requested by the owner.
- **Tasks:**
  - Write a one-time migration script (or configure Alembic) if preserving SQLite data for the PostgreSQL switch is necessary.
