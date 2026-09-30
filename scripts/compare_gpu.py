"""Hardware gate: same model, same tolerance, repeated end-to-end timings.
No CUDA device means a failure, not a fake CPU fallback.
"""
import argparse,json,statistics,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sovopt import load,solve
p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('--output',default='reports/gpu_comparison.json');a=p.parse_args()
import cupy as cp
m=load(a.model);runs=[]
# Include one cold CUDA result separately; warm repeated runs include transfers and verification.
for backend in ['pdhg-cpu','pdhg-cuda']:
    for repeat in range(6):
        r=solve(m,backend=backend);r.update(repeat=repeat,cold=repeat==0);runs.append(r)
valid=all(r['status']=='OPTIMAL_VERIFIED' for r in runs)
median=lambda b:statistics.median(r['elapsed_seconds'] for r in runs if r['backend']==b and not r['cold'])
record=dict(model_sha256=m.fingerprint(),cupy_version=cp.__version__,device=str(cp.cuda.runtime.getDeviceProperties(0)['name']),accuracy_gate_passed=valid,speedup_cpu_pdhg_over_cuda=median('pdhg-cpu')/median('pdhg-cuda') if valid else None,runs=runs)
Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(record,indent=2)+'\n');print(a.output)
