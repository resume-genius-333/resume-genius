# Production Dockerfile for Backend
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies for building including git for GitHub dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install production dependencies
RUN uv sync --no-dev

# Production stage
FROM python:3.13-slim AS runner

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 appuser

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

USER appuser

# Set Python path to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Start production server without reload
CMD ["python", "main.py"]