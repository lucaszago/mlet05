# Evidencias da Entrega

Este diretorio consolida as evidencias operacionais da entrega MLET_TC05. Nao inclua tokens, arquivos `.env`, chaves ou prints contendo segredos.

## Status Atual

| Item | Status | Evidencia |
| --- | --- | --- |
| Repositorio publico | OK | https://github.com/lucaszago/mlet05 |
| Esteira GitHub Actions | OK | Run `25300452941`, status `success` |
| Qualidade local | OK | `uv run ruff check .`, `uv run pytest`, `uv build` |
| Databricks Bundle validate | OK | `databricks bundle validate -t dev --profile dbc-d3858b75-976f` |
| Databricks Job | OK | Job `271536484960804`, run `7043957383197`, status `SUCCESS` |
| MLflow Tracking | OK | Experimento `/Shared/finance-basic` |
| Unity Catalog Model Registry | OK | Modelo `mlops_dev.finance.finance_lstm_model_basic`, alias `latest-model` |
| API FastAPI | Pronto para demo | Endpoints `/health`, `/predict`, `/agent/ask` |
| Agente financeiro | Pronto para demo | RAG local e tools auditaveis em `finance.agent` |
| Governanca | OK | Model Card, System Card, LGPD, OWASP e Red Teaming em `docs/` |

## Evidencias Recomendadas Para Anexar

Salve imagens em `docs/evidence/images/` se quiser deixar os prints versionados no repo.

1. Print da aba Actions do GitHub mostrando a run `25300452941` com status verde.
2. Print dos detalhes da action mostrando `Lint`, `Test`, `Build`, `Validate Databricks bundle`, `Deploy Databricks bundle` e `Run Databricks workflow`.
3. Print do Databricks Workflows mostrando o job `[dev lukaszago] MLET_TC05-workflow` com run `7043957383197` em `SUCCESS`.
4. Print das tasks do job: `preprocessing`, `train_model`, `model_updated`, `deploy_model`, `post_commit_status`.
5. Print do MLflow Experiments com metricas do treinamento.
6. Print do Unity Catalog Model Registry mostrando o modelo `finance_lstm_model_basic` e o alias `latest-model`.
7. Print ou output de teste da API FastAPI para `/health`, `/predict` e `/agent/ask`.
8. Print da pagina de colaboradores do GitHub se a banca exigir comprovante de acesso do colega.

## Arquivos Deste Pacote

- `GITHUB_ACTIONS.md`: evidencia da esteira CI/CD.
- `DATABRICKS_JOB.md`: evidencia do workflow Databricks.
- `MLFLOW_AND_REGISTRY.md`: evidencia de tracking e registro do modelo.
- `API_AND_AGENT.md`: evidencia da API e do agente financeiro.
- `LOCAL_VALIDATION.md`: comandos locais de validacao.
