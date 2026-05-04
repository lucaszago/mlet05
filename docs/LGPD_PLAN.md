# Plano LGPD

## Classificação de Dados

O projeto atual usa dados públicos de mercado financeiro via `yfinance`, sem dados pessoais identificáveis.

## Controles

- Secrets devem ficar em variáveis de ambiente, nunca no Git.
- `.env.example` documenta variáveis sem valores sensíveis.
- Dados brutos não devem ser commitados.
- Dados sintéticos/fixtures são usados em testes.

## Evolução Necessária

Se a empresa convidada fornecer dados com PII, adicionar detecção/mascaramento antes de persistência em Delta e registrar finalidade, base legal, retenção e responsáveis.
