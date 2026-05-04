"""Tests for local data processing logic."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from finance.config import LSTMParameters, ProjectConfig
from finance.data_processor import DataProcessor


class FakeSparkDataFrame:
    """Minimal Spark DataFrame double for local preprocessing tests."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.columns = list(frame.columns)

    def select(self, *columns: str) -> FakeSparkDataFrame:
        return FakeSparkDataFrame(self.frame.loc[:, list(columns)])

    def toPandas(self) -> pd.DataFrame:
        return self.frame.copy()


def make_config(sequence_length: int = 3, train_ratio: float = 0.6) -> ProjectConfig:
    return ProjectConfig(
        num_features=["Close"],
        cat_features=[],
        target="Close",
        catalog_name="mlops_dev",
        schema_name="finance",
        pipeline_id="pipeline",
        experiment_name_basic="/Shared/basic",
        experiment_name_custom="/Shared/custom",
        experiment_name_fe="/Shared/fe",
        parameters=LSTMParameters(
            SYMBOL="DIS",
            START_DATE="2024-01-01",
            END_DATE="2024-01-10",
            SEQUENCE_LENGTH=sequence_length,
            TRAIN_RATIO=train_ratio,
            EPOCHS=1,
            BATCH_SIZE=2,
        ),
    )


def test_preprocess_sorts_dates_and_scales_target() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2024-01-03", "2024-01-01", "2024-01-02"],
            "Close": [30.0, 10.0, 20.0],
        }
    )
    processor = DataProcessor(FakeSparkDataFrame(frame), make_config(sequence_length=1), spark=None)

    processor.preprocess()

    assert processor.df["Close"].tolist() == [10.0, 20.0, 30.0]
    assert processor.df["scaled_target"].between(0, 1).all()


def test_create_sequences_uses_rolling_windows() -> None:
    processor = DataProcessor(FakeSparkDataFrame(pd.DataFrame({"Close": [1, 2, 3, 4, 5]})), make_config(), spark=None)
    processor.df = pd.DataFrame({"scaled_target": [0.1, 0.2, 0.3, 0.4, 0.5]})

    X, y = processor.create_sequences()

    assert X.shape == (2, 3, 1)
    np.testing.assert_allclose(X[0].flatten(), [0.1, 0.2, 0.3])
    np.testing.assert_allclose(y, [0.4, 0.5])


def test_split_data_rejects_empty_test_split() -> None:
    processor = DataProcessor(
        FakeSparkDataFrame(pd.DataFrame({"Close": [1, 2, 3, 4]})),
        make_config(sequence_length=2, train_ratio=1.0),
        spark=None,
    )
    processor.df = pd.DataFrame({"scaled_target": [0.1, 0.2, 0.3, 0.4]})

    with pytest.raises(ValueError, match="empty train or test split"):
        processor.split_data()


def test_resolve_target_column_accepts_yfinance_suffix() -> None:
    processor = DataProcessor(
        FakeSparkDataFrame(pd.DataFrame({"Close_DIS": [1.0]})),
        make_config(),
        spark=None,
    )

    assert processor._resolve_target_column("Close") == "Close_DIS"
