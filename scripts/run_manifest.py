"""Run every frozen instance, preserving unsupported models and timeouts."""
import argparse,hashlib,json,subprocess,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--timeout',type=float,default=40);p.add_argument('--output',default='reports/manifest_results.json');a=p.parse_args();mf=Path(a.manifest).resolve();data=json.loads(mf.read_text());results=[]
for item in data['instances']:
    path=(mf.parent/item['path']).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Changed model: '+str(path))
    try:
        run=subprocess.run([sys.executable,'-m','sovopt',str(path)],cwd=ROOT,capture_output=True,text=True,timeout=a.timeout,env=dict(os.environ,OPENBLAS_NUM_THREADS='1'))
        try:r=json.loads(run.stdout)
        except ValueError:r={'status':'WORKER_ERROR','message':run.stderr[-1000:]}
    except subprocess.TimeoutExpired:r={'status':'LIMIT_REACHED','message':'External wall-clock timeout'}
    results.append(dict(instance=item,result=r))
Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(results,indent=2)+'\n');print(a.output)
