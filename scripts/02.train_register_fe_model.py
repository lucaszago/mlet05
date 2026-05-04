from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from databricks.connect import DatabricksSession
from loguru import logger

from finance.config import ProjectConfig, Tags
from finance.models.basic_model import BasicModel


def parse_args() -> argparse.Namespace:
    """Parse Databricks bundle task arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="model_train_register")
    parser.add_argument("--root_path", default="")
    parser.add_argument("--env", default="dev")
    parser.add_argument("--git_sha", default="local")
    parser.add_argument("--job_run_id", default="local")
    parser.add_argument("--branch", default="local")
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


def get_spark():
    """Reuse an existing Spark session or create one via Databricks Connect."""
    spark = globals().get("spark")
    if spark is None:
        spark = DatabricksSession.builder.getOrCreate()
    return spark


def set_task_value(spark, key: str, value: str) -> None:
    """Best-effort task value publishing for Databricks Jobs condition tasks."""
    if globals().get("dbutils") is None:
        logger.info("Skipping Databricks task value publication outside Databricks Jobs runtime.")
        return
    try:
        dbutils = globals().get("dbutils")
        dbutils.jobs.taskValues.set(key=key, value=value)
    except Exception as exc:  # pragma: no cover - best effort for Databricks runtime only
        logger.warning("Unable to set task value {}={}: {}", key, value, exc)


def main() -> None:
    """Train, log, and register the basic finance LSTM model."""
    args = parse_args()
    config = ProjectConfig.from_yaml(str(resolve_config_path(args.root_path)), env=args.env)
    logger.info("Configuration loaded:")
    logger.info(yaml.dump(config.model_dump(mode="json"), default_flow_style=False))

    tags = Tags(git_sha=args.git_sha, branch=args.branch, job_run_id=args.job_run_id)
    logger.info("Creating Spark session...")
    spark = get_spark()

    model = BasicModel(config=config, tags=tags, spark=spark)
    logger.info("Loading training data...")
    model.load_data()
    logger.info("Preparing model features...")
    model.prepare_features()
    logger.info("Training model...")
    model.train()
    logger.info("Logging model to MLflow...")
    model.log_model()
    logger.info("Registering model in Unity Catalog...")
    model.register_model()

    set_task_value(spark, "model_updated", "1")
    logger.info("Model training and registration completed for command '{}'.", args.command)


if __name__ == "__main__":
    main()
