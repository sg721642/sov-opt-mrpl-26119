"""Reproducible demo suite, not a Netlib/MIPLIB/QPLIB benchmark claim."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from sovopt import solve,load
p=argparse.ArgumentParser();p.add_argument('--external-python');p.add_argument('--repeats',type=int,default=3);a=p.parse_args()
if not 1<=a.repeats<=20:raise SystemExit('repeats must be 1..20')
records=[]
for path in sorted((ROOT/'examples').glob('*.json')):
    for scaling in [True,False]:
        for repeat in range(a.repeats):
            r=solve(load(path),scaling=scaling);r.update(file=path.name,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scaling=scaling,repeat=repeat)
            records.append(r)
    if a.external_python and 'qp' not in path.stem:
        run=subprocess.run([a.external_python,str(ROOT/'scripts/baseline_worker.py'),str(path)],capture_output=True,text=True,timeout=40)
        if run.returncode:records.append(dict(file=path.name,backend='external',error=run.stderr))
        else:records.append(dict(file=path.name,**json.loads(run.stdout)))
out=ROOT/'reports/benchmark.json';out.write_text(json.dumps(dict(scope='synthetic examples only',platform=platform.platform(),records=records),indent=2,allow_nan=False)+'\n');print(out)
