# ==============================================================================
# Stage 1 — Builder: install dependencies into a clean virtual environment
# ==============================================================================
FROM python:3.10-slim AS builder

WORKDIR /install

# Copy only the dependency manifest first (maximises Docker layer cache)
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt


# ==============================================================================
# Stage 2 — Runtime: minimal image, no build tools
# ==============================================================================
FROM python:3.10-slim AS runtime

# Security: run as a non-root user
RUN useradd --create-home --shell /bin/bash antinuke
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install/deps /usr/local

# Copy the application source
COPY --chown=antinuke:antinuke . .

# Switch to non-root user
USER antinuke

# Alembic migrations run first, then the bot starts.
# The entrypoint script handles both steps cleanly.
CMD ["sh", "-c", "python -m alembic upgrade head && python main.py"]
