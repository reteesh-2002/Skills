#!/usr/bin/env python3
"""Local fault injections into disposable copies; never publishes or contacts a service."""
import concurrent.futures, hashlib, json, os, platform, shutil, signal
import subprocess as sp, sys, tempfile, time
from pathlib import Path

SRC=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).parent/'source'
OUT=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else Path(__file__).parent/'rerun'
OUT.mkdir(parents=True,exist_ok=True)
RESULTS=[]
ENV=dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
for k in ['GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','BASH_ENV','ENV','SHELLOPTS']:
    ENV.pop(k,None)

def run(argv,cwd,**kw):
    p=sp.run(list(map(str,argv)),cwd=cwd,env=kw.pop('env',ENV),text=True,capture_output=True,timeout=15,**kw)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def repo(root,name):
    p=root/name;p.mkdir()
    for d in ['scripts','tests','.agents','adaptive-worker-orchestrator-v2/scripts']:
        shutil.copytree(SRC/d,p/d,dirs_exist_ok=True)
    for f in p.rglob('*.sh'): f.chmod(0o755)
    (p/'.gitignore').write_text('.evidence/\n')
    (p/'app.py').write_text('value = 1\n')
    for a in [['git','init','-q','-b','main'],['git','config','user.name','Audit'],['git','config','user.email','audit@example.invalid'],['git','add','.'],['git','commit','-qm','fixture']]:
        assert run(a,p)['exit']==0
    return p

def proxy(p,label,*argv,**kw):return run(['bash',p/'scripts/exec-proxy.sh','--label',label,*argv],p,**kw)
def gate(p,*args,cwd=None):return run(['bash',p/'scripts/verify-release-gate.sh',*args],cwd or p)
def manifest(p):return json.loads((p/'.evidence/manifest.v1.json').read_text())
def write_manifest(p,m):
    (p/'.evidence').mkdir(exist_ok=True)
    (p/'.evidence/manifest.v1.json').write_text(json.dumps(m))
def add(id,observation,**data):RESULTS.append(dict(id=id,observation=observation,**data))

with tempfile.TemporaryDirectory(prefix='agy-audit-') as t:
    root=Path(t)
    p=repo(root,'bundled'); a=run(['bash','tests/verify_runtime.sh'],p)
    add('P00','Bundled conformance suite',result=a)

    p=repo(root,'zero');a=proxy(p,'unit','true')
    add('P01','Zero tests accepted',proxy=a,gate=gate(p),manifest=manifest(p))

    p=repo(root,'unstaged');proxy(p,'unit','python3','-c',"print('1 passed in 0.01s')")
    (p/'app.py').write_text('raise RuntimeError("untested change")\n')
    (p/'untracked.py').write_text('also_untested = True\n')
    add('P02','Unstaged and untracked changes accepted',status=run(['git','status','--porcelain'],p),gate=gate(p))
    run(['git','add','app.py','untracked.py'],p)
    add('P03','Staged change correctly rejected',gate=gate(p))
    proxy(p,'lint','true')
    add('P04','New cheap check refreshes top-level tree; old unit receipt survives',gate=gate(p),manifest=manifest(p))

    p=repo(root,'forged')
    sha=run(['git','write-tree'],p)['stdout'].strip()
    forged={'schema_version':'manifest.v1','git_tree_sha':sha,'policy_disposition':'GREEN','checks':[{'command':'never executed','exit_code':0,'metrics':{'collected':1,'passed':1,'failed':0}}],'open_waivers':[]}
    write_manifest(p,forged)
    add('P05','Handwritten receipt-free/log-free manifest accepted',gate=gate(p))
    forged['git_tree_sha']='unknown';write_manifest(p,forged)
    add('P06','Literal unknown tree disables comparison',gate=gate(p))
    forged['git_tree_sha']=sha;forged['policy_disposition']='BANANA';write_manifest(p,forged)
    add('P07','Invalid disposition accepted',gate=gate(p))
    forged['policy_disposition']='AMBER';forged['open_waivers']=['self-approved'];write_manifest(p,forged)
    add('P08','Unauthenticated waiver accepted',gate=gate(p))
    forged['policy_disposition']='GREEN';write_manifest(p,forged)
    add('P09','Git failure outside repository accepted',gate=gate(p,cwd=root))

    p=repo(root,'nested');a=proxy(p,'unit','bash','-c','false | cat')
    add('P10','Nested shell pipeline masks failure',proxy=a,gate=gate(p))
    p=repo(root,'spoof');a=proxy(p,'unit','python3','-c',"print('999 passed in 0.01s')")
    add('P11','Printed text accepted as test metrics',proxy=a,gate=gate(p),manifest=manifest(p))

    p=repo(root,'retry');a=proxy(p,'unit','bash','-c','exit 1');b=proxy(p,'unit','python3','-c',"print('1 passed in 0.01s')")
    add('P12','Same-label retry erases active failure',first=a,second=b,gate=gate(p),manifest=manifest(p),receipt_count=len(list((p/'.evidence/receipts').glob('*.json'))))
    p=repo(root,'warnings');proxy(p,'unit','python3','-c',"print('DeprecationWarning: unsafe old API'); print('1 passed in 0.01s')")
    add('P13','Warning is not reflected in disposition',gate=gate(p),manifest=manifest(p))

    p=repo(root,'sink');binpath=p/'fakebin';binpath.mkdir()
    (binpath/'tee').write_text('#!/bin/bash\ncat >/dev/null\necho "injected tee sink failure" >&2\nexit 23\n');(binpath/'tee').chmod(0o755)
    a=proxy(p,'unit','python3','-c',"print('1 passed')",env=dict(ENV,PATH=str(binpath)+':'+ENV['PATH']))
    add('P14','Log sink process failure ignored',proxy=a,gate=gate(p),logs=list(map(str,(p/'.evidence/logs').glob('*'))))

    p=repo(root,'hooks')
    payload=json.dumps({'toolCall':{'name':'run_command','args':{'CommandLine':'git push','Cwd':str(p)}}})
    stub=run(['bash',p/'.agents/scripts/verify-release-gate.sh'],p,input=payload)
    registered=run(['bash',p/'scripts/verify-release-gate.sh','--pre-tool'],p,input=payload)
    alias=gate(p,'--pre-tool','git -C . push')
    add('P15','Hook stub allows; registered hook ignores stdin and emits non-JSON; regex misses git options',stub=stub,registered=registered,variant=alias)

    p=repo(root,'node');(p/'t.cjs').write_text("const test=require('node:test'); const assert=require('node:assert/strict'); test('real assertion',()=>assert.equal(1,1));\n")
    a=proxy(p,'unit','node','--test','--test-reporter=spec','t.cjs')
    add('P16','Real Node spec report parsing',proxy=a,gate=gate(p),manifest=manifest(p))

    p=repo(root,'signal');proxy(p,'unit','python3','-c',"print('1 passed')")
    before=(p/'.evidence/manifest.v1.json').read_bytes()
    log=OUT/'signal-process.log'
    with log.open('w') as f:
        proc=sp.Popen(['bash',str(p/'scripts/exec-proxy.sh'),'--label','unit','python3','-c','import time; print("started", flush=True); time.sleep(10)'],cwd=p,env=ENV,stdout=f,stderr=sp.STDOUT,start_new_session=True)
        deadline=time.monotonic()+3
        while 'started' not in log.read_text() and time.monotonic()<deadline:time.sleep(.02)
        os.killpg(proc.pid,signal.SIGTERM);rc=proc.wait(timeout=3)
    add('P17','Interrupted rerun leaves prior GREEN available',exit=rc,manifest_unchanged=before==(p/'.evidence/manifest.v1.json').read_bytes(),gate=gate(p),signal_log=log.read_text())

    concurrent_runs=[]
    for round in range(4):
        p=repo(root,'parallel'+str(round))
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            rr=list(pool.map(lambda i:proxy(p,'check'+str(i),'true'),range(6)))
        try:m=manifest(p);n=len(m['checks']);err=None
        except Exception as e:n=None;err=str(e)
        concurrent_runs.append({'submitted':6,'proxy_exits':[v['exit'] for v in rr],'retained':n,'error':err})
    add('P18','Concurrent manifest updates',rounds=concurrent_runs)

    p=repo(root,'cleanup');script=p/'adaptive-worker-orchestrator-v2/scripts/setup_worktrees.sh'
    setup=run(['bash',script,'main','alice'],p)
    wt=p/'.git/.orch-worktrees/alice';(wt/'unsaved.txt').write_text('unique work not committed\n');(wt/'app.py').write_text('unique uncommitted tracked work\n')
    clean=run(['bash',script,'cleanup'],p)
    add('P19','Cleanup force-removes uncommitted worker data',setup=setup,cleanup=clean,worktree_exists=wt.exists(),branches=run(['git','branch','--list','orch/*'],p))

    p=repo(root,'symlink');(p/'outside').mkdir();(p/'outside/bypass').symlink_to('../app.py')
    audit=p/'adaptive-worker-orchestrator-v2/scripts/audit_diff.sh'
    add('P20','Out-of-scope symlink skipped',audit=run(['bash',audit,p,'main','src/'],p))
    (p/'outside/bypass').unlink();(p/'src-evil').mkdir();(p/'src-evil/bad.py').write_text('x=1\n')
    add('P21','Prefix scope accepts sibling path',audit=run(['bash',audit,p,'main','src'],p))
    (p/'src-evil/bad.py').unlink();(p/'src').mkdir();(p/'src/new.py').write_text('# TODO placeholder\n')
    add('P22','Untracked placeholder content uninspected',audit=run(['bash',audit,p,'main','src/'],p,env=dict(ENV,FAIL_ON_PLACEHOLDERS='1')))

versions={k:run(cmd,OUT)['stdout'].splitlines()[0] for k,cmd in [('git',['git','--version']),('bash',['bash','--version']),('node',['node','--version'])]}
versions['python']=platform.python_version()
payload={'scope':'Isolated Linux shell/Git fixtures. Not an installed AGY session or production application. Synthetic parser strings are identified explicitly.','versions':versions,'results':RESULTS}
(OUT/'probe_results.json').write_text(json.dumps(payload,indent=2))
shutil.copy2(__file__,OUT/'audit_probes.py')
for item in RESULTS:
    print(item['id'],item['observation'],json.dumps({k:v for k,v in item.items() if k in ['gate','audit','rounds','exit','manifest_unchanged','worktree_exists']},ensure_ascii=False))
