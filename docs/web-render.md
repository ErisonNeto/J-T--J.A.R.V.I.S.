# JARVIS web — PostgreSQL e JT API existentes

O Blueprint cria somente o frontend Next.js gratuito no Render. Não cria banco nem backend extra. A configuração anterior de três recursos foi substituída após a decisão de reutilizar o PostgreSQL próprio.

## Dependência antes de aplicar o plano

A JT Server API na VM precisa expor o backend autenticado do JARVIS em /jarvis. Os endpoints esperados incluem /jarvis/health, /jarvis/api/status, /jarvis/api/chat e os endpoints de memórias e conversas já implementados em backend/jarvis/main.py. A rota /query existente, sozinha, não implementa esses endpoints.

É necessário inspecionar o código da JT Server API antes de montar esse backend, para preservar as rotas dos indicadores, a autenticação, a configuração e o processo existentes. O JARVIS usa jarvis_memory para guardar conversas e memórias no schema jarvis do banco jt_indicadores, já preparado com as migrações 001–003. Não executar essas migrações novamente. Dados operacionais podem continuar sendo lidos por JT_API_URL e JT_API_KEY.

## Configuração

No frontend Render: JARVIS_API_URL aponta para a montagem HTTPS /jarvis da API existente. JARVIS_BRIDGE_TOKEN fica apenas no servidor Next.js e deve coincidir com BRIDGE_TOKEN no backend JARVIS da VM. O token individual do usuário continua separado do segredo de origem.

A chave OpenAI, a chave JT e a senha do usuário jarvis_memory ficam no backend da VM. Usar OPENAI_MODEL=gpt-4.1-mini e APP_ENV=production. Não usar o inicializador jarvis.deploy nesta arquitetura: ele foi criado para um banco isolado no Render e deve continuar sem execução.

## Verificação

Antes do deploy do frontend: verificar /jarvis/health e a rejeição de /jarvis/api/status sem autenticação. Depois: testar o login, /api/jarvis/diagnostics pela interface, uma conversa, persistência após recarregar e uma memória. Os indicadores permanecem desabilitados até validar a gestão histórica e a comparação com os dashboards.

O código de integração da JT API ainda não foi recebido nem alterado. Portanto, a montagem /jarvis ainda não está confirmada e o plano não deve ser aplicado como se o backend já estivesse disponível.
