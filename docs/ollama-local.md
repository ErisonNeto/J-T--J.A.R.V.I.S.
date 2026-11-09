# JARVIS local com Ollama — teste no PC da J&T

## Iniciar no pacote configurado

1. Extraia o ZIP completo para uma pasta nova. Não execute dentro do ZIP e não substitua a instalação anterior.
2. Deixe o Ollama aberto, com gemma3:1b instalado (já testado neste PC).
3. Abra INICIAR-JARVIS-LOCAL.cmd. O iniciador verifica o modelo, instala a interface com npm ci na primeira vez e abre um servidor somente no endereço local.
4. Acesse http://127.0.0.1:3001/jarvis. A chave individual está no arquivo privado ACESSO-LOCAL.txt fornecido no pacote.
5. Entre e faça uma pergunta curta. Use Testar conexões para verificar o Ollama e, se configurada, a JT API.

Para iniciar manualmente, abra PowerShell na pasta extraída e execute os comandos abaixo. Se houver uma mensagem explícita de bloqueio por política da empresa, encaminhe ao TI.

```powershell
Set-Location .\frontend
node --env-file=.env.local scripts\check-local.mjs
npm.cmd ci
npm.cmd run dev -- --hostname 127.0.0.1 --port 3001
```

Execute a instalação e a inicialização somente após sucesso da etapa anterior. Se a porta 3001 estiver ocupada, escolha outra porta e use o endereço correspondente.

## O que foi conectado

A interface Next.js chama seu próprio servidor Node, que autentica o token individual e chama o Ollama em http://127.0.0.1:11434/api/chat. AI_PROVIDER=ollama impede qualquer chamada à OpenAI, mesmo se uma chave OpenAI existir no ambiente. Não há uso de Python nem SQLAlchemy nesse fluxo. O endereço do Ollama é limitado a loopback e o iniciador da interface também escuta somente em 127.0.0.1.

O modelo recebe contexto curto (2048 tokens), no máximo duas mensagens anteriores truncadas, respostas limitadas e temperatura zero. Isso limita consumo, mas não garante precisão. O Gemma 3 1B já errou o exemplo de SLA no teste real: resultados do modelo devem ser conferidos.

O formulário Calcular SLA com quantidades informadas usa código determinístico. Os campos começam vazios. Total deve ser inteiro e positivo, e no prazo deve estar entre zero e total. Nenhum resultado manual é apresentado como dado consultado do banco.

## Limitações

- Esta é a interface local neste PC. O link no Render continua apontando para o serviço web e não acessa o localhost da empresa. Não foi criado túnel nem exposta a porta do Ollama.
- As conversas ficam temporariamente no processo Node e desaparecem ao reiniciar. Não foram migradas as memórias nem alterado o PostgreSQL.
- Memórias permanentes, pesquisas e análises automáticas dos indicadores continuam pendentes. A JT API pode ser diagnosticada, mas não é usada para fornecer números sem homologação.
- Não usar o modelo para calcular métricas, confirmar causas ou executar SQL. A futura leitura dos indicadores continuará parametrizada e somente leitura.
- O custo de API externa para o modelo local é zero; permanecem consumo de energia, memória e processamento do computador.

## Validação realizada

Build Next.js e TypeScript, testes de proxy/autenticação, transporte Ollama, ausência de recurso automático à API paga e cálculo determinístico. O fluxo HTTP integrado é testado com provedor local simulado, isolado. O teste final com Gemma e com as políticas do Windows deve ser feito no computador da J&T.
