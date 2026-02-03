![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-community.jpg)

# CLI Target Cleanup

## Description

This tool automatically identifies and removes stale CLI-monitored targets from Snyk organizations within a Snyk Group. It helps maintain clean Snyk dashboards by removing targets that haven't been imported (via `snyk monitor`) within a configurable time threshold.

## Table of Contents

- [Description](#description)
- [Installation and Setup](#installation-and-setup)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Configuration](#configuration)
  - [Parameter Descriptions](#parameter-descriptions)
- [Output Sample](#output-sample)
- [Error Handling/Logging](#error-handlinglogging)
- [Contributing](#contributing)

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- A Snyk API token with appropriate permissions
- Access to the Snyk Group you want to clean up

### Environment Setup

1. Set your Snyk API token as an environment variable:

```bash
export SNYK_TOKEN="your-snyk-api-token"
```

You can find your API token in the Snyk UI under Account Settings > API Token.

2. (Optional) If using a different Snyk API base URL (e.g., for EU or AU regions):

```bash
export SNYK_API_BASE_URL="https://api.eu.snyk.io"  # For EU
export SNYK_API_BASE_URL="https://api.au.snyk.io"  # For AU
```

### Installation

1. Clone the repository:

```bash
git clone https://github.com/snyk-ps/cli-target-cleanup.git
cd cli-target-cleanup
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The tool runs in **dry-run mode by default**, which means it will only report what would be deleted without actually deleting anything.

### Basic Usage (Dry Run)

```bash
# Dry run with default 90-day threshold
python -m src.main <group-id>
```

### Custom Threshold

```bash
# Dry run with custom threshold (e.g., 60 days)
python -m src.main <group-id> --threshold-days 60
```

### Actually Delete Stale Targets

```bash
# Perform actual deletion (use with caution!)
python -m src.main <group-id> --no-dry-run
```

### Verbose Output

```bash
# Enable verbose logging
python -m src.main <group-id> --verbose
```

### Full Help

```bash
python -m src.main --help
```

## Features

- **Group-wide Processing**: Automatically iterates through all organizations in a Snyk Group
- **CLI Target Identification**: Specifically identifies targets created via `snyk monitor` CLI command
- **Import Date Tracking**: Checks the last import date (when `snyk monitor` was last run) to determine staleness
- **Configurable Threshold**: Set custom staleness threshold (default: 90 days)
- **Dry Run Mode**: Safe by default - preview deletions before executing
- **Comprehensive Logging**: Detailed logging of all operations
- **Error Handling**: Graceful handling of API errors with retry logic
- **Rate Limiting**: Automatic handling of Snyk API rate limits

## Configuration

### Parameter Descriptions

| Parameter | Short | Default | Description |
|-----------|-------|---------|-------------|
| `GROUP_ID` | - | Required | The Snyk Group ID to process |
| `--threshold-days` | `-t` | `90` | Number of days after which a target is considered stale |
| `--dry-run` / `--no-dry-run` | - | `--dry-run` | If enabled, only report stale targets without deleting |
| `--verbose` | `-v` | `False` | Enable verbose logging output |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SNYK_TOKEN` | - | Required. Your Snyk API token |
| `SNYK_API_BASE_URL` | `https://api.snyk.io` | Snyk API base URL (change for EU/AU regions) |

## Output Sample

### Dry Run Output

```
2025-01-15 10:30:00 - INFO - Starting CLI target cleanup for group: abc123-def456
2025-01-15 10:30:00 - INFO - Stale threshold: 90 days
2025-01-15 10:30:00 - INFO - Dry run mode: enabled
2025-01-15 10:30:00 - INFO - Fetching organizations for group: abc123-def456
2025-01-15 10:30:01 - INFO - Processing organization: My Org (org-id-123)
2025-01-15 10:30:02 - INFO -   STALE: my-project (120 days since last import)
2025-01-15 10:30:03 - INFO -   STALE: another-project (never imported)

============================================================
SUMMARY
============================================================
2025-01-15 10:30:05 - INFO - Organizations processed: 1
2025-01-15 10:30:05 - INFO - CLI targets found: 5
2025-01-15 10:30:05 - INFO - Stale targets identified: 2
2025-01-15 10:30:05 - INFO - Targets that WOULD be deleted: 2

This was a DRY RUN. No targets were deleted.
To perform actual deletion, run with --no-dry-run

Stale targets:
  [WOULD DELETE] My Org / my-project (120 days since last import)
  [WOULD DELETE] My Org / another-project (never imported)
```

## Error Handling/Logging

The tool provides comprehensive logging with the following levels:

- **INFO**: Standard operation messages (default)
- **DEBUG**: Detailed operation messages (enabled with `--verbose`)
- **WARNING**: Rate limiting and recoverable errors
- **ERROR**: API failures and critical errors

All logs are output to stdout with timestamps for easy parsing and redirection.

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `SNYK_TOKEN environment variable not set` | Missing API token | Set `SNYK_TOKEN` environment variable |
| `API request failed: 401` | Invalid or expired token | Verify your Snyk API token |
| `API request failed: 403` | Insufficient permissions | Ensure token has access to the Group |
| `Rate limited` | Too many API requests | Tool will automatically retry after waiting |

## Contributing

Contributions are welcome! Please submit a pull request or create an issue to report bugs or suggest enhancements. For detailed instructions on contribution please review the "CONTRIBUTING" file.
