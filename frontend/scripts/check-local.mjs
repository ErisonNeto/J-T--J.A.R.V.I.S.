const root = new URL(process.env.OLLAMA_BASE_URL || 'http://127.0.0.1:11434');
const model = process.env.OLLAMA_MODEL || 'gemma3:1b';
try {
  if (process.env.AI_PROVIDER !== 'ollama') throw new Error('AI_PROVIDER precisa ser ollama neste pacote local.');
  if (root.protocol !== 'http:' || !['127.0.0.1','localhost','[::1]'].includes(root.hostname) || root.username || root.password || root.search || root.hash || root.pathname !== '/') throw new Error('Configure OLLAMA_BASE_URL com endereco HTTP local, sem caminho.');
  if ((process.env.JARVIS_WEB_ACCESS_TOKEN || '').length < 32) throw new Error('Chave de acesso local ausente.');
  const response = await fetch(root.origin + '/api/tags', {signal: AbortSignal.timeout(10000),redirect:'error'});
  if (!response.ok) throw new Error('Ollama retornou HTTP ' + response.status);
  const data = await response.json();
  if (!data.models?.some(m => m.name === model || m.model === model)) throw new Error('Modelo nao instalado. Execute: ollama run ' + model);
  console.log('Ollama conectado. Modelo: ' + model + '. Nenhuma API paga sera chamada.');
} catch (error) {
  console.error('Nao foi possivel iniciar o JARVIS local: ' + error.message);
  console.error('Abra o Ollama neste computador e tente novamente.');
  process.exitCode = 1;
}
