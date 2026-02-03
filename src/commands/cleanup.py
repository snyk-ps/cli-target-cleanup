"""Cleanup command for removing stale CLI targets from Snyk."""

from datetime import datetime, timezone
from typing import List, Optional

import typer

from src.common.logging import get_logger, setup_logging
from src.config.settings import DEFAULT_STALE_THRESHOLD_DAYS, get_snyk_token
from src.snyk.api import SnykClient, SnykAPIError, SnykTarget


def get_last_imported_date_for_target(
    client: SnykClient,
    org_id: str,
    target_id: str
) -> Optional[datetime]:
    """
    Get the most recent import date across all projects in a target.
    
    Args:
        client: The Snyk API client.
        org_id: The organization ID.
        target_id: The target ID.
        
    Returns:
        The most recent import date, or None if no projects or no import dates.
    """
    logger = get_logger()
    most_recent = None
    
    try:
        for project in client.get_projects_for_target(org_id, target_id):
            if project.last_imported_date:
                if most_recent is None or project.last_imported_date > most_recent:
                    most_recent = project.last_imported_date
    except SnykAPIError as e:
        logger.warning(f"Failed to get projects for target {target_id}: {e}")
    
    return most_recent


def is_target_stale(
    last_imported: Optional[datetime],
    threshold_days: int
) -> bool:
    """
    Check if a target is considered stale based on its last import date.
    
    Args:
        last_imported: The last import date of the target.
        threshold_days: Number of days after which a target is considered stale.
        
    Returns:
        True if the target is stale, False otherwise.
    """
    if last_imported is None:
        # If we can't determine last imported, consider it potentially stale
        return True
    
    now = datetime.now(timezone.utc)
    days_since_import = (now - last_imported).days
    return days_since_import > threshold_days


def run_cleanup(
    group_id: str,
    threshold_days: int = DEFAULT_STALE_THRESHOLD_DAYS,
    dry_run: bool = True,
    verbose: bool = False,
) -> None:
    """
    Main cleanup function to remove stale CLI targets.
    
    Args:
        group_id: The Snyk group ID to process.
        threshold_days: Number of days after which a target is considered stale.
        dry_run: If True, only report what would be deleted without actually deleting.
        verbose: If True, enable verbose logging.
    """
    logger = setup_logging(verbose=verbose)
    
    # Get Snyk token
    token = get_snyk_token()
    if not token:
        logger.error(
            "SNYK_TOKEN environment variable not set. "
            "Please set it to your Snyk API token."
        )
        raise typer.Exit(code=1)
    
    logger.info(f"Starting CLI target cleanup for group: {group_id}")
    logger.info(f"Stale threshold: {threshold_days} days")
    logger.info(f"Dry run mode: {'enabled' if dry_run else 'DISABLED - deletions will occur!'}")
    
    if not dry_run:
        logger.warning("=" * 60)
        logger.warning("DRY RUN IS DISABLED - TARGETS WILL BE PERMANENTLY DELETED!")
        logger.warning("=" * 60)
    
    # Initialize client
    client = SnykClient(token)
    
    # Track statistics
    total_orgs = 0
    total_cli_targets = 0
    stale_targets: List[dict] = []
    deleted_targets = 0
    failed_deletions = 0
    
    try:
        # Iterate through all orgs in the group
        for org in client.get_orgs_in_group(group_id):
            total_orgs += 1
            logger.info(f"Processing organization: {org.name} ({org.id})")
            
            try:
                # Get all targets in the org
                for target in client.get_targets_in_org(org.id):
                    # Filter for CLI targets only
                    if target.target_type != "cli":
                        logger.debug(
                            f"Skipping non-CLI target: {target.display_name} "
                            f"(origin: {target.origin})"
                        )
                        continue
                    
                    total_cli_targets += 1
                    target.org_name = org.name
                    
                    # Get the last imported date for this target
                    last_imported = get_last_imported_date_for_target(
                        client, org.id, target.id
                    )
                    
                    # Check if target is stale
                    if is_target_stale(last_imported, threshold_days):
                        days_stale = "never imported"
                        if last_imported:
                            days_since = (datetime.now(timezone.utc) - last_imported).days
                            days_stale = f"{days_since} days since last import"
                        
                        stale_info = {
                            "target": target,
                            "last_imported": last_imported,
                            "days_stale": days_stale
                        }
                        stale_targets.append(stale_info)
                        
                        logger.info(
                            f"  STALE: {target.display_name} ({days_stale})"
                        )
                        
                        # Delete if not dry run
                        if not dry_run:
                            try:
                                client.delete_target(org.id, target.id)
                                deleted_targets += 1
                                logger.info(
                                    f"    DELETED: {target.display_name}"
                                )
                            except SnykAPIError as e:
                                failed_deletions += 1
                                logger.error(
                                    f"    FAILED to delete {target.display_name}: {e}"
                                )
                    else:
                        logger.debug(
                            f"  OK: {target.display_name} "
                            f"(last imported: {last_imported})"
                        )
                        
            except SnykAPIError as e:
                logger.error(f"Failed to process org {org.name}: {e}")
                continue
                
    except SnykAPIError as e:
        logger.error(f"Failed to get organizations for group {group_id}: {e}")
        raise typer.Exit(code=1)
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Organizations processed: {total_orgs}")
    logger.info(f"CLI targets found: {total_cli_targets}")
    logger.info(f"Stale targets identified: {len(stale_targets)}")
    
    if dry_run:
        logger.info(f"Targets that WOULD be deleted: {len(stale_targets)}")
        logger.info("")
        logger.info("This was a DRY RUN. No targets were deleted.")
        logger.info("To perform actual deletion, run with --no-dry-run")
    else:
        logger.info(f"Targets successfully deleted: {deleted_targets}")
        if failed_deletions > 0:
            logger.warning(f"Targets failed to delete: {failed_deletions}")
    
    # List stale targets
    if stale_targets:
        logger.info("")
        logger.info("Stale targets:")
        for info in stale_targets:
            target = info["target"]
            status = "DELETED" if not dry_run else "WOULD DELETE"
            logger.info(
                f"  [{status}] {target.org_name} / {target.display_name} "
                f"({info['days_stale']})"
            )
