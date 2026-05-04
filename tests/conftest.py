"""Shared pytest fixtures."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def reference_frame() -> pd.DataFrame:
    """Stable reference feature distribution."""
    return pd.DataFrame({"Close": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]})


@pytest.fixture
def shifted_frame() -> pd.DataFrame:
    """Clearly shifted current feature distribution."""
    return pd.DataFrame({"Close": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39]})
