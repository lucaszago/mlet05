# Evidencia: Validacao Local

## Ambiente

- Python: `3.11`
- Gerenciador: `uv`
- Branch de trabalho: `feature/lz`
- Data da evidencia: `2026-05-04`

## Comandos

```bash
uv sync --group dev
uv run ruff check .
uv run pytest
uv build
databricks bundle validate -t dev --profile dbc-d3858b75-976f
```

## Resultado Validado

- Testes locais: `15 passed`
- Cobertura local observada: `86.24%`
- `databricks bundle validate`: `Validation OK`

## Observacoes

Os warnings observados nos testes sao de bibliotecas transitivas do PySpark/pyarrow e nao impedem a execucao. O bundle deve ser validado com `--profile dbc-d3858b75-976f` localmente para evitar conflito quando existem multiplos profiles apontando para o mesmo host.
