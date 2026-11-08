# Aceitação e evolução

## Critérios para liberar uso real

- Migrações 1–3 aplicadas no banco certo, com backup e restauração de ensaio.
- Papéis do app sem escrita operacional direta, herdada ou via PUBLIC; startup de produção aprovado.
- Gestão por código e vigência completa, sem sobreposição; transferências de bases testadas.
- Paridade de cada indicador aprovado, documentando diferenças em nulos/fechamento; CSAT bloqueado.
- PostgreSQL real validado via psycopg, não apenas SQLite/PGlite.
- Chaves individuais provisionadas; analista não confirma causa; conversas de outro usuário inacessíveis.
- Hipótese persistida, confirmada pelo gestor, corrigida e auditada; conflito concorrente retorna 409.
- LLM configurada e consentimento de dados autorizado; respostas citam números do contexto, sem alegar causas não confirmadas.
- Túnel, Render e Central testados ponta a ponta; notebook desligado retorna indisponibilidade.
- Testes visuais desktop/mobile, voz e interrupção com usuário. Sem acessibilidade visual homologada nesta sessão.

## Etapas entregues e pendentes

| Etapa | Implementação | Pendência real |
|---|---|---|
| 1 Diagnóstico | Repositórios da Central e sete indicadores inspecionados, regras documentadas | Metadados e amostras do PostgreSQL real |
| 2 Fundação | FastAPI, autenticação, roles, migrations, limites e testes | Aplicar migrations na VM |
| 3 Inteligência | Responses API, planejamento tipado e consultas fixas, histórico | Teste com chave/modelo real e avaliação de respostas |
| 4 Memória | Hipótese/confirmação/rejeição, versões, evidências, ações, auditoria | Recuperação semântica; UI de métricas estruturadas |
| 5 Indicadores | 11 adaptadores, percentuais ponderados, série, ranking, comparações | CSAT, detalhamento das etapas 6/7/8, metas, auditoria separada de arbitragem e homologação |
| 6 Interface/voz | Next.js, chat, filtros, histórico, memória, pesquisa, Web Speech | Teste visual e com microfone físico |
| 7 Pesquisa | Ferramenta web_search com fontes; cidade/UF/período | Teste com provedor, fontes estruturadas e avaliação de confiança |
| 8 Publicação | Gateway HTTPS e Blueprint, documentação Windows | Túnel, segredos, deploy e teste ponta a ponta |
| 9 Evolução | Plano abaixo | Implementação e validação separadas |

## Busca semântica

Primeiro avaliar corpus local com casos anotados pelo gestor, incluindo casos rejeitados. Medir recall@k e precisão das recuperações com separação temporal. Antes de pgvector, verificar release compatível com PostgreSQL 18 e instalação Windows/VM; não aplicar extensão sem ensaio. Embeddings externos só após consentimento e minimização. Migration futura: memória_id, modelo, dimensão, hash do texto, vetor e data; reindexar em correções, excluir hipóteses rejeitadas da recuperação. Similaridade nunca equivale a causa.

## Predição

Definir evento-alvo e horizonte com a operação. Baseline de persistência e medianas móveis; testar modelos simples com features históricas de Shipping, retidos e volume, sem usar dados disponíveis somente após o evento. Divisão temporal rolling-origin; medir precisão/recall dos alertas, falsos positivos por base/semana e calibração, comparando ao baseline. Avaliar bases sem histórico, feriados e mudanças de gestão. Só emitir alertas preditivos após validação e monitoramento de drift. Nenhuma previsão é emitida na v0.1.

## Agente de desenvolvimento

Etapa futura: GitHub App com repositórios permitidos, leitura de branch, sandbox efêmero sem credenciais de produção, limites de CPU/memória/rede, testes e diff revisável. Escrita apenas em branches, PR com rastreabilidade e aprovação humana antes de merge/deploy. O endpoint atual não recebe comandos nem executa código. Memória e conteúdo externo são dados, nunca instruções para liberar ferramentas.
