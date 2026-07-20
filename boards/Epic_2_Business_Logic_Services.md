# Epic 2: Business Logic & Services Abstraction

**Goal:** Refactor the Discord Cogs (presentation layer) to delegate business rules and data interactions to a dedicated Services layer. This ensures Clean Architecture compliance and allows a Web UI to reuse the same logic.

## User Stories

### Story 2.1: Extract Business Services
- **As a** developer,
- **I want** to create a Services layer to encapsulate core bot logic (e.g., limit tracking, admin management),
- **So that** the Discord API is solely responsible for input/output, not decision-making.
- **Tasks:**
  - Create `src/services/admin_service.py` for managing owners and admins.
  - Create `src/services/limits_service.py` for tracking logic.
  - Create `src/services/config_service.py` for guild settings.

### Story 2.2: Refactor Discord UI (Cogs)
- **As a** developer,
- **I want** to update `dev_panel.py` and `admin_panel.py` to use the new Services,
- **So that** no direct database interactions occur within UI Modals or Views.
- **Tasks:**
  - Replace `database.save_guild_roles()` calls with `await config_service.update_roles()`.
  - Remove all inline `cursor.execute()` statements from `cogs/`.

### Story 2.3: Refactor Event Trackers
- **As a** developer,
- **I want** to update event listeners (e.g., `channels_tracker.py`) to query the Services layer,
- **So that** rate-limiting and punishment logic is centralized and easily testable.
- **Tasks:**
  - Route all limit-checking through `limits_service`.
