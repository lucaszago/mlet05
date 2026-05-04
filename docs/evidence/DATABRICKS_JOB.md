# Evidencia: Databricks Job

## Resultado Validado

- Workspace: `https://dbc-d3858b75-976f.cloud.databricks.com`
- Bundle: `MLET_TC05`
- Target: `dev`
- Job: `[dev lukaszago] MLET_TC05-workflow`
- Job ID: `271536484960804`
- Run ID: `112977968925212`
- Status: `SUCCESS`
- URL da run: `https://dbc-d3858b75-976f.cloud.databricks.com/?o=299177927171866#job/271536484960804/run/112977968925212`
- Data da evidencia: `2026-05-04`

## Tasks Do Workflow

O workflow principal esta em `databricks.yml`:

1. `preprocessing`: baixa dados financeiros, cria sequencias e grava `train_set` e `test_set` no Delta/Unity Catalog.
2. `train_model`: treina LSTM, registra metricas no MLflow e publica o modelo no Unity Catalog.
3. `model_updated`: valida se houve atualizacao de modelo.
4. `deploy_model`: valida o carregamento do modelo registrado pelo alias `latest-model`.
5. `post_commit_status`: registra status final da execucao.

## Como Revalidar Localmente

```bash
databricks bundle validate -t dev --profile dbc-d3858b75-976f
databricks bundle deploy -t dev --profile dbc-d3858b75-976f
databricks bundle run deployment -t dev --profile dbc-d3858b75-976f
```

Se houver erro de multiplos profiles para o mesmo host, usar:

```bash
export DATABRICKS_CONFIG_PROFILE=dbc-d3858b75-976f
databricks bundle validate -t dev
```

## Evidencia Visual Recomendada

Anexar print da run `112977968925212` mostrando status `SUCCESS` e a lista de tasks. Se usar screenshot no repo, salvar em:

```text
docs/evidence/images/databricks-job-run-112977968925212.png
```
