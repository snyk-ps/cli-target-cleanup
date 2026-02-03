"""
CLI Target Cleanup Tool

A command-line tool to identify and remove stale CLI-monitored targets
from Snyk organizations within a Snyk Group.
"""

import typer

from src.commands.cleanup import run_cleanup
from src.config.settings import DEFAULT_STALE_THRESHOLD_DAYS

app = typer.Typer(
    name="cli-target-cleanup",
    help="Remove stale CLI-monitored targets from Snyk organizations.",
    add_completion=False,
)


@app.command()
def cleanup(
    group_id: str = typer.Argument(
        ...,
        help="The Snyk Group ID to process.",
    ),
    threshold_days: int = typer.Option(
        DEFAULT_STALE_THRESHOLD_DAYS,
        "--threshold-days",
        "-t",
        help="Number of days after which a target is considered stale.",
        min=1,
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="If enabled, only report stale targets without deleting them.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging output.",
    ),
) -> None:
    """
    Clean up stale CLI-monitored targets from Snyk organizations.

    This command iterates through all organizations in the specified Snyk Group,
    identifies CLI targets that haven't been tested within the threshold period,
    and optionally deletes them.

    By default, dry-run mode is enabled which only reports what would be deleted
    without performing actual deletions.

    Examples:

        # Dry run with default 90-day threshold
        python -m src.main <group-id>

        # Dry run with custom threshold
        python -m src.main <group-id> --threshold-days 60

        # Actually delete stale targets
        python -m src.main <group-id> --no-dry-run

        # Verbose output
        python -m src.main <group-id> --verbose
    """
    run_cleanup(
        group_id=group_id,
        threshold_days=threshold_days,
        dry_run=dry_run,
        verbose=verbose,
    )


if __name__ == "__main__":
    app()
