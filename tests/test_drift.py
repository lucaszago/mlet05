"""Tests for PSI drift detection."""

from finance.monitoring.drift import calculate_psi, detect_drift


def test_calculate_psi_returns_zero_for_same_distribution(reference_frame) -> None:
    psi = calculate_psi(reference_frame["Close"].to_numpy(), reference_frame["Close"].to_numpy())

    assert psi == 0.0


def test_detect_drift_flags_shifted_distribution(reference_frame, shifted_frame) -> None:
    result = detect_drift(
        reference_frame,
        shifted_frame,
        features=["Close"],
        warning_threshold=0.1,
        critical_threshold=0.2,
    )

    assert result[0].feature == "Close"
    assert result[0].status == "critical"
