# Databricks notebook source

from loguru import logger
import yaml
import yfinance as yf
from databricks.connect import DatabricksSession

from finance.config import ProjectConfig
from finance.data_processor import DataProcessor


config = ProjectConfig.from_yaml(config_path="../project_config.yml", env="dev")

logger.info("Configuration loaded:")
logger.info(yaml.dump(config.model_dump(mode="json"), default_flow_style=False))

spark = globals().get("spark")
if spark is None:
    spark = DatabricksSession.builder.getOrCreate()

params = config.parameters
pandas_df = yf.download(params.symbol, start=params.start_date, end=params.end_date, progress=False).reset_index()
if hasattr(pandas_df.columns, "to_flat_index"):
    pandas_df.columns = [
        "_".join(str(part) for part in column if part not in ("", None)).strip("_")
        if isinstance(column, tuple)
        else str(column)
        for column in pandas_df.columns.to_flat_index()
    ]
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

# COMMAND ----------
