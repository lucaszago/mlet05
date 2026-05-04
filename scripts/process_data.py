from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml
import yfinance as yf
from databricks.connect import DatabricksSession
from loguru import logger

from finance.config import ProjectConfig
from finance.data_processor import DataProcessor


def parse_args() -> argparse.Namespace:
    """Parse Databricks bundle preprocessing task arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="data_ingestion")
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


def flatten_yfinance_columns(pandas_df):
    """Flatten yfinance MultiIndex columns into stable Spark-compatible names."""
    if hasattr(pandas_df.columns, "to_flat_index"):
        pandas_df.columns = [
            "_".join(str(part) for part in column if part not in ("", None)).strip("_")
            if isinstance(column, tuple)
            else str(column)
            for column in pandas_df.columns.to_flat_index()
        ]
    return pandas_df


def main() -> None:
    """Download market data, create sequences, and persist Delta train/test tables."""
    args = parse_args()
    os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", args.env)
    config = ProjectConfig.from_yaml(config_path=str(resolve_config_path(args.root_path)), env=args.env)

    logger.info("Configuration loaded:")
    logger.info(yaml.dump(config.model_dump(mode="json"), default_flow_style=False))

    spark = globals().get("spark")
    if spark is None:
        spark = DatabricksSession.builder.getOrCreate()

    params = config.parameters
    pandas_df = yf.download(params.symbol, start=params.start_date, end=params.end_date, progress=False).reset_index()
    pandas_df = flatten_yfinance_columns(pandas_df)
    spark_df = spark.createDataFrame(pandas_df)

    data_processor = DataProcessor(spark_df, config, spark)
    data_processor.preprocess()

    logger.info("Data preprocessing completed")

    X_train, X_test, y_train, y_test = data_processor.split_data()
    logger.info("Training set shape: {}", X_train.shape)
    logger.info("Test set shape: {}", X_test.shape)

    logger.info("Saving data to catalog")
    data_processor.save_to_catalog(X_train, X_test, y_train, y_test)

    logger.info("Enable change data feed")
    data_processor.enable_change_data_feed()
    logger.info("Data processing completed for command '{}'.", args.command)


if __name__ == "__main__":
    main()
