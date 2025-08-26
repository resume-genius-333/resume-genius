# Claude Development Guide

## Project Overview
Resume Genius - An intelligent resume management system with LLM-powered extraction and optimization.

## Essential Commands

### Quick Start
```bash
just setup    # Initial setup: installs deps, starts services, runs migrations
just up       # Start development mode with hot-reload
just down     # Stop all services
```

### Development Workflow
```bash
just logs           # View all logs
just logs backend   # View specific service logs
just restart        # Restart all services
```

### Backend Commands
```bash
just backend-dev    # Run backend locally (without Docker)
just backend-test   # Run backend tests
just migrate        # Apply database migrations
just makemigration "description"  # Create new migration
```

### Frontend Commands
```bash
just frontend-dev       # Run frontend locally
just frontend-build     # Build for production
just frontend-lint      # Run linting
just frontend-typecheck # Run TypeScript type checking
```

### Code Quality Checks
**IMPORTANT**: Always run these before completing tasks:
```bash
# Backend
cd apps/backend && uv run ruff check .
cd apps/backend && uv run mypy .

# Frontend
cd apps/frontend && npm run lint
cd apps/frontend && npm run typecheck
```

### Database Operations
```bash
just db-shell    # Connect to PostgreSQL
just db-reset    # Reset database (CAUTION: deletes all data)
```

### Testing
```bash
just test           # Run all tests
just backend-test   # Backend tests only
```

## Service URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- LiteLLM Proxy: http://localhost:4000
- PostgreSQL: localhost:5441

## Project Structure
- `apps/frontend/`: Next.js 15 + TypeScript frontend
- `apps/backend/`: FastAPI + SQLAlchemy backend
- `infrastructure/docker/`: Docker configurations
- `justfile`: Task runner commands

## Key Technologies
- Frontend: Next.js 15, TypeScript, TailwindCSS
- Backend: Python 3.13, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL with pgvector
- Package Managers: uv (Python), npm (Node.js)

## Important Notes
- Always use `just` commands when available
- Run linting/type checking before marking tasks complete
- Backend uses `uv` for Python dependency management
- Frontend uses npm for Node.js dependencies
- All services run in Docker for development