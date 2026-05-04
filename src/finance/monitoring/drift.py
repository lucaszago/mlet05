"""Drift detection helpers based on Population Stability Index (PSI)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DriftResult:
    """Drift status for one feature."""

    feature: str
    psi: float
    status: str


def calculate_psi(reference: np.ndarray, current: np.ndarray, buckets: int = 10) -> float:
    """Calculate Population Stability Index for a numeric feature."""
    if buckets < 2:
        raise ValueError("buckets must be greater than or equal to 2")

    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    reference = reference[~np.isnan(reference)]
    current = current[~np.isnan(current)]

    if reference.size == 0 or current.size == 0:
        raise ValueError("reference and current arrays must contain at least one non-null value")

    quantiles = np.linspace(0, 1, buckets + 1)
    breakpoints = np.unique(np.quantile(reference, quantiles))
    if breakpoints.size < 2:
        return 0.0

    reference_counts, _ = np.histogram(reference, bins=breakpoints)
    current_counts, _ = np.histogram(current, bins=breakpoints)

    epsilon = 1e-6
    reference_pct = np.maximum(reference_counts / max(reference_counts.sum(), 1), epsilon)
    current_pct = np.maximum(current_counts / max(current_counts.sum(), 1), epsilon)
    return float(np.sum((current_pct - reference_pct) * np.log(current_pct / reference_pct)))


def detect_drift(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    features: list[str],
    warning_threshold: float = 0.1,
    critical_threshold: float = 0.2,
) -> list[DriftResult]:
    """Evaluate drift status for configured numeric features."""
    missing = [
        feature
        for feature in features
        if feature not in reference_data.columns or feature not in current_data.columns
    ]
    if missing:
        raise ValueError(f"Missing drift features: {', '.join(missing)}")

    results: list[DriftResult] = []
    for feature in features:
        psi = calculate_psi(reference_data[feature].to_numpy(), current_data[feature].to_numpy())
        if psi >= critical_threshold:
            status = "critical"
        elif psi >= warning_threshold:
            status = "warning"
        else:
            status = "ok"
        results.append(DriftResult(feature=feature, psi=psi, status=status))
    return results
