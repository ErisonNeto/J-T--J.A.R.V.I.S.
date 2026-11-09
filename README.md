> **Web com banco próprio:** veja [docs/web-render.md](docs/web-render.md). Um único serviço hospeda a interface e um chat temporário de teste com GPT-4.1 mini. A memória permanente e os indicadores aguardam integração com a JT API existente; nenhum banco novo é criado.

# JARVIS — primeira versão executável

Assistente de Inteligência Operacional da Regional Orlean — J&T Express.

Esta entrega contém backend FastAPI, frontend Next.js, memória persistente, consultas controladas, gateway para Render e migrações PostgreSQL. **Não está conectado ao Predator nem publicado no Render.** Os adaptadores foram construídos a partir dos repositórios reais, mas seus resultados ainda precisam de comparação com o banco da empresa. Nenhum número de produção foi usado ou simulado.

## Começar no Windows — modo local

Pré-requisitos: Python 3.12, Node compatível com a Central (22.13+), npm. Extraia o ZIP; abra PowerShell na pasta `J-T-JARVIS`.

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item ..\.env.example .env
.\.venv\Scripts\python.exe -m jarvis.cli user --name Orlean --role manager
```

Guarde a chave individual exibida. Para programação, crie outro usuário com perfil `developer` ou `admin`. Nunca compartilhe uma chave entre usuários. O SQLite é criado **somente para desenvolvimento**, vazio, sem indicadores fictícios. Para executar:

```powershell
.\.venv\Scripts\python.exe -m uvicorn jarvis.main:create_app --factory --host 127.0.0.1 --port 8010
```

Em outro PowerShell, na raiz do projeto:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Abra `http://localhost:3000/jarvis`, entre com sua chave e experimente conversar e registrar hipóteses na aba Memória. A primeira resposta informa que a fonte operacional ainda não foi configurada. As memórias e conversas persistem no SQLite; não são descartadas ao reiniciar o backend.

## Ativar a conversa com IA

No `backend/.env`, configure `OPENAI_API_KEY` e `OPENAI_MODEL` com um modelo disponível no seu projeto de API. Só defina `ALLOW_EXTERNAL_AI=true` após autorização organizacional para enviar mensagens, resultados agregados e memórias recuperadas ao provedor. Credenciais ficam no backend. `store:false` não substitui a avaliação da política de retenção do provedor.

Reinicie o backend. A opção **Interpretar pergunta** permite ao modelo planejar até três consultas tipadas. Códigos de base não identificados devem gerar pedido de esclarecimento. Filtros de base, gestor e datas explícitos não podem ser ampliados pelo planejador. Desmarcando essa opção, a consulta usa exatamente os filtros da tela. Sem modelo, o modo local tem respostas determinísticas limitadas; não equivale a uma IA conversacional completa.

Perguntas de exemplo: “Como está o SLA?”, “Compare o Shipping Time e o SLA desta semana”. A capacidade real depende do modelo, da disponibilidade das fontes e do recorte selecionado. Não há geração ou execução de SQL pelo modelo.

## Conectar PostgreSQL 18 no Predator

A instalação real deve ser feita na VM/máquina que alcança o banco. **Não use `10.0.2.15` como endereço público.** Não abra a porta 5432 na internet. O usuário de migração é diferente dos usuários de execução.

1. Faça backup do banco existente e confirme o banco de destino. As migrações adicionam apenas objetos em `jarvis` e dois papéis; não atualizam dados operacionais.
2. Como administrador, aplique os arquivos em ordem com parada em erro:

```powershell
psql -U postgres -d jt_indicadores -v ON_ERROR_STOP=1 -f migrations/001_memory.sql
psql -U postgres -d jt_indicadores -v ON_ERROR_STOP=1 -f migrations/002_historical_scope.sql
psql -U postgres -d jt_indicadores -v ON_ERROR_STOP=1 -f migrations/003_permissions.sql
psql -U postgres -d jt_indicadores
```

No psql, use `\password jarvis_memory` e `\password jarvis_reader`; saia com `\q`. Não coloque senhas em argumentos de shell. Migrações não devem ser reaplicadas: confira `SELECT * FROM jarvis.schema_migrations ORDER BY version`. Cada arquivo é transacional.

3. Configure `MEMORY_DATABASE_URL` e `OPERATIONAL_DATABASE_URL` no `.env`, usando respectivamente os usuários `jarvis_memory` e `jarvis_reader`, conforme `.env.example`. Escape caracteres especiais das senhas na URL. Ambos devem apontar para `jt_indicadores`; nunca use `postgres` ou o proprietário do banco na aplicação.
4. Execute, dentro de `backend`:

```powershell
.\.venv\Scripts\python.exe -m jarvis.cli discover > ..\schema-real.csv
```

Compare o resultado com [docs/indicadores.md](docs/indicadores.md). A descoberta consulta metadados; não copia remessas, nomes de clientes ou outros registros pessoais.
5. Preencha uma cópia de `scripts/historical_assignments.example.csv` com códigos, nomes, S/C, regional, início/fim de vigência e evidência documental. Não foi criada gestão fictícia. O nome da regional deve coincidir exatamente com `REGIONAL_NAME`. Não há cadastro retroativo automático da gestão atual.
6. Importe as vigências com uma conexão administrativa temporária no processo CLI; essa operação não pode usar `jarvis_memory`, que não tem escrita nessa tabela. Execute `python -m jarvis.cli assignments caminho.csv`. Não persista a credencial administrativa no `.env` de execução. O importador é transacional e bloqueia intervalos sobrepostos.
7. Compare manualmente os recortes com os dashboards. Só então configure, por exemplo, `APPROVED_INDICATORS=sla,t0`. Inclua os demais após validação individual. CSAT permanece indisponível até existir fonte e fórmula verificadas.
8. Crie novamente os usuários no PostgreSQL com `jarvis.cli user`. A memória de desenvolvimento não migra automaticamente para produção.
9. Defina `APP_ENV=production`, configure `BRIDGE_TOKEN` aleatório com 32+ caracteres e reinicie. O backend recusa credenciais que possam alterar tabelas operacionais, criar objetos no schema público ou administrar o banco. Grants herdados de PUBLIC precisam ser corrigidos pelo DBA, sem revogações indiscriminadas.

## Central e Render

O frontend foi desenvolvido com as versões da Central existente. Para integrar, copie somente `frontend/app/jarvis/` e `frontend/app/api/jarvis/` para a mesma estrutura da Central e adicione um link `/jarvis`. Não substitua `app/page.tsx`, layout, package.json ou rotas de indicadores. Há uma branch/PR de integração preparada quando o acesso ao GitHub permite; veja o relatório de validação.

Na Central, configure `JARVIS_API_URL=https://<gateway-render>`. Não use `NEXT_PUBLIC_` para segredos. A chave individual é mantida apenas na memória da aba; recarregar requer novo login. A Central não recebe uma chave de gestor compartilhada.

[docs/implantacao.md](docs/implantacao.md) descreve túnel HTTPS, gateway, publicação e diagnóstico. O `render.yaml` publica somente o gateway, **não cria banco ou disco no Render**. O núcleo e a memória ficam no Predator nesta fase. Isso mantém uma única fonte persistente, mas significa indisponibilidade quando o notebook estiver desligado.

## Voz, memória e pesquisa

- Microfone: botão, sem escuta contínua; Web Speech API conforme suporte do navegador. O ditado preenche o campo e não envia automaticamente. Pode depender de um serviço externo do navegador; a interface informa isso. Resposta por voz é opcional e pode ser interrompida. Áudio não é gravado no backend. Não foi testado com microfone físico.
- Memória: hipóteses, confirmação atribuída ao gestor, rejeição, correções versionadas, ações, resultados posteriores e auditoria. Analistas consultam; gestores/admins registram e confirmam. Toda a memória é compartilhada dentro desta única regional. Conversas são privadas por usuário.
- Recuperação: busca lexical local nas 500 memórias mais recentes, com filtro de base. **Não é busca semântica nem fine-tuning.** Embeddings/pgvector são evolução documentada, não instalados silenciosamente no Windows.
- Pesquisa: `ALLOW_EXTERNAL_SEARCH=true` além de IA habilitada. Usa busca web do modelo; envia cidade, UF e período, sem métricas internas. Guarda fontes citadas, classificação e causalidade não comprovada. Não possui conector meteorológico/feriados dedicado nem escore de confiança validado.
- Desenvolvimento: produz código e testes no chat para revisão. Não inspeciona repositórios em tempo de execução, não executa shell, não cria PRs automaticamente e não modifica produção. O agente isolado está previsto na evolução.

## Testar

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
cd ..\frontend
npm ci
npm run build
```

Testes usam banco temporário e dados sintéticos isolados. Para validar migrações sem tocar no Predator, veja `validation/README.md`. A aceitação real está em [docs/aceitacao.md](docs/aceitacao.md).

## Estrutura

- `backend/jarvis`: autenticação, chat, planejador, memória, adaptadores, investigação, gateway e CLI.
- `frontend/app/jarvis`: interface integrada e voz.
- `frontend/app/api/jarvis`: proxy Next.js com lista de rotas permitidas.
- `migrations`: schema versionado, vigências de gestão e permissões.
- `scripts`: execução, backup e exemplo de gestão histórica.
- `docs`: arquitetura, diagnóstico, implantação, aceitação e evolução.

Não estão incluídos segredos, dados internos, node_modules, ambiente virtual ou banco de desenvolvimento.
