# JARVIS web independente — ambiente de testes

O Blueprint cria dois serviços web gratuitos (Next.js e FastAPI) e um PostgreSQL gratuito exclusivo para conversas, usuários, memórias e auditoria. A fonte operacional continua sendo JT_API_URL /query. Nenhuma migração é aplicada no banco operacional. Os recursos existentes da Central e dos indicadores não participam deste Blueprint.

O PostgreSQL gratuito do Render tem prazo de validade: use este ambiente para homologação e migre/atualize o plano antes da expiração informada pelo Render. Serviços gratuitos podem hibernar e consumir as horas gratuitas compartilhadas do workspace. A OpenAI cobra o consumo da API conforme sua conta.

## Segredos
JT_API_KEY, OPENAI_API_KEY e JARVIS_BOOTSTRAP_TOKEN são preenchidos somente no Render. Nunca publicar .env ou o ZIP privado no GitHub. O token individual de bootstrap cria um usuário Orlean com perfil manager, uma única vez por hash. Não imprime o token. O segredo entre frontend e backend e a senha do usuário de memória são gerados pelo Render.

JARVIS_MEMORY_ADMIN_URL é usado somente durante a inicialização do banco dedicado jt_jarvis_memory. O processo da API recebe a URL com usuário restrito jarvis_memory; a credencial administrativa é removida do ambiente antes do exec da API. O processo da API recusa privilégios excessivos sobre public e exige token de origem e token individual.

## Testes após publicação
1. GET /jarvis no frontend: tela abre.
2. GET /health no backend: banco de memória responde.
3. GET /api/status sem autenticação: HTTP 401.
4. Entrar pela interface com o token individual e verificar /api/jarvis/status.
5. GET /api/jarvis/diagnostics autenticado: consultar conexão JT API e quantidade de vínculos históricos sem expor registros.
6. Criar conversa, enviar mensagem, recarregar e confirmar persistência.
7. Registrar hipótese em Memória e verificar o histórico.
8. Testar GPT-4.1 mini com mensagem curta; disponibilidade e crédito dependem da chave fornecida.

APPROVED_INDICATORS inicia vazio. Antes de habilitar qualquer indicador, validar acesso à gestão histórica, preencher os vínculos com evidência e comparar fórmulas com o dashboard. Ausência de cadastro histórico não significa ausência de entregas. O chat deve informar indisponibilidade em vez de inventar números.

A interface deste primeiro deploy é a versão funcional existente. A evolução visual para o HUD futurista e o PWA serão posteriores à homologação funcional.
