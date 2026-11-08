# Relatório de validação — 08/11/2026

## Resultados executados

- Backend: **15 testes pytest aprovados**. Autenticação, RBAC, isolamento de conversas, persistência entre instâncias, hipótese/confirmada/corrigida, auditoria, conflitos, filtros inválidos/injeção, indisponibilidade sem números fictícios, datas, cálculos ponderados, pesquisa externa bloqueada, recuperação lexical, limite de uso, token da ponte, restrição do planejador, falha do provedor sem gravação parcial, ranking/comparações, gateway e payload do modelo.
- HTTP: processo Uvicorn iniciado em porta isolada, `/health` respondeu 200.
- PostgreSQL embarcado PGlite: migrations 001, 002 e 003 executadas; vigências sobrepostas recusadas; leitor impedido de apagar vigências/escrever memórias; papel de memória impedido de apagar auditoria/editar revisões.
- SQL dos **11 adaptadores** executado em PostgreSQL embarcado com fixtures isoladas. Conferidos numeradores/denominadores, exclusão de outra regional, vigência, aging >3/>10, etapas nulas e exclusão de status não finais.
- Frontend independente: `npm run build` aprovado com TypeScript e rotas `/jarvis` e proxy.
- Central com integração: `npm test` aprovado (S/C, direct, SQL, Qualidade e arbitragem) e `npm run build` aprovado. Cálculos/rotas existentes preservados.
- `render.yaml`: validado pelo JSON Schema atual obtido de https://render.com/schema/render.yaml.json. Não foi executada validação autenticada no Render nem deploy.
- Formatação: Black no Python e Prettier nos componentes novos.

O TestClient emite aviso de depreciação do transporte httpx; os testes passam, e a migração para o novo transporte pode ser tratada na próxima manutenção.

## Limites de verificação

Não houve conexão com o PostgreSQL 18 real do Predator, chave de LLM, chamada real de web_search, túnel, serviço Render ou áudio físico. PGlite não prova compatibilidade integral com PostgreSQL 18 Windows. A prévia de navegador não conseguiu alcançar o servidor local (conexão recusada); não se declara revisão visual concluída. Não foram geradas previsões.

A aplicação exige configuração e homologação, explicitadas no README. As consultas reais ficam desabilitadas por padrão. Nenhum segredo ou dado operacional foi incluído no pacote.

## Integração da Central

PR em rascunho: https://github.com/ErisonNeto/Central-de-Indicadores/pull/2
Branch: `feat/jarvis-assistant`. Nenhum merge ou deploy realizado.
Arquivos: `app/jarvis/page.tsx`, `app/jarvis/jarvis.css`, `app/api/jarvis/[...path]/route.ts`, `JARVIS.md` e um link adicional em `app/page.tsx`. Não há dependência nova na Central.

## Revisões de origem inspecionadas

| Checkout | Commit de origem |
|---|---|
| central | `d16fc94224926ec5fe1e2b27d56ef2aa37d22ac3` |
| sla | `2292206d8439762e0efb89b83d6ce876322e57f1` |
| t0 | `6c89dde62952c8edc67fff639d072e3d82a8a77b` |
| shipping | `a19022ba5f56f911c9ee18c6ba02210e5b1d1014` |
| cap | `35600b54494df990a2ab47eeb2203364eb790527` |
| aging | `f95c5f9243a3f415f4c3a142f40bdf27edc64704` |
| quality | `bed0a5f2cb525b3d8766acea721e2caf563f5fbc` |
| claims | `ce2df43b18b867d4b04009240b111573e75d91bf` |
