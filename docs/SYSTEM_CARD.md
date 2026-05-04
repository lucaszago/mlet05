# System Card — MLET TC05

## Objetivo

Pipeline MLOps para ingestão de dados financeiros, treino de LSTM, registro em MLflow/Unity Catalog, validação de deployment e serving via FastAPI.

## Componentes

- `scripts/process_data.py`: ingestão yfinance, normalização, sequenciamento e gravação Delta.
- `scripts/02.train_register_fe_model.py`: treino, tracking MLflow e registro do modelo.
- `scripts/03.deploy_model.py`: validação de carregamento do alias `latest-model`.
- `src/finance/serving/app.py`: API `/health` e `/predict`.
- `src/finance/agent`: agente financeiro ReAct-style com RAG e tools.
- `src/finance/monitoring/drift.py`: detecção de drift por PSI.

## Operação

O workflow Databricks é definido em `databricks.yml` com ambientes `dev`, `test`, `acc` e `prd`. O schedule de produção permanece pausado por segurança até validação da banca/equipe.

## Riscos

- Dependência de dados externos do Yahoo Finance.
- Ausência de dados reais da empresa convidada neste repositório.
- Modelo não inclui variáveis exógenas.
- Monitoramento local implementa PSI; dashboard Prometheus/Grafana ainda deve ser conectado ao ambiente de execução.
- Agente usa RAG local determinístico para rastreabilidade em demo; LLM externo deve ser plugado com as mesmas guardrails antes de produção.
