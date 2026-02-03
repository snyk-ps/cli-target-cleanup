"""Configuration settings for the CLI target cleanup tool."""

import os
import dotenv
from typing import Optional

# Default threshold in days for considering a target stale
DEFAULT_STALE_THRESHOLD_DAYS = 90

# Snyk API base URL
SNYK_API_BASE_URL = "https://api.snyk.io"

# API version for REST endpoints
SNYK_API_VERSION = "2024-10-15"

dotenv.load_dotenv()

def get_snyk_token() -> Optional[str]:
    """
    Get the Snyk API token from environment variables.
    
    Returns:
        The Snyk API token or None if not set.
    """
    return os.environ.get("SNYK_TOKEN")


def get_api_base_url() -> str:
    """
    Get the Snyk API base URL, allowing override via environment variable.
    
    Returns:
        The Snyk API base URL.
    """
    return os.environ.get("SNYK_API_BASE_URL", SNYK_API_BASE_URL)
