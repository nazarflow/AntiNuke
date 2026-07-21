# Epic 3: Dockerization & CI/CD Pipelines

**Goal:** Containerize the application and database for easy deployment and scale. Establish an automated testing pipeline to verify the newly decoupled business logic on every change.

## User Stories

### Story 3.1: Containerize Application and Database
- **As a** DevOps engineer,
- **I want** to create a multi-container environment using Docker,
- **So that** the bot and its PostgreSQL database run consistently across any machine.
- **Tasks:**
  - Write a `Dockerfile` for the Python bot environment.
  - Write a `docker-compose.yml` defining the `bot` and `db` (PostgreSQL) services.
  - Update `config.py` to read `DATABASE_URL` from the `.env` file.

### Story 3.2: Implement Automated Testing (Unit Tests)
- **As a** developer,
- **I want** to write unit tests for the decoupled Services and Repository layers,
- **So that** I can confidently verify business logic without running the Discord bot.
- **Tasks:**
  - Install `pytest` and `pytest-asyncio`.
  - Write tests for `admin_service.py` using an in-memory SQLite database.

### Story 3.3: Set up CI/CD Pipeline
- **As a** DevOps engineer,
- **I want** to configure a CI pipeline (e.g., GitHub Actions),
- **So that** tests are automatically run and code quality is validated on every push or PR.
- **Tasks:**
  - Create `.github/workflows/ci.yml`.
  - Configure the pipeline to run syntax checks and the `pytest` suite.
