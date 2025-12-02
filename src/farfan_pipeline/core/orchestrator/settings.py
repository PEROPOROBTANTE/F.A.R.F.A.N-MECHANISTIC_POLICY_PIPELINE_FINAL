"""
Centralized settings module for SAAAAAA orchestrator.
This module loads configuration from environment variables and .env file.
Only the orchestrator should read from this module - core modules should not import this.
"""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the repository root
REPO_ROOT: Final[Path] = Path(__file__).parent.parent
ENV_FILE: Final[Path] = REPO_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

def _get_int(key: str, default: int) -> int:
    """Safely get an integer from environment variables."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def _get_bool(key: str, default: str) -> bool:
    """Safely get a boolean from environment variables."""
    return os.getenv(key, default).lower() == "true"

class Settings:
    """Application settings loaded from environment variables."""

    # Application Settings
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = _get_bool("DEBUG", "false")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = _get_int("API_PORT", 5000)
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "dev-secret-key")

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = _get_int("DB_PORT", 5432)
    DB_NAME: str = os.getenv("DB_NAME", "farfan_core")
    DB_USER: str = os.getenv("DB_USER", "farfan_core_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = _get_int("REDIS_PORT", 6379)
    REDIS_DB: int = _get_int("REDIS_DB", 0)

    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = _get_int("JWT_EXPIRATION_HOURS", 24)

    # External Services
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Processing Configuration
    MAX_WORKERS: int = _get_int("MAX_WORKERS", 4)
    BATCH_SIZE: int = _get_int("BATCH_SIZE", 100)
    TIMEOUT_SECONDS: int = _get_int("TIMEOUT_SECONDS", 300)

    # Feature Flags
    ENABLE_CACHING: bool = _get_bool("ENABLE_CACHING", "true")
    ENABLE_MONITORING: bool = _get_bool("ENABLE_MONITORING", "false")
    ENABLE_RATE_LIMITING: bool = _get_bool("ENABLE_RATE_LIMITING", "true")

# Global settings instance
settings = Settings()
