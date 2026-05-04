"""FastAPI application for finance LSTM inference."""

from __future__ import annotations

import os

import mlflow
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from finance.agent import create_finance_agent
from finance.config import ProjectConfig


class PredictionRequest(BaseModel):
    """Inference request with one or more LSTM sequences."""

    sequences: list[list[float]] = Field(..., min_length=1)


class PredictionResponse(BaseModel):
    """Inference response with one prediction per input sequence."""

    predictions: list[float]
    model_uri: str


class AgentRequest(BaseModel):
    """Finance agent request."""

    question: str = Field(..., min_length=1, max_length=2000)


class AgentResponse(BaseModel):
    """Finance agent response."""

    answer: str
    tools_used: list[str]
    trace: list[str]
    sources: list[str]


def create_app() -> FastAPI:
    """Create the finance serving API."""
    app = FastAPI(title="MLET TC05 Finance API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/predict", response_model=PredictionResponse)
    def predict(payload: PredictionRequest) -> PredictionResponse:
        model_uri = os.getenv("MODEL_URI")
        if not model_uri:
            raise HTTPException(status_code=503, detail="MODEL_URI environment variable is not configured")

        try:
            model = mlflow.tensorflow.load_model(model_uri)
            input_array = np.array(payload.sequences, dtype=np.float32).reshape(len(payload.sequences), -1, 1)
            predictions = model.predict(input_array, verbose=0).flatten().astype(float).tolist()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

        return PredictionResponse(predictions=predictions, model_uri=model_uri)

    @app.post("/agent/ask", response_model=AgentResponse)
    def ask_agent(payload: AgentRequest) -> AgentResponse:
        config_path = os.getenv("PROJECT_CONFIG_PATH", "project_config.yml")
        env = os.getenv("APP_ENV", "dev")
        try:
            config = ProjectConfig.from_yaml(config_path, env=env)
            response = create_finance_agent(config).answer(payload.question)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Agent failed: {exc}") from exc

        return AgentResponse(
            answer=response.answer,
            tools_used=response.tools_used,
            trace=response.trace,
            sources=response.sources,
        )

    return app


app = create_app()
