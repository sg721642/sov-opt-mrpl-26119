"""Serial best-bound B&B with exact rational conservative bounds.
No cuts, warm starts, or pseudocosts in this reference release.

safe_lower_bound may return None for models with unbounded variable directions.
In that case, the rootlb fallback is used conservatively.
"""
from dataclasses import replace
from fractions import Fraction as F
import heapq, math, time
import numpy as np
from .simplex import solve_lp
from .verify import verify,safe_lower_bound,downward_float

def exact_objective(model,x):return sum((F(float(a))*F(float(b)) for a,b in zip(model.c,x)),F(0))

def solve_milp(model,tol=1e-7,max_nodes=1000,time_limit=30.,**kwargs):
    start=time.perf_counter()
    # Root lower bound from the box: for finite bounds use the tighter bound
    def box_lb(m):
        b=F(0)
        for c,l,u in zip(m.c,m.lower,m.upper):
            c=float(c)
            if c>=0:
                if math.isfinite(l): b+=F(c)*F(l)
                # else unbounded: not contributing to a finite lower bound here
            else:
                if math.isfinite(u): b+=F(c)*F(u)
                # else unbounded: not contributing
        return b
    rootlb=box_lb(model)
    lo=model.lower.copy();hi=model.upper.copy()
    for j in model.integer:
        if math.isfinite(lo[j]):lo[j]=math.ceil(lo[j])
        if math.isfinite(hi[j]):hi[j]=math.floor(hi[j])
    if np.any(lo>hi):return dict(status='INFEASIBLE_CERTIFIED',message='An integer variable has no integer in its box',algorithm='rational-bound branch-and-bound',nodes=0)
    heap=[(rootlb,0,lo,hi)];serial=0;nodes=0;inc=None;incval=None;history=[];terminal=[];failure=None
    while heap and nodes<max_nodes and time.perf_counter()-start<time_limit:
        inherited,_,lo,hi=heapq.heappop(heap)
        if incval is not None and inherited>=incval:terminal.append(inherited);continue
        node=replace(model,lower=lo,upper=hi,integer=())
        res=solve_lp(node,tol=tol,**kwargs);nodes+=1
        if res['status']=='INFEASIBLE_CERTIFIED':continue
        if res['status']!='OPTIMAL_VERIFIED':
            heapq.heappush(heap,(inherited,serial+1,lo,hi));failure='Unresolved LP relaxation: '+res.get('message',res['status']);break
        slb=safe_lower_bound(node,res['dual'])
        bound=max(inherited, float(slb) if slb is not None else float(inherited))
        if incval is not None and bound>=incval:terminal.append(bound);continue
        x=np.array(res['x']); fractional=[j for j in model.integer if abs(x[j]-round(x[j]))>tol]
        if not fractional:
            xr=x.copy()
            for j in model.integer:xr[j]=round(xr[j])
            vr=verify(model,xr,tol=tol)
            val=exact_objective(model,xr)
            if vr['feasible'] and (incval is None or val<incval):inc=xr;incval=val
            # Close only with a checked incumbent and rational lower bound gap.
            if vr['feasible'] and float(val-bound)<=tol*(1+abs(float(val))):terminal.append(bound)
            else:
                heapq.heappush(heap,(bound,serial+1,lo,hi));failure='Near-integral node could not be closed safely';break
        else:
            j=max(fractional,key=lambda j:min(x[j]-math.floor(x[j]),math.ceil(x[j])-x[j]))
            for left in [True,False]:
                l=lo.copy();u=hi.copy()
                if left:u[j]=min(u[j],math.floor(x[j]))
                else:l[j]=max(l[j],math.ceil(x[j]))
                if l[j]<=u[j]:serial+=1;heapq.heappush(heap,(bound,serial,l,u))
        history.append(dict(nodes=nodes,open_nodes=len(heap),incumbent=None if incval is None else float(incval),node_bound=downward_float(bound)))
    lower=min([t[0] for t in heap]+terminal+([incval] if incval is not None else [rootlb]))
    result=dict(algorithm='rational-bound branch-and-bound',nodes=nodes,history=history,best_bound=downward_float(lower),bound_kind='exact rational Lagrangian bounds of binary64 input',open_nodes=len(heap))
    if inc is not None:
        gap=max(0.,float(incval-lower))/(1+abs(float(incval)));vr=verify(model,inc,tol=tol)
        result.update(x=inc.tolist(),objective=float(incval),verification=vr,relative_gap=gap)
        result['status']='OPTIMAL_VERIFIED' if not heap and not failure and gap<=tol else 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED'
        result['verification']['optimality_basis']='finite B&B tree and rational lower bounds; feasibility is numerical'
    else:result['status']='NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if heap else 'INFEASIBLE_CERTIFIED'
    if failure:result['message']=failure
    return result
