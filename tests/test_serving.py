"""Tests for the FastAPI serving application."""

from fastapi.testclient import TestClient

from finance.serving.app import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_requires_model_uri() -> None:
    client = TestClient(create_app())

    response = client.post("/predict", json={"sequences": [[1.0, 2.0, 3.0]]})

    assert response.status_code == 503
    assert "MODEL_URI" in response.json()["detail"]


def test_agent_endpoint_answers_finance_question() -> None:
    client = TestClient(create_app())

    response = client.post("/agent/ask", json={"question": "Quando o drift PSI é crítico?"})

    assert response.status_code == 200
    payload = response.json()
    assert "explain_drift_policy" in payload["tools_used"]
    assert payload["sources"]
