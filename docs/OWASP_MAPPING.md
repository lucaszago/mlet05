# OWASP Mapping

## Ameaças Mapeadas

- Prompt injection: agente valida padrões explícitos de prompt injection em `finance.security.guardrails`.
- Sensitive information disclosure: mitigar via secrets em env vars e bloqueio de logs sensíveis.
- Insecure output handling: validar payloads com Pydantic na API.
- Excessive agency: agente opera com allowlist fixa de tools e não executa comandos arbitrários.
- Model denial of service: limitar tamanho de `sequences` e configurar timeout/retry no serving.

## Estado Atual

A API usa validação Pydantic e falha fechada quando `MODEL_URI` não está configurado. Rate limit, auth e limites de payload devem ser adicionados antes de exposição pública.
