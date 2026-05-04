"""Deterministic ReAct-style finance agent with auditable tool traces."""

from __future__ import annotations

from dataclasses import dataclass

from finance.agent.rag_pipeline import FinanceRAGPipeline
from finance.agent.tools import FinanceTool, build_finance_tools
from finance.config import ProjectConfig
from finance.security.guardrails import validate_agent_input, validate_agent_output


@dataclass(frozen=True)
class FinanceAgentResponse:
    """Agent answer with source context and tool trace."""

    answer: str
    tools_used: list[str]
    trace: list[str]
    sources: list[str]


class FinanceAgent:
    """Finance-domain agent that follows a small ReAct loop over registered tools."""

    def __init__(self, tools: list[FinanceTool], rag_pipeline: FinanceRAGPipeline) -> None:
        self.tools = {tool.name: tool for tool in tools}
        self.rag_pipeline = rag_pipeline

    def answer(self, question: str) -> FinanceAgentResponse:
        """Answer a finance project question using selected tools."""
        validate_agent_input(question)
        selected_tools = self._select_tools(question)
        trace: list[str] = []
        observations: list[str] = []

        for tool_name in selected_tools:
            tool = self.tools[tool_name]
            trace.append(f"Thought: preciso usar {tool.name} para responder no contexto financeiro.")
            trace.append(f"Action: {tool.name}")
            observation = tool.run(question)
            trace.append(f"Observation: {observation}")
            observations.append(observation)

        documents = self.rag_pipeline.retrieve(question, top_k=3)
        sources = sorted({document.source for document in documents})
        answer = self._compose_answer(question, observations)
        validate_agent_output(answer)
        return FinanceAgentResponse(answer=answer, tools_used=selected_tools, trace=trace, sources=sources)

    def _select_tools(self, question: str) -> list[str]:
        normalized = question.lower()
        tools = ["retrieve_finance_context"]
        if any(term in normalized for term in ["modelo", "lstm", "config", "ativo", "janela", "target"]):
            tools.append("describe_model_config")
        if any(term in normalized for term in ["risco", "volatil", "drawdown", "preço", "precos", "retorno"]):
            tools.append("estimate_market_risk")
        if any(term in normalized for term in ["drift", "psi", "monitoramento", "retrein"]):
            tools.append("explain_drift_policy")
        return list(dict.fromkeys(tools))

    @staticmethod
    def _compose_answer(question: str, observations: list[str]) -> str:
        context = " ".join(observations)
        return (
            f"Pergunta: {question}\n"
            f"Resposta fundamentada no contexto do projeto finance: {context}\n"
            "Limite: esta resposta não é recomendação de investimento."
        )


def create_finance_agent(config: ProjectConfig) -> FinanceAgent:
    """Create the default finance agent with RAG and at least three tools."""
    rag_pipeline = FinanceRAGPipeline()
    tools = build_finance_tools(config=config, rag_pipeline=rag_pipeline)
    return FinanceAgent(tools=tools, rag_pipeline=rag_pipeline)
