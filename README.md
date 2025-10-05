# Resume Genius

An intelligent resume management system that helps users create, version, and optimize resumes for different job applications.

## Features

- **Resume Extraction**: Extract structured data from PDF resumes using LLM
- **Version Management**: Track multiple resume versions per job application
- **Smart Optimization**: Tailor resumes for specific job descriptions
- **API-First Design**: RESTful API with FastAPI backend
- **Modern UI**: Next.js frontend with hot-reload development

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, TailwindCSS
- **Backend**: Python 3.13, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL with pgvector extension
- **LLM Proxy**: LiteLLM for unified access to multiple AI providers
- **Infrastructure**: Docker, Docker Compose
- **Task Runner**: Just command runner

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ and npm
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [just](https://github.com/casey/just) (command runner)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/resume-genius.git
cd resume-genius
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your API keys (OpenAI, Anthropic, etc.)
```

### 3. Run initial setup
```bash
just setup
```

This command will:
- Install all dependencies
- Start Docker services
- Run database migrations
- Set up the development environment

### 4. Access the application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- LiteLLM Proxy: http://localhost:4000

## Development

### Using Just Commands

The project uses `just` as a command runner. Run `just` or `just help` to see all available commands.

#### Common Commands

**Starting Services:**
```bash
just up         # Start development mode with hot-reload
just up-prod    # Start production mode
just down       # Stop all services
```

**Development:**
```bash
just logs           # View all logs
just logs backend   # View specific service logs
just restart        # Restart all services
just restart frontend  # Restart specific service
```

**Backend:**
```bash
just backend-dev    # Run backend locally (without Docker)
just migrate        # Run database migrations
just makemigration "description"  # Create new migration
just backend-shell  # Open Python shell with app context
just backend-test   # Run tests
```

**Frontend:**
```bash
just frontend-dev   # Run frontend locally (without Docker)
just frontend-build # Build for production
just frontend-lint  # Run linting
just frontend-typecheck  # Type checking
```

**Database:**
```bash
just db-shell      # Connect to PostgreSQL
just db-backup     # Backup database
just db-restore backup.sql  # Restore from backup
just db-reset      # Reset database (CAUTION: deletes all data)
```

**Utilities:**
```bash
just check         # Check if all tools are installed
just clean         # Clean build artifacts and caches
just open          # Open services in browser
```

### Project Structure

```
resume-genius/
├── apps/
│   ├── frontend/          # Next.js frontend application
│   │   ├── src/
│   │   │   ├── app/       # App router pages
│   │   │   ├── components/# React components
│   │   │   └── lib/       # Utilities and API client
│   │   ├── Dockerfile     # Production build
│   │   └── Dockerfile.dev # Development with hot-reload
│   │
│   └── backend/           # FastAPI backend application
│       ├── src/
│       │   ├── api/       # API routes and endpoints
│       │   ├── models/    # Database models
│       │   ├── schemas/   # Pydantic schemas
│       │   ├── services/  # Business logic
│       │   └── extractors/# Resume extraction logic
│       ├── alembic/       # Database migrations
│       ├── Dockerfile     # Production build
│       └── Dockerfile.dev # Development with hot-reload
│
├── infrastructure/
│   └── docker/            # Docker configuration
│       ├── docker-compose.yml      # Development setup
│       ├── docker-compose.prod.yml # Production overrides
│       └── litellm-config.yaml    # LLM proxy configuration
│
├── justfile              # Command runner configuration
├── .env.example          # Environment variables template
└── README.md            # This file
```

### API Documentation

The backend provides automatic API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database Migrations

Create and apply migrations:
```bash
# Create a new migration
just makemigration "add user table"

# Apply migrations
just migrate
```

### Testing

Run tests for both frontend and backend:
```bash
just test              # Run all tests
just backend-test      # Backend tests only
just frontend-typecheck # Frontend type checking
```

## Docker Services

The application runs several Docker services:

- **frontend**: Next.js application (port 3000)
- **backend**: FastAPI application (port 8000)
- **resume-genius-postgres**: Main application database (port 5441)
- **litellm**: LLM proxy service (port 4000)
- **postgres**: LiteLLM database (port 5440)

### Development vs Production

**Development Mode** (`just up`):
- Hot-reload enabled
- Source code mounted as volumes
- Verbose logging
- Development tools available

**Production Mode** (`just up-prod`):
- Optimized builds
- No source mounting
- Security hardening
- Health checks enabled

## Backend Database Configuration

### Local container (default)
`just up` enables the `backend-local-db` Docker Compose profile whenever `BACKEND_DATABASE_URL` is empty, which spins up the `resume-genius-postgres` container (PostgreSQL 16 with pgvector). Set `BACKEND_DATABASE_URL` to the connection string your local tooling should use, and `BACKEND_DATABASE_URL_DOCKER` to the hostname that the backend container should reach (for the bundled database, use `postgresql://…@resume-genius-postgres:5432/resume_genius`). If you rely on the optional local Postgres container, tweak the `RESUME_GENIUS_POSTGRES_*` values in `.env` to control its bootstrap credentials, then run `just migrate` once the stack is running.

### Remote database (managed)
1. Edit `infrastructure/terraform/environments/dev/terraform.tfvars` and update `backend_rds_master_username`, `backend_rds_database_name`, and (optionally) `backend_rds_secret_name` to match the credentials you want Terraform to create.
2. Run `terraform -chdir=infrastructure/terraform/environments/dev plan` followed by `terraform -chdir=infrastructure/terraform/environments/dev apply` to provision the new RDS instance. Terraform generates a random password, allows ingress from the `backend` security group, and writes a JSON payload into Secrets Manager at the configured name.
3. Capture the outputs `backend_rds_endpoint` and `backend_rds_secret_arn` (see `terraform output`). The secret’s JSON includes `engine`, `host`, `port`, `username`, `password`, `dbname`, and a ready-to-use `url` field.
4. Give any runtime (local dev, ECS task, CI job) IAM permission to call `secretsmanager:GetSecretValue` on that ARN and, if it runs inside AWS, attach the exported `backend_security_group_id` to its network interface so it can reach the database. Either inject the secret JSON directly or set `BACKEND_DATABASE_URL` to the `url` string so the backend skips the local container automatically.
5. After deploying new infrastructure, run `just migrate` (pointing at the remote database) to initialise the schema and verify that the security group rules allow connections from your workload.
6. The Terraform defaults keep the dev instance inexpensive (`db.t4g.micro`, 20 GB storage, 1-day backups, no Multi-AZ). Increase these knobs through the `backend_rds_*` variables when you move beyond development.

### Useful toggles
Set `BACKEND_DATABASE_ECHO=true` to print SQL queries during debugging. Commands like `just db-shell`, `just db-backup`, and `just db-restore` read the same environment variables, so they automatically target whichever database (local or remote) you have configured.

### Remote Redis (managed)
Point the backend at a managed Redis service (for example, AWS ElastiCache or Valkey) by overriding the Docker defaults. Set `BACKEND_REDIS_HOST_DOCKER` and `BACKEND_REDIS_PORT_DOCKER` to the cluster endpoint and port injected into your container environment. Local CLI tools continue to use the `_LOCAL` variants, letting you test against a local cache while production points at the managed instance. Enable Redis snapshots and multi-AZ from your infrastructure layer so the cache maintains persistence and survives node failures.

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `LITELLM_API_KEY`: API key for LiteLLM proxy
- `BACKEND_DATABASE_URL`: Optional override that points the backend at a managed PostgreSQL instance
- `DATABASE_URL`: PostgreSQL connection string for the LiteLLM proxy
- `OPENAI_API_KEY`: OpenAI API key (if using GPT models)
- `ANTHROPIC_API_KEY`: Anthropic API key (if using Claude)

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using the port
lsof -i :3000  # or :8000, :5441, etc.

# Stop the process or change the port in docker-compose.yml
```

**Database connection issues:**
```bash
# Check if database is running
just ps

# View database logs
just logs resume-genius-postgres

# Reset database if needed
just db-reset
```

**Dependencies out of sync:**
```bash
# Frontend
cd apps/frontend && npm ci

# Backend
cd apps/backend && uv sync
```

**Docker issues:**
```bash
# Rebuild images
just build

# Clean and restart
just down
just clean
just up
```

## Cloud Deployment

- **Workflow** `litellm-deploy` builds the LiteLLM container, runs Terraform in `infrastructure/terraform/environments/dev`, and updates AWS Secrets Manager values for both LiteLLM (`DATABASE_URL`) and, when available, the backend (`BACKEND_DATABASE_URL`). Trigger it by pushing to `main` or via the manual `workflow_dispatch` input when you need to roll out a specific image tag.
- **Terraform outputs** must expose `rds_endpoint` (for LiteLLM) and, if you provision a managed backend database, `backend_rds_endpoint`. The workflow skips backend secret updates when those outputs are missing, so you can opt in gradually.
- **GitHub secrets** to configure: AWS access (`AWS_REGION`, `AWS_ROLE_TO_ASSUME`), Terraform state (`TF_STATE_BUCKET`, `TF_STATE_LOCK_TABLE`), LiteLLM deployment (`LITELLM_ECR_REPOSITORY`, `LITELLM_DB_MASTER_PASSWORD`, `LITELLM_SECRETS_JSON`, `LITELLM_REDIS_AUTH_TOKEN_SECRET_ARN`), plus backend database credentials when you manage it via Terraform (`BACKEND_DB_MASTER_PASSWORD`, `BACKEND_SECRETS_JSON`).
- **Secrets JSON format** expects an object mapping environment variable names to secret ARNs, for example `{"DATABASE_URL":"arn:aws:secretsmanager:...","BACKEND_DATABASE_URL":"arn:aws:secretsmanager:..."}`. The workflow reads these maps to know which secret entry to update after Terraform applies.
- **Repository variables** let you tune resource names without editing the workflow: `TERRAFORM_ENVIRONMENT`, `RDS_MASTER_USERNAME`, `RDS_DATABASE_NAME`, `BACKEND_RDS_MASTER_USERNAME`, `BACKEND_RDS_DATABASE_NAME`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.
