# Evidencia: API E Agente Financeiro

## Como Subir A API

Configurar o modelo registrado:

```bash
cp .env.example .env
MODEL_URI=models:/mlops_dev.finance.finance_lstm_model_basic@latest-model uv run uvicorn finance.serving.app:app --host 0.0.0.0 --port 8000
```

## Endpoints Para Demonstracao

### Healthcheck

```bash
curl http://localhost:8000/health
```

Resultado esperado: status indicando que a API esta disponivel.

### Predicao

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sequences": [[1.0, 2.0, 3.0]]}'
```

Resultado esperado: resposta JSON com predicoes ou erro controlado caso o modelo remoto nao esteja acessivel no ambiente local.

### Agente Financeiro

```bash
curl -X POST http://localhost:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quando o drift PSI e critico?"}'
```

Resultado esperado: resposta do agente usando contexto financeiro, governanca e politica de drift.

## Capacidades Do Agente

O agente esta em `finance.agent` e implementa um fluxo ReAct-style com RAG local e tools auditaveis:

1. `retrieve_finance_context`: recupera contexto de modelo, pipeline, LGPD e drift.
2. `describe_model_config`: resume ativo, target, janela temporal e periodo de treino.
3. `estimate_market_risk`: calcula volatilidade e drawdown aproximados.
4. `explain_drift_policy`: explica thresholds PSI e resposta operacional.

## Evidencia Visual Recomendada

Salvar prints ou outputs em:

```text
docs/evidence/images/api-health.png
docs/evidence/images/api-predict.png
docs/evidence/images/api-agent-ask.png
```
