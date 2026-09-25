"""Local counterexamples; not an AGY integration test or framework benchmark."""
import json, subprocess, platform, pathlib, hashlib

ROOT = pathlib.Path(__file__).resolve().parent
P = ROOT / 'probes'
P.mkdir(exist_ok=True)
results = []

def probe(name, argv, expected, source=None):
    if source:
        (P / source[0]).write_text(source[1])
    p = subprocess.run(argv, cwd=P, capture_output=True, text=True, timeout=15)
    (P / (name + '.log')).write_text(p.stdout + '\nSTDERR:\n' + p.stderr)
    results.append({'id': name, 'argv': argv, 'exit_code': p.returncode,
                    'expected_exit': expected, 'matched': p.returncode == expected,
                    'output': p.stdout.strip(), 'stderr': p.stderr.strip()})

probe('unawaited_pending', ['node', '--test', 'pending.cjs'], 0,
 ('pending.cjs', "const {test}=require('node:test');\nconst assert=require('node:assert/strict');\ntest('purports to verify async work',()=>{\n new Promise(()=>{}).then(()=>assert.equal(1,2));\n});\n"))
probe('awaited_pending', ['node', '--test', 'awaited.cjs'], 1,
 ('awaited.cjs', "const {test}=require('node:test');\nconst assert=require('node:assert/strict');\ntest('actually awaits work',{timeout:100},async()=>{\n await new Promise(()=>{});\n assert.equal(1,2);\n});\n"))
probe('mock_masks_production', ['node', '--test', 'mock.cjs'], 0,
 ('mock.cjs', "const {test}=require('node:test');\nconst assert=require('node:assert/strict');\nfunction productionLookup(){throw new Error('real database unavailable')}\nfunction service(lookup=productionLookup){return lookup()}\ntest('mock-only boundary',()=>assert.equal(service(()=>42),42));\n"))
probe('unmocked_boundary', ['node', '--test', 'real.cjs'], 1,
 ('real.cjs', "const {test}=require('node:test');\nfunction productionLookup(){throw new Error('real database unavailable')}\nfunction service(lookup=productionLookup){return lookup()}\ntest('unmocked boundary',()=>service());\n"))
probe('masked_pipeline', ['bash','-c', 'false | tee pipeline.log'], 0)
probe('pipefail_pipeline', ['bash','-o','pipefail','-c','false | tee pipefail.log'], 1)
probe('wrapped_exit_256', ['bash','-c','exit 256'], 0)
probe('ignored_sink_failure', ['bash','-c','printf evidence > /dev/full; true'], 0)
probe('checked_sink_failure', ['bash','-c','printf evidence > /dev/full'], 1)

versions = {}
for name, argv in {'node':['node','--version'], 'bash':['bash','--version'], 'git':['git','--version']}.items():
    versions[name]=subprocess.check_output(argv,text=True).splitlines()[0]
out={'scope':'Local probes only; no Antigravity runtime or full suite exercised',
     'versions':versions,'python':platform.python_version(),'results':results}
(ROOT/'probe_results.json').write_text(json.dumps(out,indent=2))
for x in results:
    print(f"{x['id']}: exit={x['exit_code']}, expected={x['expected_exit']}, matched={x['matched']}")
print(json.dumps(versions))
assert all(x['matched'] for x in results)
