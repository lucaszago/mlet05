# Model Card — Finance LSTM

## Visão Geral

Modelo LSTM de regressão para previsão de preço de fechamento de ativo financeiro configurado em `project_config.yml`.

## Dados

- Fonte: `yfinance`, parametrizada por `SYMBOL`, `START_DATE` e `END_DATE`.
- Persistência: tabelas Delta `train_set` e `test_set` no Unity Catalog.
- Lineage: registro via MLflow quando executado fora de Spark Connect.

## Métricas

O treinamento registra `mae`, `rmse`, `mape` e `r2` no MLflow.

## Governança

Tags obrigatórias registradas no MLflow/Unity Catalog:

- `model_name`
- `model_version`
- `model_type`
- `training_data_version`
- `metrics`
- `owner`
- `risk_level`
- `fairness_checked`
- `git_sha`

## Limitações

O modelo usa apenas a série de preço de fechamento, portanto não deve ser interpretado como recomendação financeira. A previsão é sensível a mudanças macroeconômicas, eventos corporativos e regimes de mercado.
