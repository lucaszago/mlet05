"""Data preprocessing module for the finance LSTM workflow."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, to_utc_timestamp
from sklearn.preprocessing import MinMaxScaler

from finance.config import ProjectConfig


class DataProcessor:
    """Prepare financial time series data for LSTM training."""

    def __init__(self, spark_df: SparkDataFrame, config: ProjectConfig, spark: SparkSession) -> None:
        self.spark_df = spark_df
        self.df = pd.DataFrame()
        self.config = config
        self.spark = spark
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def preprocess(self) -> None:
        """Validate and normalize the target time series used by the LSTM."""
        target = self._resolve_target_column(self.config.target)

        selected_columns = [target]
        if "Date" in self.spark_df.columns:
            selected_columns.insert(0, "Date")

        self.df = self.spark_df.select(*selected_columns).toPandas()
        if target != self.config.target:
            self.df = self.df.rename(columns={target: self.config.target})
        target = self.config.target

        if "Date" in self.df.columns:
            self.df["Date"] = pd.to_datetime(self.df["Date"])
            self.df = self.df.sort_values("Date").reset_index(drop=True)

        self.df[target] = pd.to_numeric(self.df[target], errors="coerce")
        self.df = self.df.dropna(subset=[target]).reset_index(drop=True)
        self.df["scaled_target"] = self.scaler.fit_transform(self.df[[target]])

    def create_sequences(self) -> tuple[np.ndarray, np.ndarray]:
        """Create rolling windows in the same shape expected by the LSTM model."""
        seq_length = self.config.parameters.sequence_length
        data = self.df["scaled_target"].to_numpy()

        if len(data) <= seq_length:
            raise ValueError(
                f"Not enough rows to create sequences with length {seq_length}. "
                f"Received {len(data)} rows."
            )

        features, labels = [], []
        for index in range(seq_length, len(data)):
            features.append(data[index - seq_length : index])
            labels.append(data[index])

        X = np.array(features).reshape(-1, seq_length, 1)
        y = np.array(labels)
        return X, y

    def split_data(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split sequence data chronologically using the configured train ratio."""
        X, y = self.create_sequences()
        split_index = int(len(X) * self.config.parameters.train_ratio)

        if split_index <= 0 or split_index >= len(X):
            raise ValueError(
                "Configured TRAIN_RATIO produces an empty train or test split. "
                f"Received ratio {self.config.parameters.train_ratio} for {len(X)} sequences."
            )

        X_train = X[:split_index]
        X_test = X[split_index:]
        y_train = y[:split_index]
        y_test = y[split_index:]
        return X_train, X_test, y_train, y_test

    def save_to_catalog(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray) -> None:
        """Persist train and test sequences as Delta tables."""
        self._ensure_schema_exists()

        train_set = self._sequence_frame(X_train, y_train, dataset="train")
        test_set = self._sequence_frame(X_test, y_test, dataset="test")

        train_set_with_timestamp = self.spark.createDataFrame(train_set).withColumn(
            "update_timestamp_utc", to_utc_timestamp(current_timestamp(), "UTC")
        )
        test_set_with_timestamp = self.spark.createDataFrame(test_set).withColumn(
            "update_timestamp_utc", to_utc_timestamp(current_timestamp(), "UTC")
        )

        train_set_with_timestamp.write.mode("overwrite").saveAsTable(
            f"{self.config.catalog_name}.{self.config.schema_name}.train_set"
        )
        test_set_with_timestamp.write.mode("overwrite").saveAsTable(
            f"{self.config.catalog_name}.{self.config.schema_name}.test_set"
        )

    def enable_change_data_feed(self) -> None:
        """Enable Change Data Feed for train and test set tables."""
        self.spark.sql(
            f"ALTER TABLE {self.config.catalog_name}.{self.config.schema_name}.train_set "
            "SET TBLPROPERTIES (delta.enableChangeDataFeed = true);"
        )
        self.spark.sql(
            f"ALTER TABLE {self.config.catalog_name}.{self.config.schema_name}.test_set "
            "SET TBLPROPERTIES (delta.enableChangeDataFeed = true);"
        )

    def _sequence_frame(self, X: np.ndarray, y: np.ndarray, dataset: str) -> pd.DataFrame:
        """Convert sequence arrays into a table-friendly representation."""
        target_unscaled = self.scaler.inverse_transform(y.reshape(-1, 1)).flatten()
        return pd.DataFrame(
            {
                "dataset": dataset,
                "sequence": [json.dumps(sequence[:, 0].tolist()) for sequence in X],
                "target": y.tolist(),
                "target_unscaled": target_unscaled.tolist(),
            }
        )

    def _resolve_target_column(self, target: str) -> str:
        """Map the configured target to the actual Spark column name."""
        if target in self.spark_df.columns:
            return target

        normalized_target = target.lower()
        prefixed_matches = [
            column for column in self.spark_df.columns if column.lower().startswith(f"{normalized_target}_")
        ]
        if len(prefixed_matches) == 1:
            return prefixed_matches[0]

        raise ValueError(
            f"Missing required target column: {target}. "
            f"Available columns: {', '.join(self.spark_df.columns)}"
        )

    def _ensure_schema_exists(self) -> None:
        """Create the configured schema if it does not exist yet."""
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.config.catalog_name}.{self.config.schema_name}")
