"""Environment loading utilities for the backend service."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Optional

from dotenv import load_dotenv

_ENV_LOADER_LOCK = Lock()
_ENV_LOADED = False


def is_docker_process() -> bool:
    """Return True when running inside a Docker container."""
    docker_flag = os.getenv("DOCKER_CONTAINER", "false").lower() == "true"
    return docker_flag or Path("/.dockerenv").exists()


def load_environment(env_file: Optional[str] = None) -> None:
    """Load environment variables from a .env file when not running in Docker.

    The loader executes at most once per process. When running outside Docker,
    the caller may supply an explicit `env_file` path or set `BACKEND_ENV_FILE`
    to control which dotenv file is used. When inside Docker, the function
    short-circuits because the environment is already injected by Compose or
    the orchestrator.
    """
    global _ENV_LOADED

    with _ENV_LOADER_LOCK:
        if _ENV_LOADED:
            return

        _ENV_LOADED = True

        if is_docker_process():
            return

        path = env_file or os.getenv("BACKEND_ENV_FILE")
        if path:
            load_dotenv(path)
        else:
            load_dotenv()


__all__ = ["is_docker_process", "load_environment"]
