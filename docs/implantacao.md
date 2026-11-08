# Instalação e publicação

## Preparação do Predator

Execute o núcleo na mesma VM que alcança o PostgreSQL, porta 8010. A API antiga na porta 8000 permanece separada. Configure serviço/agendador do Windows com diretório de trabalho `backend`, conta de serviço restrita, ambiente virtual e variáveis de ambiente. Desative logs de conteúdo/Authorization no proxy; os logs do app têm request ID, método, status e duração.

Um túnel de saída autorizado pelo TI deve encaminhar uma origem HTTPS dedicada ao `127.0.0.1:8010` da VM. Se o túnel estiver no host e o app na VM, localhost é outro computador: configure uma interface host-only e firewall restrito. Não publicar `/query`, PostgreSQL ou uma porta administrativa. O domínio da API já existente não foi alterado nesta entrega.

Exija autenticação de serviço no túnel (por exemplo Cloudflare Access service token) e `BRIDGE_TOKEN` no núcleo. No gateway, `PREDATOR_API_URL` é a origem HTTPS sem caminho; `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` e `BRIDGE_TOKEN` são segredos no Render. `/health` do núcleo informa somente processo vivo; toda rota de dados exige token da ponte e chave individual. Não desabilite validação TLS.

## Render

1. Repositório do projeto: https://github.com/ErisonNeto/J-T--J.A.R.V.I.S. . Ele foi criado como público; contém somente código, documentação e fixtures sintéticas. Nunca envie `.env`, SQLite, dumps, dados operacionais ou credenciais. Revise o PR da primeira versão antes de conectar a branch aprovada ao Render.
2. No Render, New Blueprint, selecione o repositório e revise `render.yaml`. Ele solicita um web service gratuito; disponibilidade/suspensão e adequação à operação precisam ser revisadas. Não houve criação de serviço ou cobrança nesta entrega.
3. Configure os quatro segredos de gateway. Use o mesmo BRIDGE_TOKEN no núcleo. Não colocar URL de PostgreSQL no gateway. Deploy automático está desligado.
4. Após deploy, confira `/health`; em seguida, `/api/status` com chave individual. Só o segundo confirma memória acessível. Teste também com o Predator desligado: o retorno esperado é 503 e texto de indisponibilidade.
5. Configure `JARVIS_API_URL` na Central com a URL HTTPS do gateway; revise e aprove o PR antes de integrar em produção.
6. Teste autenticação, conversa, confirmação, fontes e uma consulta real de cada indicador habilitado. Build e testes locais não substituem essa homologação.

O backend LLM roda no núcleo; API key e consentimentos ficam no Predator. Uma fase futura pode mover o núcleo e o PostgreSQL para rede privada de nuvem, mantendo a interface HTTP atual e reconfigurando a Central. Não faça escrita simultânea de memória em dois bancos.

## Diagnóstico

| Sintoma | Verificar |
|---|---|
| 401 origem não autorizada | BRIDGE_TOKEN no núcleo e gateway |
| 401 credencial inválida | chave individual, usuário ativo, banco correto |
| 403 | perfil: confirmação exige manager/admin; programação exige developer/admin |
| 409 na memória | outra correção foi salva; recarregue e revise |
| 422 | datas, intervalo, código ou evidência de confirmação |
| 429 | limite por usuário em 60 segundos |
| 503 memória | VM, PostgreSQL, usuário, senha, migrations |
| 503 indicador | OPERATIONAL_DATABASE_URL, aprovação, histórico e esquema |
| 503 gateway | túnel, TLS, política Access, Predator desligado |
| Sem dados | datas sem carga, regional exata, vigências ausentes; não significa zero |
| IA em modo local | chave/modelo/ALLOW_EXTERNAL_AI no núcleo |
| Pesquisa indisponível | consentimento separado e modelo com web_search |
| Voz não funciona | HTTPS/localhost, suporte e permissão do navegador |

## Backup e retenção

Use `scripts/backup.ps1 -Destination <pasta-protegida>` com PostgreSQL bin no PATH e credencial via PGPASSFILE/serviço local. O script salva apenas schema jarvis; faça backup independente da operação. Proteger dumps com criptografia e ACL; manter cópia fora do notebook.

Restauração: em um banco de teste vazio, preparar papéis e executar `pg_restore --dbname=<banco-teste> --no-owner arquivo.dump`. Conferir usuários, conversas, mensagens, revisões, vigências e auditoria. Não usar `--clean` no banco operacional. Testar restauração regularmente antes de depender do backup.

Retenção proposta de 365 dias é configurável, não aplicada automaticamente. `python -m jarvis.cli retention-preview` lista a quantidade de conversas candidatas sem apagar. Definir política corporativa antes de migrar para expurgo aprovado, incluindo mensagens, revisões, investigações e backups. Aplicação não tem DELETE em auditoria.
