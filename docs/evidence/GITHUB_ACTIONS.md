# Evidencia: GitHub Actions

## Resultado Validado

- Repositorio: `https://github.com/lucaszago/mlet05`
- Branch validada: `main`
- Commit: `dac5cef fix: set bundle repository metadata`
- Workflow: `ci`
- Run: `25300452941`
- Status: `success`
- Data da evidencia: `2026-05-04`

## O Que A Esteira Executa

A esteira esta definida em `.github/workflows/ci.yml` e cobre:

1. Checkout do codigo.
2. Instalacao do `uv`.
3. Setup de Python `3.11`.
4. Instalacao de dependencias com `uv sync --group dev`.
5. Lint com `uv run ruff check .`.
6. Testes com `uv run pytest`.
7. Build do pacote com `uv build`.
8. Instalacao do Databricks CLI.
9. Validacao do segredo `DATABRICKS_TOKEN`.
10. Validacao do bundle com `databricks bundle validate -t dev`.
11. Deploy do bundle em push para `main`.
12. Execucao do workflow Databricks em push para `main`.

## Como Revalidar

```bash
gh run list --repo lucaszago/mlet05 --limit 5
gh run view 25300452941 --repo lucaszago/mlet05
```

## Evidencia Visual Recomendada

Anexar print da run `25300452941` mostrando todos os steps concluidos com sucesso. Se usar screenshot no repo, salvar em:

```text
docs/evidence/images/github-actions-run-25300452941.png
```
