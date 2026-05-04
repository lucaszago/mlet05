"""Post-deployment status task used by test bundle runs.

The Databricks job calls this task after deployment validation. In a production
repository this is where a GitHub commit status or deployment check would be
published. For the datathon delivery, the task emits structured logs and exits
non-zero only when required arguments are missing.
"""

from __future__ import annotations

import argparse

from loguru import logger


def parse_args() -> argparse.Namespace:
    """Parse Databricks bundle post-commit task arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="post_commit_check")
    parser.add_argument("--job_run_id", required=True)
    parser.add_argument("--job_id", required=True)
    parser.add_argument("--git_sha", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--org", required=True)
    args, unknown = parser.parse_known_args()
    ignored = [arg for arg in unknown if arg.startswith("--f=")]
    unexpected = [arg for arg in unknown if arg not in ignored]
    if unexpected:
        logger.warning("Ignoring unknown CLI arguments: {}", unexpected)
    return args


def main() -> None:
    """Emit the status payload expected by CI/CD logs."""
    args = parse_args()
    logger.info(
        "Deployment check passed: command={} org={} repo={} git_sha={} job_id={} job_run_id={}",
        args.command,
        args.org,
        args.repo,
        args.git_sha,
        args.job_id,
        args.job_run_id,
    )


if __name__ == "__main__":
    main()
