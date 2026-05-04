# Evidencia: MLflow E Unity Catalog

## MLflow Tracking

- Experimento esperado: `/Shared/finance-basic`
- Origem: task `train_model`
- Conteudo esperado: parametros de treino, metricas, artefatos e modelo LSTM.

Metricas principais a evidenciar na apresentacao:

1. `test_mse`
2. `test_rmse`
3. `test_mae`
4. Parametros do dataset e da janela temporal.
5. `git_sha` e `job_run_id` registrados na run.

## Unity Catalog Model Registry

- Catalogo/schema: `mlops_dev.finance`
- Modelo: `finance_lstm_model_basic`
- Nome completo: `mlops_dev.finance.finance_lstm_model_basic`
- Alias de consumo: `latest-model`
- URI usada pela API: `models:/mlops_dev.finance.finance_lstm_model_basic@latest-model`

## Como Validar No Databricks

1. Abrir `Experiments` e procurar `/Shared/finance-basic`.
2. Abrir a run gerada pelo job `7043957383197`.
3. Conferir metricas e artefatos.
4. Abrir `Catalog > mlops_dev > finance > Models`.
5. Conferir se `finance_lstm_model_basic` existe e possui alias `latest-model`.

## Evidencia Visual Recomendada

Salvar os prints em:

```text
docs/evidence/images/mlflow-experiment-finance-basic.png
docs/evidence/images/unity-catalog-model-latest-model.png
```
