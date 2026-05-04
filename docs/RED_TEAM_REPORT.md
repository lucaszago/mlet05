# Red Team Report

## Cenários Testados

- Requisição de predição sem `MODEL_URI`: API retorna `503`.
- Payload vazio: validação Pydantic rejeita a entrada.
- Feature drift crítico: PSI sinaliza `critical` para distribuição deslocada.
- Configuração inválida de ambiente: `ProjectConfig` rejeita ambientes fora de `dev`, `acc`, `prd`.
- Modelo registrado indisponível: script de deploy falha ao carregar o alias `latest-model`.

## Próximos Testes

- Carga concorrente no endpoint `/predict`.
- Payloads muito grandes.
- Token Databricks inválido/expirado.
- Drift em múltiplas features.
- Teste de rollback para versão anterior do modelo.
