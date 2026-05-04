"""Validate that the latest registered finance model can be loaded for serving."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import mlflow
import yaml
from databricks.connect import DatabricksSession
from loguru import logger

from finance.config import ProjectConfig


def parse_args() -> argparse.Namespace:
    """Parse Databricks bundle deployment task arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="deployment")
    parser.add_argument("--root_path", default="")
    parser.add_argument("--env", default="dev")
    parser.add_argument("--is_test", default="0")
    args, unknown = parser.parse_known_args()
    ignored = [arg for arg in unknown if arg.startswith("--f=")]
    unexpected = [arg for arg in unknown if arg not in ignored]
    if unexpected:
        logger.warning("Ignoring unknown CLI arguments: {}", unexpected)
    return args


def resolve_config_path(root_path: str = "") -> Path:
    """Resolve the project configuration file in Databricks or locally."""
    if root_path:
        candidate = Path(root_path) / "files" / "project_config.yml"
        if candidate.exists():
            return candidate
        return Path(root_path) / "project_config.yml"

    if "__file__" in globals():
        return Path(__file__).resolve().parents[1] / "project_config.yml"

    return Path.cwd() / "project_config.yml"


def configure_mlflow_registry(env: str) -> None:
    """Configure MLflow to use Databricks Unity Catalog when available."""
    if os.getenv("DATABRICKS_HOST") or is_databricks_runtime():
        mlflow.set_tracking_uri("databricks")
        mlflow.set_registry_uri("databricks-uc")
    else:
        mlflow.set_tracking_uri(f"databricks://{env}")
        mlflow.set_registry_uri(f"databricks-uc://{env}")


def is_databricks_runtime() -> bool:
    """Detect execution inside a Databricks job/runtime without relying on local profiles."""
    databricks_env_markers = (
        "DATABRICKS_RUNTIME_VERSION",
        "DATABRICKS_JOB_ID",
        "DATABRICKS_CLUSTER_ID",
        "DB_HOME",
    )
    return any(os.getenv(marker) for marker in databricks_env_markers)


def main() -> None:
    """Load the registered model alias to fail fast before production serving."""
    args = parse_args()
    config = ProjectConfig.from_yaml(str(resolve_config_path(args.root_path)), env=args.env)
    logger.info("Configuration loaded:")
    logger.info(yaml.dump(config.model_dump(mode="json"), default_flow_style=False))

    spark = globals().get("spark")
    if spark is None:
        spark = DatabricksSession.builder.getOrCreate()
    logger.info("Spark session ready: {}", spark)

    configure_mlflow_registry(args.env)
    model_name = f"{config.catalog_name}.{config.schema_name}.finance_lstm_model_basic"
    model_uri = f"models:/{model_name}@latest-model"
    logger.info("Validating registered model URI: {}", model_uri)
    mlflow.tensorflow.load_model(model_uri)
    logger.info("Deployment validation completed for command '{}'.", args.command)


if __name__ == "__main__":
    main()
