// Synthetic boundary and soak fixtures. All HTTP traffic is loopback-only.
const http = require('node:http');
const { EventEmitter } = require('node:events');
const assert = require('node:assert/strict');
const fs = require('node:fs');

async function security() {
  const doc = {id:'a-doc', tenant:'A', body:'synthetic-tenant-A-canary'};
  // Unit mock enforces the condition omitted from the actual repository path.
  const mockFind = (id, caller) => doc.id===id && doc.tenant===caller ? doc : null;
  assert.equal(mockFind('a-doc','B'), null);
  const inner = http.createServer((q,s)=>s.end('synthetic-internal-canary'));
  await new Promise(r=>inner.listen(0,'127.0.0.1',r));
  const app = http.createServer(async (q,s)=>{
    if(q.url.startsWith('/doc/')) { s.setHeader('Content-Type','application/json'); s.end(JSON.stringify(doc)); return; }
    try { const u=new URL(q.url,'http://127.0.0.1'); const result=await fetch(u.searchParams.get('url')); s.end(await result.text()); }
    catch(e) {s.statusCode=500;s.end(e.message);}
  });
  await new Promise(r=>app.listen(0,'127.0.0.1',r));
  try {
    const base=`http://127.0.0.1:${app.address().port}`;
    const bola=await fetch(base+'/doc/a-doc',{headers:{'x-synthetic-tenant':'B'}});
    const body=await bola.text();
    const ssrf=await fetch(base+'/fetch?url='+encodeURIComponent(`http://127.0.0.1:${inner.address().port}/canary`));
    return {mock_unit_assertion:'passed',cross_tenant_http_status:bola.status,cross_tenant_body:body,ssrf_http_status:ssrf.status,ssrf_body:await ssrf.text(),scope:'Toy application with deliberately omitted authorization and egress validation. No third-party traffic.'};
  } finally {app.closeAllConnections();inner.closeAllConnections();await Promise.all([new Promise(r=>app.close(r)),new Promise(r=>inner.close(r))]);}
}

function soak(){
  if(!global.gc)throw Error('run with --expose-gc');
  const emitter=new EventEmitter();
  const baseline=new Array(2_000_000).fill(0); // Stable unrelated heap, approximating an already-warm service.
  const samples=[];
  function sample(i){global.gc();samples.push({operations:i,...process.memoryUsage(),listeners:emitter.listenerCount('requestDone')});}
  sample(0);
  for(let i=1;i<=10000;i++){
    if(i>8000){const retained=Buffer.alloc(1024,1);emitter.on('requestDone',()=>retained[0]);}
    if(i%2500===0)sample(i);
  }
  assert.equal(baseline.length,2_000_000);
  const pct=100*(samples.at(-1).heapUsed-samples[0].heapUsed)/samples[0].heapUsed;
  return {samples,heap_delta_percent:pct,passes_example_five_percent_budget:pct<5,leaked_listeners:emitter.listenerCount('requestDone'),scope:'Synchronous operation loop, not a production HTTP load benchmark.'};
}

(async()=>{
  const result={node:process.version,security:await security(),soak:soak()};
  fs.writeFileSync(process.argv[2]||'scenario_results.json',JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
