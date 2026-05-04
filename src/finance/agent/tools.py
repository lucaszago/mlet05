"""Tools exposed to the finance ReAct-style agent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from finance.agent.rag_pipeline import FinanceRAGPipeline
from finance.config import ProjectConfig
from finance.monitoring.drift import detect_drift


@dataclass(frozen=True)
class FinanceTool:
    """Callable tool metadata."""

    name: str
    description: str
    run: Callable[[str], str]


def build_finance_tools(config: ProjectConfig, rag_pipeline: FinanceRAGPipeline) -> list[FinanceTool]:
    """Build the minimum three finance-domain tools required by the Datathon README."""

    def retrieve_context(query: str) -> str:
        return rag_pipeline.format_context(query=query, top_k=3)

    def describe_model(_: str) -> str:
        params = config.parameters
        return (
            f"Modelo: LSTM de regressão para {params.symbol}. "
            f"Janela={params.sequence_length}, treino={params.train_ratio:.0%}, "
            f"período={params.start_date} até {params.end_date}, target={config.target}."
        )

    def estimate_risk(query: str) -> str:
        values = _extract_numbers(query)
        if len(values) < 2:
            return "Risco não calculado: informe ao menos dois preços ou retornos numéricos."
        returns = np.diff(values) / values[:-1]
        volatility = float(np.std(returns))
        max_drawdown = _max_drawdown(values)
        return f"Volatilidade aproximada={volatility:.4f}; max drawdown aproximado={max_drawdown:.4f}."

    def drift_policy(_: str) -> str:
        return (
            "Política de drift: PSI >= 0.1 gera warning; PSI >= 0.2 é crítico e deve disparar análise "
            "de dados, retreinamento candidato e aprovação antes de promover nova versão."
        )

    return [
        FinanceTool(
            name="retrieve_finance_context",
            description="Busca contexto do RAG financeiro sobre modelo, MLOps, LGPD e drift.",
            run=retrieve_context,
        ),
        FinanceTool(
            name="describe_model_config",
            description="Resume configuração de ativo, janela, target e período de treino.",
            run=describe_model,
        ),
        FinanceTool(
            name="estimate_market_risk",
            description="Calcula volatilidade e drawdown aproximados a partir de números informados.",
            run=estimate_risk,
        ),
        FinanceTool(
            name="explain_drift_policy",
            description="Explica thresholds e resposta operacional para drift.",
            run=drift_policy,
        ),
    ]


def _extract_numbers(text: str) -> np.ndarray:
    """Extract positive numeric values from free text."""
    normalized = text.replace(",", ".")
    values = []
    for token in normalized.split():
        cleaned = token.strip("[](){};:")
        try:
            values.append(float(cleaned))
        except ValueError:
            continue
    return np.asarray(values, dtype=float)


def _max_drawdown(values: np.ndarray) -> float:
    """Compute max drawdown over a numeric sequence."""
    cumulative_max = np.maximum.accumulate(values)
    drawdowns = (values - cumulative_max) / cumulative_max
    return float(abs(drawdowns.min()))


def run_drift_tool(reference_values: list[float], current_values: list[float]) -> str:
    """Convenience tool for external drift checks."""
    import pandas as pd

    result = detect_drift(
        pd.DataFrame({"Close": reference_values}),
        pd.DataFrame({"Close": current_values}),
        features=["Close"],
    )[0]
    return f"Feature={result.feature}; PSI={result.psi:.4f}; status={result.status}."
