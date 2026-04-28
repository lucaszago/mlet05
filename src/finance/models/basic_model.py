"""Basic LSTM model implementation for the finance project."""

from __future__ import annotations

import json
import os
import time
from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Any

import mlflow
import numpy as np
import pandas as pd
from loguru import logger
from mlflow import MlflowClient
from mlflow.models import infer_signature
from pyspark.sql import SparkSession
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras import Input
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential

from finance.config import ProjectConfig, Tags


class LSTMModel:
    """Train and manage the finance LSTM model lifecycle."""

    def __init__(self, config: ProjectConfig, tags: Tags, spark: SparkSession) -> None:
        self.config = config
        self.spark = spark
        self.parameters = self.config.parameters
        self.catalog_name = self.config.catalog_name
        self.schema_name = self.config.schema_name
        self.experiment_name = self.config.experiment_name_basic
        self.model_name = f"{self.catalog_name}.{self.schema_name}.finance_lstm_model_basic"
        self.tags = tags.model_dump()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_uri: str | None = None
        self.metrics: dict[str, float] = {}

    def load_data(self) -> None:
        """Load train/test sequence tables and parse them into LSTM tensors."""
        logger.info("Loading finance train/test tables...")
        self.train_set_spark = self.spark.table(f"{self.catalog_name}.{self.schema_name}.train_set")
        self.test_set_spark = self.spark.table(f"{self.catalog_name}.{self.schema_name}.test_set")

        self.train_set = self.train_set_spark.toPandas()
        self.test_set = self.test_set_spark.toPandas()
        self.data_version = "0"

        self.X_train = self._parse_sequences(self.train_set["sequence"])
        self.X_test = self._parse_sequences(self.test_set["sequence"])
        self.y_train = self.train_set["target"].to_numpy(dtype=np.float32)
        self.y_test = self.test_set["target"].to_numpy(dtype=np.float32)

        if "target_unscaled" in self.train_set.columns and "target_unscaled" in self.test_set.columns:
            self.y_train_unscaled = self.train_set["target_unscaled"].to_numpy(dtype=np.float32)
            self.y_test_unscaled = self.test_set["target_unscaled"].to_numpy(dtype=np.float32)
            combined_targets = np.concatenate([self.y_train_unscaled, self.y_test_unscaled]).reshape(-1, 1)
            self.scaler.fit(combined_targets)
        else:
            self.y_train_unscaled = None
            self.y_test_unscaled = None

        logger.info("Train tensor shape: {}", self.X_train.shape)
        logger.info("Test tensor shape: {}", self.X_test.shape)

    def prepare_features(self) -> None:
        """Build the LSTM architecture from the notebook specification."""
        sequence_length = self.parameters.sequence_length
        self.model = Sequential(
            [
                Input(shape=(sequence_length, 1)),
                LSTM(units=50, return_sequences=True),
                Dropout(0.2),
                LSTM(units=50, return_sequences=False),
                Dropout(0.2),
                Dense(units=1),
            ]
        )
        self.model.compile(optimizer="adam", loss="mean_squared_error")
        logger.info("LSTM model compiled.")

    def train(self) -> None:
        """Train the LSTM model with early stopping."""
        logger.info("Starting LSTM training...")
        early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        self.history = self.model.fit(
            self.X_train,
            self.y_train,
            epochs=self.parameters.epochs,
            batch_size=self.parameters.batch_size,
            validation_split=0.1,
            callbacks=[early_stop],
            verbose=0,
        )
        logger.info("Training completed.")

    def log_model(self) -> None:
        """Log metrics, inputs, and the trained TensorFlow model to MLflow."""
        self._configure_mlflow_uris()
        logger.info("Ensuring MLflow experiment '{}' exists...", self.experiment_name)
        mlflow.set_experiment(self.experiment_name)
        run_tags = self._build_required_tags()
        run_tags.update(self.tags)
        logger.info("Starting MLflow run...")
        with mlflow.start_run(tags=run_tags) as run:
            self.run_id = run.info.run_id
            logger.info("Started MLflow run {}.", self.run_id)

            y_pred_scaled = self.model.predict(self.X_test, verbose=0).flatten()
            metrics = self._calculate_metrics(y_pred_scaled)
            self.metrics = metrics

            mlflow.log_param("model_type", "TensorFlow LSTM")
            mlflow.log_params(self.parameters.model_dump())
            mlflow.log_metrics(metrics)

            signature = infer_signature(model_input=self.X_train, model_output=y_pred_scaled)
            if self._is_spark_connect_dataframe(self.train_set_spark):
                logger.info("Skipping dataset lineage logging for Spark Connect dataframe.")
            else:
                logger.info("Logging training dataset lineage to MLflow...")
                dataset = mlflow.data.from_spark(
                    self.train_set_spark,
                    table_name=f"{self.catalog_name}.{self.schema_name}.train_set",
                    version=self.data_version,
                )
                mlflow.log_input(dataset, context="training")
            logger.info("Logging TensorFlow model artifact to MLflow...")
            model_info = mlflow.tensorflow.log_model(self.model, name="lstm-model", signature=signature)
            self.model_uri = getattr(model_info, "model_uri", None) or (
                f"models:/{model_info.model_id}" if getattr(model_info, "model_id", None) else None
            )
            logger.info("Metrics logged: {}", metrics)

    def register_model(self) -> None:
        """Register the trained model in Unity Catalog and update the latest alias."""
        registry_uri = self._configure_mlflow_uris()
        if not registry_uri.startswith("databricks-uc"):
            raise RuntimeError(
                "MLflow registry URI is not configured for Unity Catalog. "
                "Set DATABRICKS_HOST/DATABRICKS_TOKEN or run inside Databricks before registering the model."
            )
        logger.info("Registering model in Unity Catalog...")
        if self.model_uri is None:
            raise RuntimeError("No MLflow model URI was captured during log_model().")
        model_tags = self._build_required_tags()
        registered_model = mlflow.register_model(
            model_uri=self.model_uri,
            name=self.model_name,
            tags=model_tags,
            await_registration_for=0,
        )
        client = MlflowClient()
        self._wait_for_model_version_ready(client, registered_model.version)
        for key, value in model_tags.items():
            client.set_model_version_tag(name=self.model_name, version=registered_model.version, key=key, value=value)
        logger.info("Setting alias 'latest-model' to version {}...", registered_model.version)
        client.set_registered_model_alias(
            name=self.model_name,
            alias="latest-model",
            version=registered_model.version,
        )
        logger.info("Alias 'latest-model' updated to version {}.", registered_model.version)
        logger.info("Model registered as version {}.", registered_model.version)

    def _configure_mlflow_uris(self) -> str:
        """Point MLflow to Databricks tracking and Unity Catalog when configured."""
        databricks_host = os.getenv("DATABRICKS_HOST")
        databricks_profile = os.getenv("DATABRICKS_CONFIG_PROFILE")

        if databricks_host:
            target_tracking_uri = "databricks"
            target_registry_uri = "databricks-uc"
        elif databricks_profile:
            target_tracking_uri = f"databricks://{databricks_profile}"
            target_registry_uri = f"databricks-uc://{databricks_profile}"
        else:
            target_tracking_uri = mlflow.get_tracking_uri()
            target_registry_uri = mlflow.get_registry_uri()
            logger.warning(
                "Neither DATABRICKS_HOST nor DATABRICKS_CONFIG_PROFILE is set. Keeping MLflow tracking URI '{}' "
                "and registry URI '{}'.",
                target_tracking_uri,
                target_registry_uri,
            )
            return target_registry_uri

        mlflow.set_tracking_uri(target_tracking_uri)
        mlflow.set_registry_uri(target_registry_uri)
        logger.info("Using MLflow tracking URI '{}' and registry URI '{}'.", target_tracking_uri, target_registry_uri)
        return target_registry_uri

    def _wait_for_model_version_ready(self, client: MlflowClient, version: str, timeout_seconds: int = 60) -> None:
        """Poll the registered model version with logs and a bounded timeout."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            model_version = client.get_model_version(name=self.model_name, version=version)
            status = getattr(model_version, "status", "UNKNOWN")
            logger.info("Model version {} status: {}", version, status)
            if status == "READY":
                return
            if status == "FAILED_REGISTRATION":
                raise RuntimeError(f"Model version {version} failed registration in Unity Catalog.")
            time.sleep(5)

        raise TimeoutError(
            f"Timed out after {timeout_seconds}s waiting for model version {version} to become READY."
        )

    @staticmethod
    def _is_spark_connect_dataframe(dataframe: Any) -> bool:
        """Detect Spark Connect dataframes, which do not support MLflow dataset profiling."""
        return type(dataframe).__module__.startswith("pyspark.sql.connect.")

    def _build_required_tags(self) -> dict[str, str]:
        """Build the required governance tags for MLflow runs and model versions."""
        semantic_version = os.getenv("MODEL_VERSION") or self._get_package_version()
        owner = os.getenv("MODEL_OWNER") or os.getenv("USER", "unknown")
        risk_level = os.getenv("MODEL_RISK_LEVEL", "medium")
        fairness_checked = os.getenv("MODEL_FAIRNESS_CHECKED", "false").lower() in {"1", "true", "yes"}
        return {
            "model_name": self.model_name,
            "model_version": semantic_version,
            "model_type": "regression",
            "training_data_version": self.data_version,
            "metrics": json.dumps(self.metrics, sort_keys=True),
            "owner": owner,
            "risk_level": risk_level,
            "fairness_checked": str(fairness_checked).lower(),
            "git_sha": self.tags["git_sha"],
        }

    @staticmethod
    def _get_package_version() -> str:
        """Return the installed package version, with a stable fallback for local runs."""
        try:
            return package_version("mlet-tc05")
        except PackageNotFoundError:
            return "0.1.0"

    def retrieve_current_run_dataset(self) -> Any:
        """Retrieve the MLflow dataset source for the active run."""
        run = mlflow.get_run(self.run_id)
        dataset_info = run.inputs.dataset_inputs[0].dataset
        dataset_source = mlflow.data.get_source(dataset_info)
        return dataset_source.load()

    def retrieve_current_run_metadata(self) -> tuple[dict, dict]:
        """Retrieve MLflow metrics and params for the active run."""
        run = mlflow.get_run(self.run_id)
        payload = run.data.to_dictionary()
        return payload["metrics"], payload["params"]

    def load_latest_model_and_predict(self, input_data: np.ndarray) -> np.ndarray:
        """Load the latest registered model and generate predictions."""
        model_uri = f"models:/{self.model_name}@latest-model"
        model = mlflow.tensorflow.load_model(model_uri)
        return model.predict(input_data, verbose=0).flatten()

    def predict_future(self, last_sequence: np.ndarray, days: int = 5) -> np.ndarray:
        """Predict future values iteratively from the latest known sequence."""
        current_sequence = np.array(last_sequence, dtype=np.float32).copy()
        predictions = []

        for _ in range(days):
            input_seq = current_sequence.reshape(1, len(current_sequence), 1)
            pred_scaled = self.model.predict(input_seq, verbose=0)[0, 0]
            predictions.append(pred_scaled)
            current_sequence = np.append(current_sequence[1:], pred_scaled)

        predictions = np.array(predictions, dtype=np.float32).reshape(-1, 1)
        if hasattr(self.scaler, "scale_"):
            return self.scaler.inverse_transform(predictions).flatten()
        return predictions.flatten()

    def _calculate_metrics(self, y_pred_scaled: np.ndarray) -> dict[str, float]:
        """Compute evaluation metrics, preferring original price scale when available."""
        if self.y_test_unscaled is not None:
            y_true = self.y_test_unscaled
            y_pred = self.scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
        else:
            y_true = self.y_test
            y_pred = y_pred_scaled

        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        non_zero_mask = y_true != 0
        mape = float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
        ss_res = float(np.sum((y_true - y_pred) ** 2))
        ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
        r2 = float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0.0
        return {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2}

    @staticmethod
    def _parse_sequences(series: pd.Series) -> np.ndarray:
        """Parse JSON-encoded sequences from Delta into LSTM input tensors."""
        sequences = [json.loads(value) if isinstance(value, str) else value for value in series.tolist()]
        return np.array(sequences, dtype=np.float32).reshape(-1, len(sequences[0]), 1)


BasicModel = LSTMModel
