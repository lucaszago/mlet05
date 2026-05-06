# Evidência: Execuções do Workflow Databricks

## Identificação

- Workspace: `https://dbc-d3858b75-976f.cloud.databricks.com`
- Bundle: `MLET_TC05`
- Target: `dev`
- Job: `[dev lukaszago] MLET_TC05-workflow`
- Job ID: `271536484960804`

---

## Histórico de Execuções (Mai 2026)

| Data/Hora (UTC-3) | Run ID | Disparado por | Duração | Status |
|---|---|---|---|---|
| 2026-05-04 05:14 PM | `205087470861753` | Manually | 8m 15s | ✅ Succeeded |
| 2026-05-04 01:18 AM | `10418983883744296` | Manually | 8m 9s | ✅ Succeeded |
| 2026-05-04 01:06 AM | `7043957383197` | Manually | 9m 31s | ✅ Succeeded |
| 2026-05-04 01:05 AM | `731691234650262` | Manually | 3m 1s | ❌ Failed (RunExecutionError) |
| 2026-05-04 12:52 AM | `1129779968925212` | Manually | 9m 53s | ✅ Succeeded |
| 2026-05-04 12:35 AM | `375844195554899` | Manually | 6m 53s | ✅ Succeeded |

**5 de 6 execuções recentes finalizaram com sucesso.**

---

## Detalhes da Run 205087470861753 (última bem-sucedida)

### DAG — Todas as Tasks Concluídas

```
preprocessing (2m 31s) ─► train_model (4m 29s) ─► model_updated ─► deploy_model (41s) ─► post_commit_status (29s)
  ✅ Succeeded              ✅ Succeeded              ✅ True           ✅ Succeeded          ✅ Succeeded
```

| Task | Script | Duração | Status |
|------|--------|---------|--------|
| `preprocessing` | `scripts/process_data.py` | 2m 31s | ✅ Succeeded |
| `train_model` | `scripts/02.train_register_fe_model.py` | 4m 29s | ✅ Succeeded |
| `model_updated` | condition: `{{updated}} == "1"` | — | ✅ True |
| `deploy_model` | `scripts/03.deploy_model.py` | 41s | ✅ Succeeded |
| `post_commit_status` | `scripts/04.post_commit_status.py` | 29s | ✅ Succeeded |

---

## Output da Task deploy_model

```
2026-05-04 20:22:04.802 | INFO | __main__:main:71 - Configuration loaded:
2026-05-04 20:22:04.827 | INFO | __main__:main:72 - cat_features: []
catalog_name: mlops_dev
experiment_name_basic: /Shared/finance-basic
experiment_name_custom: /Shared/finance-custom
experiment_name_fe: /Shared/finance-fe
num_features:
  - Close
parameters:
  batch_size: 32
  end_date: '2024-07-20'
  epochs: 100
  sequence_length: 60
  start_date: '2018-01-01'
  symbol: DIS
  train_ratio: 0.8
pipeline_id: 9b8df4fc-bfe1-4cc1-9534-e579a017629d
schema_name: finance
target: Close

2026-05-04 20:22:04.828 | INFO | __main__:main:77 - Spark session ready
2026-05-04 20:22:04.829 | INFO | __main__:main:82 - Validating registered model URI:
                                                     models:/mlops_dev.finance.finance_lstm_model_basic@latest-model
2026-05-04 20:22:14.446 | INFO | __main__:main:84 - Deployment validation completed for command 'deployment'.
```

**Modelo validado com sucesso no alias `latest-model`.**

---

## Unity Catalog — Tabelas Delta Geradas

Catálogo/schema: `mlops_dev.finance` — 2 tabelas criadas pelo pipeline de preprocessamento.

### `mlops_dev.finance.train_set`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `dataset` | string | `"train"` |
| `sequence` | array | Janela de 60 valores normalizados (MinMaxScaler) |
| `target` | float | Valor alvo normalizado |
| `target_unscaled` | float | Valor alvo em escala original (preço de fechamento DIS) |
| `update_timestamp_utc` | timestamp | Data/hora de ingestão |

Exemplo de `target_unscaled`: valores entre ~93–100, consistente com histórico DIS 2018–2024.

### `mlops_dev.finance.test_set`

Mesma estrutura de `train_set`, com `dataset = "test"`. Split cronológico de 20% dos dados (2023–2024).

**Change Data Feed habilitado em ambas as tabelas** para suporte a ingestão incremental.

---

## Configuração do Treinamento

| Parâmetro | Valor |
|-----------|-------|
| Ativo | DIS (The Walt Disney Company) |
| Período | 2018-01-01 → 2024-07-20 |
| Feature | Close (preço de fechamento) |
| Janela (sequence_length) | 60 dias |
| Train ratio | 80% |
| Épocas máximas | 100 |
| Batch size | 32 |

---

## Como Revalidar

```bash
databricks bundle validate -t dev --profile dbc-d3858b75-976f
databricks bundle deploy -t dev --profile dbc-d3858b75-976f
databricks bundle run deployment -t dev --profile dbc-d3858b75-976f
```

URL da última run bem-sucedida:
```
https://dbc-d3858b75-976f.cloud.databricks.com/?o=299177927171866#job/271536484960804/run/205087470861753
```
