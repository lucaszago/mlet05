"""Lightweight RAG pipeline for finance-domain documentation."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class FinanceDocument:
    """A retrievable finance-domain context document."""

    doc_id: str
    title: str
    content: str
    source: str


DEFAULT_FINANCE_CORPUS = [
    FinanceDocument(
        doc_id="model_scope",
        title="Escopo do modelo financeiro",
        content=(
            "O modelo LSTM prevê preço de fechamento com base em janelas históricas da série Close. "
            "A saída é uma estimativa estatística e não deve ser interpretada como recomendação de investimento."
        ),
        source="docs/MODEL_CARD.md",
    ),
    FinanceDocument(
        doc_id="mlops_pipeline",
        title="Pipeline MLOps financeiro",
        content=(
            "O pipeline ingere dados via yfinance, cria sequências, persiste train_set e test_set em Delta, "
            "treina o modelo, registra métricas no MLflow e publica o artefato no Unity Catalog."
        ),
        source="docs/SYSTEM_CARD.md",
    ),
    FinanceDocument(
        doc_id="drift",
        title="Monitoramento de drift",
        content=(
            "A detecção de drift usa Population Stability Index. PSI acima de 0.1 indica warning e PSI acima "
            "de 0.2 indica drift crítico e necessidade de investigação ou retreinamento."
        ),
        source="src/finance/monitoring/drift.py",
    ),
    FinanceDocument(
        doc_id="lgpd",
        title="LGPD e dados financeiros",
        content=(
            "O projeto atual usa dados públicos de mercado financeiro e não processa PII. Se dados da empresa "
            "contiverem dados pessoais, deve haver detecção, mascaramento, retenção definida e base legal."
        ),
        source="docs/LGPD_PLAN.md",
    ),
]


class FinanceRAGPipeline:
    """TF-IDF retriever used by the finance agent."""

    def __init__(self, documents: list[FinanceDocument] | None = None) -> None:
        self.documents = documents or DEFAULT_FINANCE_CORPUS
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=None)
        self.document_matrix = self.vectorizer.fit_transform(
            [f"{document.title}. {document.content}" for document in self.documents]
        )

    def retrieve(self, query: str, top_k: int = 3) -> list[FinanceDocument]:
        """Return the most relevant context documents for a query."""
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k < 1:
            raise ValueError("top_k must be greater than zero")

        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.document_matrix).flatten()
        ranked_indexes = scores.argsort()[::-1][:top_k]
        return [self.documents[index] for index in ranked_indexes if scores[index] > 0]

    def format_context(self, query: str, top_k: int = 3) -> str:
        """Format retrieved documents as compact grounded context."""
        documents = self.retrieve(query=query, top_k=top_k)
        if not documents:
            return "Nenhum contexto financeiro relevante encontrado."
        return "\n".join(
            f"[{document.doc_id}] {document.title}: {document.content} Fonte: {document.source}"
            for document in documents
        )
