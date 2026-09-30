"""EXTERNAL BENCHMARK ONLY. Never imported by sovopt.
Run in a separate interpreter/process. SciPy's HiGHS is the external LP/MILP baseline.
"""
import sys,json,time
import numpy as np
from scipy.optimize import linprog,milp,Bounds,LinearConstraint
from pathlib import Path
start=time.perf_counter();d=json.loads(Path(sys.argv[1]).read_text());A=np.array(d.get('A',[]));c=np.array(d['c'])
if d.get('Q') is not None:raise SystemExit('This baseline adapter supports LP/MILP only')
l=np.array([-np.inf if v is None else v for v in d.get('row_lower',[-np.inf]*len(A))]);u=np.array([np.inf if v is None else v for v in d.get('row_upper',[np.inf]*len(A))])
if d.get('integer'):
    integrality=np.zeros(len(c));integrality[d['integer']]=1
    r=milp(c,integrality=integrality,bounds=Bounds(d['lower'],d['upper']),constraints=LinearConstraint(A,l,u),options={'time_limit':30})
else:
    G=[];h=[]
    for a,lo,hi in zip(A,l,u):
        if np.isfinite(hi):G.append(a);h.append(hi)
        if np.isfinite(lo):G.append(-a);h.append(-lo)
    r=linprog(c,A_ub=G or None,b_ub=h or None,bounds=list(zip(d['lower'],d['upper'])),method='highs')
print(json.dumps(dict(backend='external SciPy/HiGHS process',success=bool(r.success),objective=None if r.fun is None else float(r.fun),seconds=time.perf_counter()-start,message=r.message)))
