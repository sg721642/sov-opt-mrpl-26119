"""Original two-phase primal revised simplex, Bland pricing, full LU refactorization.
This is a dense reference implementation, not the roadmap's sparse dual simplex.
"""
import numpy as np
from fractions import Fraction
from math import lcm
from .linalg import LU, NumericalError
from .verify import verify, exact_farkas

def _iterate(M,b,c,basis,allowed,limit,history):
    for k in range(limit):
        B=M[:,basis]; lu=LU(B); xb=lu.solve(b); y=LU(B.T).solve(c[basis]); rc=c-M.T@y
        if np.min(xb,initial=0)<-1e-7*(1+np.max(abs(b),initial=0)):raise NumericalError('Lost basis feasibility')
        entering=next((j for j in range(allowed) if j not in basis and rc[j]<-1e-10*(1+abs(c[j]))),None)
        if entering is None:return xb,y,k
        d=lu.solve(M[:,entering]); possible=np.flatnonzero(d>1e-12)
        if not len(possible):raise NumericalError('Unbounded direction in finite-box problem')
        ratios=np.maximum(xb[possible],0)/d[possible]; best=np.min(ratios)
        ties=[int(possible[t]) for t,v in enumerate(ratios) if v<=best+1e-12*(1+abs(best))]
        leaving=min(ties,key=lambda i:basis[i])
        if len(history)<1000:history.append({'iteration':len(history),'objective_transformed':float(c[basis]@np.maximum(xb,0))})
        basis[leaving]=entering
    raise NumericalError('Simplex iteration limit')

def solve_lp(model,tol=1e-7,max_iter=10000,scaling=True):
    G,h,_=model.inequalities(); n=len(model.c); m=len(h); history=[]
    scale=np.maximum(np.max(abs(G),axis=1),1e-30) if scaling else np.ones(m)
    D=G/scale[:,None]; b=(h-G@model.lower)/scale
    signs=np.where(b<0,-1.,1.); D*=signs[:,None]; b*=signs
    neg=np.flatnonzero(signs<0); M=np.column_stack([D,np.diag(signs),np.eye(m)[:,neg]])
    basis=[n+i if signs[i]>0 else n+m+int(np.flatnonzero(neg==i)[0]) for i in range(m)]
    phase=np.zeros(M.shape[1]); phase[n+m:]=1
    try:
        xb,y,it=_iterate(M,b,phase,basis,M.shape[1],max_iter,history)
        if phase[basis]@xb>1e-8:
            z=-y*signs/scale
            r=G.T@z
            for j in range(n):z[m-2*n+2*j+1]+=r[j]
            cert=exact_farkas(model,z)
            if not cert:
                # Rational reconstruction is only a candidate; exact check decides.
                q=[Fraction(float(v)).limit_denominator(1000000) for v in z]
                den=lcm(*(v.denominator for v in q))
                if den.bit_length()<45:
                    candidate=np.array([float(v*den) for v in q])
                    if exact_farkas(model,candidate):z=candidate;cert=True
            return dict(status='INFEASIBLE_CERTIFIED' if cert else 'NUMERICAL_FAILURE',message='Phase I infeasibility; exact binary-rational certificate '+('passed' if cert else 'could not be established'),certificate=z.tolist(),algorithm='two-phase primal revised simplex',iterations=it,history=history)
        # Remove zero-valued artificial variables from the basis.
        for i in range(m):
            if basis[i]>=n+m:
                row=LU(M[:,basis].T).solve(np.eye(m)[i])@M[:,:n+m]
                j=next((j for j in range(n+m) if j not in basis and abs(row[j])>1e-10),None)
                if j is None:raise NumericalError('Unable to remove artificial basis variable')
                basis[i]=j
        cost=np.r_[model.c,np.zeros(m+len(neg))]
        xb,y,it2=_iterate(M,b,cost,basis,n+m,max_iter,history)
        t=np.zeros(M.shape[1]);t[basis]=xb; x=model.lower+t[:n]
        z=-y*signs/scale
        reduced=model.c+G.T@z
        for j in range(n):z[m-2*n+2*j+1]+=reduced[j]
        report=verify(model,x,z,tol,check_integer=False)
        return dict(status='OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',x=x.tolist(),dual=z.tolist(),verification=report,objective=report['objective'],iterations=it+it2,algorithm='two-phase primal revised simplex',history=history)
    except (NumericalError,FloatingPointError,OverflowError) as e:
        return dict(status='NUMERICAL_FAILURE',message=str(e),algorithm='two-phase primal revised simplex',history=history)
