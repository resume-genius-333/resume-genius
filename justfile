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

# Docker compose command with proper env file loading
docker_compose := "docker-compose -f " + compose_file + " --env-file .env"

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
    {{docker_compose}} up -d
    @echo "{{GREEN}}Services started!{{NC}}"
    @echo "Frontend: http://localhost:3000"
    @echo "Backend:  http://localhost:8000/docs"
    @echo "LiteLLM:  http://localhost:4000"
    @echo "Redis:    localhost:6380"

# Start all services in production mode
up-prod:
    @echo "{{YELLOW}}Starting services in production mode...{{NC}}"
    cd {{compose_dir}} && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    @echo "{{GREEN}}Production services started!{{NC}}"

# Stop all services
down:
    @echo "{{YELLOW}}Stopping all services...{{NC}}"
    {{docker_compose}} down
    @echo "{{GREEN}}Services stopped!{{NC}}"

# View logs for a specific service (or all if no service specified)
logs service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        {{docker_compose}} logs -f
    else
        {{docker_compose}} logs -f {{service}}
    fi

# Restart a specific service (or all if no service specified)
restart service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        echo "{{YELLOW}}Restarting all services...{{NC}}"
        {{docker_compose}} restart
    else
        echo "{{YELLOW}}Restarting {{service}}...{{NC}}"
        {{docker_compose}} restart {{service}}
    fi
    echo "{{GREEN}}Restart complete!{{NC}}"

# Build or rebuild Docker images
build service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        echo "{{BLUE}}Building all services...{{NC}}"
        {{docker_compose}} build
    else
        echo "{{BLUE}}Building {{service}}...{{NC}}"
        {{docker_compose}} build {{service}}
    fi

# Show status of all services
ps:
    @{{docker_compose}} ps

# Execute command in a running container
exec service command:
    {{docker_compose}} exec {{service}} {{command}}

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

# Run backend integration tests (requires services to be running)
backend-test:
    @echo "{{BLUE}}Running backend integration tests...{{NC}}"
    @echo "{{YELLOW}}Note: Backend must be running (use 'just up' first){{NC}}"
    cd apps/backend && uv run pytest integration_tests/

# Run specific backend test file
backend-test-file file:
    @echo "{{BLUE}}Running test file: {{file}}{{NC}}"
    cd apps/backend && uv run pytest {{file}} -v

# Test job streaming interactively (requires running backend)
test-job-streaming:
    @echo "{{BLUE}}Testing job creation and SSE streaming (interactive mode)...{{NC}}"
    cd apps/backend && uv run python scripts/test_job_streaming.py

# Test job streaming in automated mode (for CI/CD)
test-job-streaming-automated:
    @echo "{{BLUE}}Testing job creation and SSE streaming (automated mode)...{{NC}}"
    cd apps/backend && uv run python scripts/test_job_streaming.py --automated --timeout 30

# Test job flow with requests library (more reliable, handles proxy issues)
test-job-flow:
    @echo "{{BLUE}}Testing complete job flow with requests library...{{NC}}"
    cd apps/backend && uv run python scripts/test_job_flow_requests.py

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

# Connect to Redis CLI
redis-cli:
    @echo "{{BLUE}}Connecting to Redis...{{NC}}"
    docker exec -it resume-genius-redis redis-cli

# Monitor Redis in real-time
redis-monitor:
    @echo "{{BLUE}}Monitoring Redis commands...{{NC}}"
    docker exec -it resume-genius-redis redis-cli monitor

# Check Redis info
redis-info:
    @echo "{{BLUE}}Redis server information:{{NC}}"
    docker exec resume-genius-redis redis-cli INFO server

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
# Database Volume Management
# ============================================================================

# Reset LiteLLM database volume (DANGEROUS - will delete all LiteLLM data!)
db-volume-reset-litellm:
    #!/usr/bin/env bash
    echo -e "{{RED}}WARNING: This will delete all LiteLLM database data!{{NC}}"
    echo -n "Type 'yes' to continue: "
    read confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "{{YELLOW}}Stopping containers...{{NC}}"
        {{docker_compose}} stop litellm litellm-postgres
        echo -e "{{YELLOW}}Removing LiteLLM postgres volume...{{NC}}"
        docker volume rm -f docker_litellm_postgres_data 2>/dev/null || true
        echo -e "{{YELLOW}}Starting LiteLLM postgres...{{NC}}"
        {{docker_compose}} up -d litellm-postgres
        sleep 5
        echo -e "{{YELLOW}}Starting LiteLLM service...{{NC}}"
        {{docker_compose}} up -d litellm
        echo -e "{{GREEN}}LiteLLM database reset complete!{{NC}}"
    else
        echo -e "{{YELLOW}}Cancelled{{NC}}"
    fi

# Reset Backend database volume (DANGEROUS - will delete all backend data!)
db-volume-reset-backend:
    #!/usr/bin/env bash
    echo -e "{{RED}}WARNING: This will delete all Resume Genius backend database data!{{NC}}"
    echo -n "Type 'yes' to continue: "
    read confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "{{YELLOW}}Stopping containers...{{NC}}"
        {{docker_compose}} stop backend frontend resume-genius-postgres
        echo -e "{{YELLOW}}Removing backend postgres volume...{{NC}}"
        docker volume rm -f docker_resume_genius_postgres_data 2>/dev/null || true
        echo -e "{{YELLOW}}Starting backend postgres...{{NC}}"
        {{docker_compose}} up -d resume-genius-postgres
        sleep 5
        echo -e "{{YELLOW}}Starting backend service...{{NC}}"
        {{docker_compose}} up -d backend
        sleep 5
        echo -e "{{YELLOW}}Running migrations...{{NC}}"
        docker exec resume-genius-backend uv run alembic upgrade head || echo "Migrations will run when backend starts"
        echo -e "{{GREEN}}Backend database reset complete!{{NC}}"
    else
        echo -e "{{YELLOW}}Cancelled{{NC}}"
    fi

# Reset all database volumes (DANGEROUS - will delete ALL data!)
db-volume-reset-all:
    #!/usr/bin/env bash
    echo -e "{{RED}}WARNING: This will delete ALL database data (LiteLLM and Backend)!{{NC}}"
    echo -n "Type 'yes' to continue: "
    read confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "{{YELLOW}}Stopping all containers...{{NC}}"
        {{docker_compose}} down
        echo -e "{{YELLOW}}Removing all database volumes...{{NC}}"
        docker volume rm -f docker_litellm_postgres_data docker_resume_genius_postgres_data 2>/dev/null || true
        echo -e "{{YELLOW}}Starting services...{{NC}}"
        {{docker_compose}} up -d
        echo -e "{{YELLOW}}Waiting for services to be ready...{{NC}}"
        sleep 10
        echo -e "{{YELLOW}}Running migrations...{{NC}}"
        docker exec resume-genius-backend uv run alembic upgrade head || echo "Run 'just migrate' manually if needed"
        echo -e "{{GREEN}}All databases reset complete!{{NC}}"
    else
        echo -e "{{YELLOW}}Cancelled{{NC}}"
    fi

# List all volumes
volumes:
    @echo "{{BLUE}}Docker volumes:{{NC}}"
    @docker volume ls | grep -E "(litellm|resume_genius)" || echo "No project volumes found"

# ============================================================================
# Environment Management
# ============================================================================

# Check environment configuration
env-check:
    @echo "{{BLUE}}Checking environment configuration...{{NC}}"
    @echo ""
    @echo "{{YELLOW}}Required Environment Variables:{{NC}}"
    @echo ""
    @echo "{{GREEN}}LiteLLM Configuration:{{NC}}"
    @[ -n "${LITELLM_MASTER_KEY}" ] && echo "✓ LITELLM_MASTER_KEY is set" || echo "✗ LITELLM_MASTER_KEY is missing"
    @[ -n "${LITELLM_API_KEY}" ] && echo "✓ LITELLM_API_KEY is set" || echo "✗ LITELLM_API_KEY is missing"
    @[ -n "${LITELLM_POSTGRES_PASSWORD}" ] && echo "✓ LITELLM_POSTGRES_PASSWORD is set" || echo "✗ LITELLM_POSTGRES_PASSWORD is missing"
    @echo ""
    @echo "{{GREEN}}Backend Configuration:{{NC}}"
    @[ -n "${BACKEND_POSTGRES_PASSWORD}" ] && echo "✓ BACKEND_POSTGRES_PASSWORD is set" || echo "✗ BACKEND_POSTGRES_PASSWORD is missing"
    @[ -n "${BACKEND_JWT_SECRET_KEY}" ] && echo "✓ BACKEND_JWT_SECRET_KEY is set" || echo "✗ BACKEND_JWT_SECRET_KEY is missing"
    @echo ""
    @echo "{{GREEN}}LLM Provider API Keys:{{NC}}"
    @[ -n "${OPENAI_API_KEY}" ] && echo "✓ OPENAI_API_KEY is set" || echo "○ OPENAI_API_KEY not set (optional)"
    @[ -n "${ANTHROPIC_API_KEY}" ] && echo "✓ ANTHROPIC_API_KEY is set" || echo "○ ANTHROPIC_API_KEY not set (optional)"
    @[ -n "${GROQ_API_KEY}" ] && echo "✓ GROQ_API_KEY is set" || echo "○ GROQ_API_KEY not set (optional)"
    @[ -n "${DEEPSEEK_API_KEY}" ] && echo "✓ DEEPSEEK_API_KEY is set" || echo "○ DEEPSEEK_API_KEY not set (optional)"
    @[ -n "${GEMINI_API_KEY}" ] && echo "✓ GEMINI_API_KEY is set" || echo "○ GEMINI_API_KEY not set (optional)"
    @echo ""
    @echo "{{BLUE}}Database URLs:{{NC}}"
    @echo "LiteLLM DB (Docker): postgresql://${LITELLM_POSTGRES_USER}:***@${LITELLM_POSTGRES_HOST_DOCKER}:${LITELLM_POSTGRES_PORT_DOCKER}/${LITELLM_POSTGRES_DB}"
    @echo "Backend DB (Docker): postgresql://${BACKEND_POSTGRES_USER}:***@${BACKEND_POSTGRES_HOST_DOCKER}:${BACKEND_POSTGRES_PORT_DOCKER}/${BACKEND_POSTGRES_DB}"
    @echo "Backend DB (Local):  postgresql://${BACKEND_POSTGRES_USER}:***@${BACKEND_POSTGRES_HOST_LOCAL}:${BACKEND_POSTGRES_PORT_LOCAL}/${BACKEND_POSTGRES_DB}"
    @echo ""
    @echo "{{BLUE}}Service URLs:{{NC}}"
    @echo "LiteLLM (Docker): ${LITELLM_BASE_URL_DOCKER}"
    @echo "LiteLLM (Local):  ${LITELLM_BASE_URL_LOCAL}"
    @echo "Backend Redis (Docker): ${BACKEND_REDIS_URL_DOCKER}"
    @echo "Backend Redis (Local):  ${BACKEND_REDIS_URL_LOCAL}"
    @echo ""
    @[ -f .env ] && echo "{{GREEN}}✓ .env file exists{{NC}}" || echo "{{RED}}✗ .env file not found - copy .env.example to .env{{NC}}"

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
    @echo "  just db-shell       - Connect to PostgreSQL"
    @echo "  just redis-cli      - Connect to Redis CLI"
    @echo "  just redis-monitor  - Monitor Redis commands"
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