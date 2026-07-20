# Epic 4: Web UI Integration

**Goal:** Develop and integrate a Web API (using FastAPI) that runs alongside the bot. This API will consume the Services layer to power a frontend dashboard for managing the bot outside of Discord.

## User Stories

### Story 4.1: Develop REST API (FastAPI)
- **As a** developer,
- **I want** to create a FastAPI backend,
- **So that** the bot's data (admins, logs, configurations) can be requested via HTTP.
- **Tasks:**
  - Install `fastapi` and `uvicorn`.
  - Create `src/api/routes.py` exposing endpoints like `GET /api/guilds/{id}/config`.
  - Connect the API endpoints to the existing Services layer.

### Story 4.2: Concurrent Execution
- **As a** developer,
- **I want** to run the FastAPI server and the `disnake` bot within the same process/container,
- **So that** they can seamlessly share the same database connection pool and memory state.
- **Tasks:**
  - Modify `main.py` to launch the FastAPI `uvicorn` server using an `asyncio.create_task()` or via Hypercorn alongside the Discord client loop.

### Story 4.3: Build Minimal Frontend (Optional)
- **As a** user,
- **I want** a web interface to view bot statistics and manage settings,
- **So that** I don't have to rely exclusively on Discord slash commands and Modals.
- **Tasks:**
  - Serve static HTML/JS/CSS files via FastAPI (or set up a separate React/Vue project) to interact with the API endpoints.
