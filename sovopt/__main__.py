import argparse,json,sys
from pathlib import Path
from . import load,solve

def main():
    p=argparse.ArgumentParser(description='SOV-OPT finite-box research prototype')
    p.add_argument('model');p.add_argument('--backend',choices=['cpu','pdhg-cpu','pdhg-cuda'],default='cpu');p.add_argument('--tol',type=float,default=1e-7);p.add_argument('--output');p.add_argument('--no-scaling',action='store_true')
    a=p.parse_args()
    try:r=solve(load(a.model),backend=a.backend,tol=a.tol,scaling=not a.no_scaling)
    except (ValueError,KeyError,OSError) as e:r={'status':'INVALID_MODEL','message':str(e)}
    out=json.dumps(r,indent=2,allow_nan=False)
    if a.output:Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(out+'\n')
    print(out);return 0 if r['status'] in ('OPTIMAL_VERIFIED','INFEASIBLE_CERTIFIED') else 2
if __name__=='__main__':sys.exit(main())
