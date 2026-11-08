# Validação isolada das migrações

Dentro desta pasta: `npm install` e `npm test`. Executa PostgreSQL embarcado PGlite em memória, sem conectar ao Predator. Testa DDL, papéis, histórico append-only e sobreposição de vigências. Não substitui integração psycopg/PostgreSQL 18 Windows nem testes de concorrência em servidor real.

Os 11 adaptadores também executam SQL real sobre fixtures isoladas. Para regenerar a captura após mudar operações: `python capture_queries.py` (com dependências do backend instaladas), seguido de `npm test`.
