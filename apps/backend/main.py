"""Backend application entrypoint."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from src.config.environment import load_environment
from src.config.settings import get_settings
from src.containers import container


def _configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


load_environment()
settings = get_settings()
logger = _configure_logging()

is_docker = settings.is_docker

container_config = settings.build_container_config(is_docker=is_docker)
container.config.from_dict(container_config.model_dump())

container.wire(
    modules=[
        "src.core.unit_of_work",
        "src.api.dependencies",
        "src.api.routers.auth",
        "src.api.routers.jobs",
        "src.api.routers.resumes",
        "src.api.routers.profile",
    ]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

app = FastAPI(
    title="Resume Genius API",
    version="1.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Log detailed validation errors and return the standard payload."""
    try:
        body = await request.body()
        request_data: Any
        request_data = json.loads(body.decode()) if body else {}
    except Exception:  # noqa: BLE001
        request_data = "Could not decode body"

    logger.error(
        """
=== Validation Error Details ===
Endpoint: %s %s
Request Body: %s
Validation Errors: %s
================================
        """,
        request.method,
        request.url.path,
        json.dumps(request_data, indent=2) if isinstance(request_data, dict) else request_data,
        json.dumps(exc.errors(), indent=2),
    )

    return JSONResponse(status_code=422, content={"detail": exc.errors()})


from src.api.routers import auth, jobs, profile, resumes  # noqa: E402

app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/v1", tags=["resumes"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Resume Genius API is running"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


async def run_fastapi() -> None:
    """Run the FastAPI server."""
    os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

    config = uvicorn.Config("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    asyncio.run(run_fastapi())


if __name__ == "__main__":
    main()
