"""Snyk API client for interacting with Snyk REST API."""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Optional

import requests

from src.common.logging import get_logger
from src.config.settings import get_api_base_url, SNYK_API_VERSION


@dataclass
class SnykOrg:
    """Represents a Snyk organization."""
    id: str
    name: str
    slug: str


@dataclass
class SnykTarget:
    """Represents a Snyk target (CLI monitored project)."""
    id: str
    display_name: str
    origin: str
    created_at: Optional[datetime]
    org_id: str
    org_name: str
    target_type: str


@dataclass
class SnykProject:
    """Represents a Snyk project within a target."""
    id: str
    name: str
    target_id: str
    last_imported_date: Optional[datetime]
    origin: str


class SnykAPIError(Exception):
    """Exception raised for Snyk API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SnykClient:
    """Client for interacting with the Snyk REST API."""
    
    def __init__(self, token: str):
        """
        Initialize the Snyk API client.
        
        Args:
            token: Snyk API token for authentication.
        """
        self.token = token
        self.base_url = get_api_base_url()
        self.api_version = SNYK_API_VERSION
        self.logger = get_logger()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Content-Type": "application/vnd.api+json",
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        retry_count: int = 3
    ) -> dict:
        """
        Make an HTTP request to the Snyk API with retry logic.
        
        Args:
            method: HTTP method (GET, DELETE, etc.)
            endpoint: API endpoint path.
            params: Query parameters.
            retry_count: Number of retries for rate limiting.
            
        Returns:
            JSON response as a dictionary.
            
        Raises:
            SnykAPIError: If the API request fails.
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add API version to params
        if params is None:
            params = {}
        params["version"] = self.api_version
        
        for attempt in range(retry_count):
            try:
                response = self.session.request(method, url, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self.logger.warning(
                        f"Rate limited. Waiting {retry_after} seconds before retry..."
                    )
                    time.sleep(retry_after)
                    continue
                
                # Handle successful responses
                if response.status_code in (200, 201, 204):
                    if response.status_code == 204 or not response.content:
                        return {}
                    return response.json()
                
                # Handle errors
                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "errors" in error_data:
                        error_msg = f"{error_msg} - {error_data['errors']}"
                except Exception:
                    error_msg = f"{error_msg} - {response.text}"
                
                raise SnykAPIError(error_msg, response.status_code)
                
            except requests.RequestException as e:
                if attempt < retry_count - 1:
                    self.logger.warning(f"Request failed, retrying: {e}")
                    time.sleep(2 ** attempt)
                    continue
                raise SnykAPIError(f"Request failed: {e}")
        
        raise SnykAPIError("Max retries exceeded")
    
    def _paginate(
        self,
        endpoint: str,
        params: Optional[dict] = None
    ) -> Generator[dict, None, None]:
        """
        Paginate through API results.
        
        Args:
            endpoint: API endpoint path.
            params: Query parameters.
            
        Yields:
            Individual items from the paginated response.
        """
        if params is None:
            params = {}
        params["limit"] = 100
        
        while True:
            response = self._make_request("GET", endpoint, params)
            
            data = response.get("data", [])
            for item in data:
                yield item
            
            # Check for next page
            links = response.get("links", {})
            next_link = links.get("next")
            
            if not next_link:
                break
            
            # Extract starting_after from next link
            if "starting_after=" in next_link:
                starting_after = next_link.split("starting_after=")[1].split("&")[0]
                params["starting_after"] = starting_after
            else:
                break
    
    def get_orgs_in_group(self, group_id: str) -> Generator[SnykOrg, None, None]:
        """
        Get all organizations in a Snyk group.
        
        Args:
            group_id: The Snyk group ID.
            
        Yields:
            SnykOrg objects for each organization in the group.
        """
        self.logger.info(f"Fetching organizations for group: {group_id}")
        endpoint = f"/rest/groups/{group_id}/orgs"
        
        for item in self._paginate(endpoint):
            attrs = item.get("attributes", {})
            yield SnykOrg(
                id=item.get("id"),
                name=attrs.get("name", "Unknown"),
                slug=attrs.get("slug", "")
            )
    
    def get_targets_in_org(self, org_id: str) -> Generator[SnykTarget, None, None]:
        """
        Get all targets in a Snyk organization.
        
        Args:
            org_id: The Snyk organization ID.
            
        Yields:
            SnykTarget objects for each target in the organization.
        """
        endpoint = f"/rest/orgs/{org_id}/targets"
        
        for item in self._paginate(endpoint):
            attrs = item.get("attributes", {})
            created_at = None
            if attrs.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(
                        attrs["created_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            
            relationships = item.get("relationships", {})
            if relationships.get("integration"):
                integration_data = relationships.get("integration", {}).get("data", {})
                target_type = integration_data.get("attributes", {}).get("integration_type", "")
            
            yield SnykTarget(
                id=item.get("id"),
                display_name=attrs.get("display_name", "Unknown"),
                origin=attrs.get("origin", ""),
                created_at=created_at,
                org_id=org_id,
                org_name="",  # Will be populated by caller if needed
                target_type=target_type
            )
    
    def get_projects_for_target(
        self,
        org_id: str,
        target_id: str
    ) -> Generator[SnykProject, None, None]:
        """
        Get all projects for a specific target.
        
        Args:
            org_id: The Snyk organization ID.
            target_id: The target ID.
            
        Yields:
            SnykProject objects for each project in the target.
        """
        endpoint = f"/rest/orgs/{org_id}/projects"
        params = {"target_id": target_id}
        
        for item in self._paginate(endpoint, params):
            meta = item.get("meta", {})
            attrs = item.get("attributes", {})
            last_imported = None
            if meta.get("cli_monitored_at"):
                try:
                    last_imported = datetime.fromisoformat(
                        meta.get("cli_monitored_at").replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            
            # Get target reference
            relationships = item.get("relationships", {})
            target_data = relationships.get("target", {}).get("data", {})
            
            yield SnykProject(
                id=item.get("id"),
                name=attrs.get("name", "Unknown"),
                target_id=target_data.get("id", target_id),
                last_imported_date=last_imported,
                origin=attrs.get("origin", "")
            )
    
    def delete_target(self, org_id: str, target_id: str) -> bool:
        """
        Delete a target from a Snyk organization.
        
        Args:
            org_id: The Snyk organization ID.
            target_id: The target ID to delete.
            
        Returns:
            True if deletion was successful.
            
        Raises:
            SnykAPIError: If the deletion fails.
        """
        endpoint = f"/rest/orgs/{org_id}/targets/{target_id}"
        self._make_request("DELETE", endpoint)
        return True
