"""Configuration module for CLI target cleanup tool."""

from src.config.settings import (
    DEFAULT_STALE_THRESHOLD_DAYS,
    SNYK_API_BASE_URL,
    SNYK_API_VERSION,
    get_api_base_url,
    get_snyk_token,
)

__all__ = [
    "DEFAULT_STALE_THRESHOLD_DAYS",
    "SNYK_API_BASE_URL",
    "SNYK_API_VERSION",
    "get_api_base_url",
    "get_snyk_token",
]
