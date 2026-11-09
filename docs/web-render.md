# JARVIS web — chat temporário e integração com banco próprio

O Blueprint cria somente um serviço Next.js gratuito no Render. Não cria outro banco. A versão de teste pode conversar com GPT-4.1 mini diretamente no servidor enquanto a VM está sem acesso administrativo.

## Chat temporário

JARVIS_WEB_PREVIEW=true habilita um backend web restrito ao token individual configurado em JARVIS_WEB_ACCESS_TOKEN. Credenciais OpenAI e JT ficam apenas no servidor. A interface avisa que as conversas são temporárias: permanecem na memória do processo por no máximo 24 horas, 20 conversas e 40 mensagens por conversa, e desaparecem quando o Render reinicia ou hiberna. Não são gravadas no PostgreSQL. Memórias operacionais, pesquisas e análises ficam indisponíveis; não existem números de demonstração.

O botão Testar conexões faz somente SELECT 1 e COUNT(*) em jarvis.base_assignments pela JT API, além de verificar acesso ao modelo OpenAI. Não permite SQL recebido do navegador ou do modelo. Existem limites por token de 30 requisições/minuto neste processo, tamanho da mensagem, histórico e concorrência. Os limites por instância não são proteção distribuída.

## Integração permanente pendente

Quando houver acesso à VM, inspecionar C:\JT.SERVER\api\main.py e integrar o backend autenticado JARVIS em /jarvis, usando jarvis_memory no schema jarvis já criado no banco jt_indicadores. Não executar novamente as migrações. Configurar BRIDGE_TOKEN na VM e o mesmo valor em JARVIS_BRIDGE_TOKEN no frontend. Desabilitar JARVIS_WEB_PREVIEW somente depois de testar /jarvis/health e /jarvis/api/status.

Não usar jarvis.deploy nesta arquitetura: ele foi criado para um banco isolado no Render e permanece sem execução. A JT API existente continua sendo a fonte dos indicadores. O cadastro histórico e as fórmulas ainda precisam de homologação antes de habilitar análises.

## Verificação

Testar login sem chave (401), token individual, conversa curta real com OpenAI, histórico temporário e diagnóstico da JT API. A validade da chave, crédito e liberação do modelo são confirmados apenas com resposta real. Falhas do provedor são exibidas sem expor credenciais.
