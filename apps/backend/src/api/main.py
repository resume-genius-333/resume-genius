import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.containers import container

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from src.core.db_config import (
    is_docker_environment,
    get_async_database_url,
    get_sync_database_url,
    get_redis_url
)

# Load environment variables
load_dotenv()

# Detect if running in Docker
is_docker = is_docker_environment()

# Configure container from environment
# LiteLLM configuration
container.config.litellm.api_key.from_env("LITELLM_API_KEY", required=True)
litellm_url_key = "LITELLM_BASE_URL_DOCKER" if is_docker else "LITELLM_BASE_URL_LOCAL"
container.config.litellm.base_url.from_env(litellm_url_key, required=True)

# Database configuration - using centralized URL construction
container.config.database.url.from_value(get_async_database_url(is_docker))
container.config.database.sync_url.from_value(get_sync_database_url(is_docker))
container.config.database.echo.from_value(
    os.getenv("BACKEND_DATABASE_ECHO", "false").lower() == "true"
)

# Authentication configuration
container.config.auth.jwt_secret_key.from_env("BACKEND_JWT_SECRET_KEY", required=True)
container.config.auth.jwt_algorithm.from_env("BACKEND_JWT_ALGORITHM", default="HS256")
container.config.auth.access_token_expire_minutes.from_env(
    "BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES", default="30"
)
container.config.auth.refresh_token_expire_days.from_env(
    "BACKEND_REFRESH_TOKEN_EXPIRE_DAYS", default="7"
)
container.config.auth.password_reset_token_expire_hours.from_env(
    "BACKEND_PASSWORD_RESET_TOKEN_EXPIRE_HOURS", default="24"
)
container.config.auth.email_verification_token_expire_hours.from_env(
    "BACKEND_EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", default="48"
)

# Redis configuration - using centralized URL construction
container.config.redis.url.from_value(get_redis_url(is_docker))
container.config.redis.max_connections.from_value(
    int(os.getenv("BACKEND_REDIS_MAX_CONNECTIONS", "50"))
)
container.config.redis.encoding.from_env("BACKEND_REDIS_ENCODING", default="utf-8")
container.config.redis.decode_responses.from_value(
    os.getenv("BACKEND_REDIS_DECODE_RESPONSES", "true").lower() == "true"
)
container.config.redis.socket_connect_timeout.from_value(
    int(os.getenv("BACKEND_REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
)
container.config.redis.socket_timeout.from_value(
    int(os.getenv("BACKEND_REDIS_SOCKET_TIMEOUT", "5"))
)
container.config.redis.retry_on_timeout.from_value(
    os.getenv("BACKEND_REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
)
container.config.redis.health_check_interval.from_value(
    int(os.getenv("BACKEND_REDIS_HEALTH_CHECK_INTERVAL", "30"))
)

# Wire dependencies - MUST be done before importing routers
container.wire(modules=[
    "src.api.dependencies",
    "src.api.routers.auth", 
    "src.api.routers.jobs",
    "src.api.routers.resume"
])

# Import routers AFTER wiring
from .routers import resume, auth, jobs  # noqa: E402

app = FastAPI(title="Resume Genius API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(resume.router, prefix="/api/v1", tags=["resume"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])


@app.get("/")
async def root():
    return {"message": "Resume Genius API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}