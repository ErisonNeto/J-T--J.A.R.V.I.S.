const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const ts = require('../frontend/node_modules/typescript');
const Module = require('node:module');
function compile(file) {
  const source = fs.readFileSync(path.join(__dirname,file),'utf8');
  const result = new Module(path.join(__dirname,'local-test-'+path.basename(file)+'.cjs'),module);
  result.filename = path.join(__dirname,'local-test-'+path.basename(file)+'.cjs'); result.paths=module.paths;
  result._compile(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,result.filename);
  return result.exports;
}
const {webPreview} = compile('../frontend/lib/web-preview.ts');
const {slaPercentage} = compile('../frontend/lib/metrics.ts');
process.env.AI_PROVIDER='ollama';
process.env.OLLAMA_MODEL='gemma3:1b';
process.env.OLLAMA_BASE_URL='http://127.0.0.1:11434';
process.env.JARVIS_WEB_ACCESS_TOKEN='local-test-'.repeat(5);
process.env.OPENAI_API_KEY='must-never-be-sent';
delete process.env.JT_API_KEY;
const req=(body)=>new Request('http://127.0.0.1:3001/api/jarvis/chat',{method:body?'POST':'GET',headers:{Authorization:'Bearer '+process.env.JARVIS_WEB_ACCESS_TOKEN},...(body?{body:JSON.stringify(body)}:{})});
(async()=>{
  assert.equal(slaPercentage(900,1000),90);
  assert.equal(slaPercentage(0,1000),0);
  assert.equal(slaPercentage(1000,1000),100);
  for(const pair of [[10,0],[-1,10],[11,10],[1.5,10],[NaN,10],[Infinity,10]]) assert.throws(()=>slaPercentage(...pair));
  const status=await (await webPreview(req(),'status')).json();assert.equal(status.provider,'ollama');assert.equal(status.model_name,'gemma3:1b');
  let calls=0;
  global.fetch=async(url,options)=>{
    calls++;
    assert.equal(url,'http://127.0.0.1:11434/api/chat');
    assert.equal(options.headers.Authorization,undefined);
    const payload=JSON.parse(options.body);assert.equal(payload.model,'gemma3:1b');assert.equal(payload.stream,false);assert.equal(payload.options.num_ctx,2048);
    assert.equal(JSON.stringify(payload).includes('must-never-be-sent'),false);
    return Response.json({done:true,done_reason:'stop',message:{role:'assistant',content:'Resposta local de teste.'}});
  };
  const response=await webPreview(req({message:'Ola'}),'chat');assert.equal(response.status,200);const first=await response.json();assert.equal(first.answer,'Resposta local de teste.');
  const convo=await (await webPreview(req(),'conversations/'+first.conversation_id)).json();assert.equal(convo.length,2);
  process.env.OLLAMA_BASE_URL='https://external.example.test';
  const failed=await webPreview(req({message:'Nao enviar'}),'chat');assert.equal(failed.status,503);assert.equal(calls,1);
  process.env.OLLAMA_BASE_URL='http://127.0.0.1:11434';
  global.fetch=async(url)=>{assert.equal(url,'http://127.0.0.1:11434/api/chat');return Response.json({}, {status:404});};
  assert.equal((await webPreview(req({message:'Modelo ausente'}),'chat')).status,502);
  global.fetch=async()=>{throw new Error('offline');};
  assert.equal((await webPreview(req({message:'Offline'}),'chat')).status,503);
  assert.equal((await webPreview(req({message:'x'.repeat(2001)}),'chat')).status,422);
  console.log('PASS Ollama: loopback only, correct endpoint, no provider secrets, no paid fallback, unavailable model, outage, bounded input, deterministic SLA');
})().catch(e=>{console.error(e);process.exitCode=1;});
