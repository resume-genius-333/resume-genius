# Resume Genius Project Commands
# Run 'just' or 'just help' to see available commands

# Load environment variables
set dotenv-load := true

# Set shell for Windows compatibility
set windows-shell := ["powershell.exe", "-c"]

# Default Docker Compose files
compose_dir := "infrastructure/docker"
compose_file := compose_dir + "/docker-compose.yml"
compose_prod := compose_dir + "/docker-compose.prod.yml"

# Colors for output
export BLUE := '\033[0;34m'
export GREEN := '\033[0;32m'
export YELLOW := '\033[1;33m'
export RED := '\033[0;31m'
export NC := '\033[0m' # No Color

# Default recipe - show help
default:
    @just --list --unsorted

# Alias for common commands
alias u := up
alias d := down
alias l := logs
alias r := restart

# ============================================================================
# Docker Commands
# ============================================================================

# Start all services in development mode with hot reload
up:
    @echo "{{GREEN}}Starting services in development mode...{{NC}}"
    cd {{compose_dir}} && docker-compose up -d
    @echo "{{GREEN}}Services started!{{NC}}"
    @echo "Frontend: http://localhost:3000"
    @echo "Backend:  http://localhost:8000"
    @echo "LiteLLM:  http://localhost:4000"

# Start all services in production mode
up-prod:
    @echo "{{YELLOW}}Starting services in production mode...{{NC}}"
    cd {{compose_dir}} && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    @echo "{{GREEN}}Production services started!{{NC}}"

# Stop all services
down:
    @echo "{{YELLOW}}Stopping all services...{{NC}}"
    cd {{compose_dir}} && docker-compose down
    @echo "{{GREEN}}Services stopped!{{NC}}"

# View logs for a specific service (or all if no service specified)
logs service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        cd {{compose_dir}} && docker-compose logs -f
    else
        cd {{compose_dir}} && docker-compose logs -f {{service}}
    fi

# Restart a specific service (or all if no service specified)
restart service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        echo "{{YELLOW}}Restarting all services...{{NC}}"
        cd {{compose_dir}} && docker-compose restart
    else
        echo "{{YELLOW}}Restarting {{service}}...{{NC}}"
        cd {{compose_dir}} && docker-compose restart {{service}}
    fi
    echo "{{GREEN}}Restart complete!{{NC}}"

# Build or rebuild Docker images
build service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        echo "{{BLUE}}Building all services...{{NC}}"
        cd {{compose_dir}} && docker-compose build
    else
        echo "{{BLUE}}Building {{service}}...{{NC}}"
        cd {{compose_dir}} && docker-compose build {{service}}
    fi

# Show status of all services
ps:
    @cd {{compose_dir}} && docker-compose ps

# Execute command in a running container
exec service command:
    cd {{compose_dir}} && docker-compose exec {{service}} {{command}}

# ============================================================================
# Backend Commands
# ============================================================================

# Run backend locally without Docker (requires Python environment)
backend-dev:
    @echo "{{GREEN}}Starting backend development server...{{NC}}"
    cd apps/backend && uv run python main.py

# Run database migrations
migrate:
    @echo "{{BLUE}}Running database migrations...{{NC}}"
    cd apps/backend && uv run alembic upgrade head

# Create a new migration
makemigration name:
    @echo "{{BLUE}}Creating migration: {{name}}{{NC}}"
    cd apps/backend && uv run alembic revision --autogenerate -m "{{name}}"

# Open Python shell with application context
backend-shell:
    @echo "{{BLUE}}Opening Python shell...{{NC}}"
    cd apps/backend && uv run python -i -c "from src.containers import Container; container = Container()"

# Run backend tests
backend-test:
    @echo "{{BLUE}}Running backend tests...{{NC}}"
    cd apps/backend && uv run pytest

# Format backend code
backend-format:
    @echo "{{BLUE}}Formatting backend code...{{NC}}"
    cd apps/backend && uv run ruff format .

# Lint backend code
backend-lint:
    @echo "{{BLUE}}Linting backend code...{{NC}}"
    cd apps/backend && uv run ruff check .

# Install backend dependencies
backend-install:
    @echo "{{BLUE}}Installing backend dependencies...{{NC}}"
    cd apps/backend && uv sync

# ============================================================================
# Frontend Commands
# ============================================================================

# Run frontend locally without Docker
frontend-dev:
    @echo "{{GREEN}}Starting frontend development server...{{NC}}"
    cd apps/frontend && pnpm run dev

# Build frontend for production
frontend-build:
    @echo "{{BLUE}}Building frontend for production...{{NC}}"
    cd apps/frontend && pnpm run build

# Run frontend linting
frontend-lint:
    @echo "{{BLUE}}Linting frontend code...{{NC}}"
    cd apps/frontend && pnpm run lint

# Run frontend type checking
frontend-typecheck:
    @echo "{{BLUE}}Type checking frontend code...{{NC}}"
    cd apps/frontend && pnpm exec tsc --noEmit

# Install frontend dependencies
frontend-install:
    @echo "{{BLUE}}Installing frontend dependencies...{{NC}}"
    cd apps/frontend && pnpm install

# Clean frontend build artifacts
frontend-clean:
    @echo "{{YELLOW}}Cleaning frontend build artifacts...{{NC}}"
    cd apps/frontend && rm -rf .next node_modules

# ============================================================================
# Database Commands
# ============================================================================

# Connect to PostgreSQL shell (Resume Genius DB)
db-shell:
    @echo "{{BLUE}}Connecting to Resume Genius database...{{NC}}"
    docker exec -it resume-genius-postgres psql -U postgres -d resume_genius

# Connect to LiteLLM PostgreSQL shell
db-shell-litellm:
    @echo "{{BLUE}}Connecting to LiteLLM database...{{NC}}"
    docker exec -it litellm-postgres psql -U postgres -d litellm

# Backup Resume Genius database
db-backup:
    @echo "{{BLUE}}Backing up Resume Genius database...{{NC}}"
    @mkdir -p backups
    docker exec resume-genius-postgres pg_dump -U postgres resume_genius > backups/resume_genius_$(date +%Y%m%d_%H%M%S).sql
    @echo "{{GREEN}}Backup saved to backups/{{NC}}"

# Restore Resume Genius database from backup
db-restore file:
    @echo "{{YELLOW}}Restoring database from {{file}}...{{NC}}"
    docker exec -i resume-genius-postgres psql -U postgres resume_genius < {{file}}
    @echo "{{GREEN}}Database restored!{{NC}}"

# Reset database (DANGEROUS - will delete all data!)
db-reset:
    @echo "{{RED}}WARNING: This will delete all data in the database!{{NC}}"
    @echo "Type 'yes' to continue:"
    @read -r confirm; \
    if [ "$$confirm" = "yes" ]; then \
        echo "{{YELLOW}}Resetting database...{{NC}}"; \
        docker exec resume-genius-postgres psql -U postgres -c "DROP DATABASE IF EXISTS resume_genius;"; \
        docker exec resume-genius-postgres psql -U postgres -c "CREATE DATABASE resume_genius;"; \
        just migrate; \
        echo "{{GREEN}}Database reset complete!{{NC}}"; \
    else \
        echo "{{YELLOW}}Cancelled{{NC}}"; \
    fi

# ============================================================================
# Utility Commands
# ============================================================================

# Initial project setup
setup:
    @echo "{{BLUE}}Setting up Resume Genius project...{{NC}}"
    @echo "1. Installing frontend dependencies..."
    @cd apps/frontend && pnpm install
    @echo "2. Installing backend dependencies..."
    @cd apps/backend && uv sync
    @echo "3. Copying environment file..."
    @[ -f .env ] || cp .env.example .env
    @echo "{{YELLOW}}Please edit .env file with your API keys{{NC}}"
    @echo "4. Starting Docker services..."
    @just up
    @echo "5. Running database migrations..."
    @sleep 5  # Wait for database to be ready
    @just migrate
    @echo "{{GREEN}}Setup complete!{{NC}}"

# Clean all generated files and caches
clean:
    @echo "{{YELLOW}}Cleaning project...{{NC}}"
    @echo "Removing Python caches..."
    @find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @find . -type f -name "*.pyc" -delete 2>/dev/null || true
    @echo "Removing frontend build artifacts..."
    @rm -rf apps/frontend/.next apps/frontend/node_modules
    @echo "Removing backend caches..."
    @rm -rf apps/backend/.venv
    @echo "{{GREEN}}Clean complete!{{NC}}"

# Check if all required tools are installed
check:
    @echo "{{BLUE}}Checking required tools...{{NC}}"
    @command -v docker >/dev/null 2>&1 && echo "✓ Docker" || echo "✗ Docker (required)"
    @command -v docker-compose >/dev/null 2>&1 && echo "✓ Docker Compose" || echo "✗ Docker Compose (required)"
    @command -v node >/dev/null 2>&1 && echo "✓ Node.js" || echo "✗ Node.js (required for frontend)"
    @command -v pnpm >/dev/null 2>&1 && echo "✓ pnpm" || echo "✗ pnpm (required for frontend)"
    @command -v python3 >/dev/null 2>&1 && echo "✓ Python" || echo "✗ Python (required for backend)"
    @command -v uv >/dev/null 2>&1 && echo "✓ uv" || echo "✗ uv (required for backend)"
    @command -v just >/dev/null 2>&1 && echo "✓ just" || echo "✗ just"

# Open project in browser
open:
    @echo "{{BLUE}}Opening services in browser...{{NC}}"
    @open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Frontend: http://localhost:3000"
    @open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null || echo "Backend API: http://localhost:8000/docs"

# Show help
help:
    @echo "{{BLUE}}Resume Genius - Available Commands{{NC}}"
    @echo ""
    @echo "{{GREEN}}Quick Start:{{NC}}"
    @echo "  just setup          - Initial project setup"
    @echo "  just up             - Start development services"
    @echo "  just down           - Stop all services"
    @echo ""
    @echo "{{GREEN}}Docker:{{NC}}"
    @echo "  just up-prod        - Start production services"
    @echo "  just logs [service] - View service logs"
    @echo "  just restart        - Restart services"
    @echo "  just build          - Rebuild Docker images"
    @echo "  just ps             - Show service status"
    @echo ""
    @echo "{{GREEN}}Development:{{NC}}"
    @echo "  just backend-dev    - Run backend locally"
    @echo "  just frontend-dev   - Run frontend locally"
    @echo "  just migrate        - Run database migrations"
    @echo ""
    @echo "{{GREEN}}Database:{{NC}}"
    @echo "  just db-shell       - Connect to database"
    @echo "  just db-backup      - Backup database"
    @echo "  just db-restore     - Restore database"
    @echo ""
    @echo "Run 'just --list' to see all available commands"

# ============================================================================
# Development Workflows
# ============================================================================

# Full development reset and restart
reset-dev:
    @just down
    @just clean
    @just setup

# Run both frontend and backend tests
test:
    @echo "{{BLUE}}Running all tests...{{NC}}"
    @just backend-test
    @just frontend-typecheck

# Format and lint all code
format:
    @echo "{{BLUE}}Formatting all code...{{NC}}"
    @just backend-format
    @just backend-lint
    @just frontend-lint