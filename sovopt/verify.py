"""Checks original model independently of solver stopping rules.
KKT checks are numerical, NOT formal interval/exact optimality certificates.
Exact rational LP lower bounds and Farkas checks use the input float values exactly.
"""
from fractions import Fraction as F
import numpy as np

def verify(model,x,z=None,tol=1e-7,check_integer=True):
    x=np.asarray(x,np.longdouble); G,h,_=model.inequalities(); G=G.astype(np.longdouble); h=h.astype(np.longdouble)
    if x.shape!=model.c.shape or not np.isfinite(x).all():return {'feasible':False,'kkt_passed':False,'reason':'nonfinite or invalid candidate'}
    activity=G@x; violation=np.maximum(activity-h,0)
    scale=1+np.abs(h)+np.abs(G)@np.abs(x)
    primal=float(np.max(violation/scale,initial=0)); absolute=float(np.max(violation,initial=0))
    integ=float(max((abs(x[j]-np.rint(x[j])) for j in model.integer),default=0))
    Q=np.zeros((len(x),len(x))) if model.Q is None else model.Q
    grad=Q.astype(np.longdouble)@x+model.c
    obj=float(model.c.astype(np.longdouble)@x+x@(Q.astype(np.longdouble)@x)/2)
    report=dict(feasible=primal<=tol and (not check_integer or integ<=tol),objective=obj,primal_residual=primal,absolute_primal_violation=absolute,integrality_residual=integ,kkt_passed=False,precision_bits=int(np.finfo(np.longdouble).nmant+1),certification='floating-point residual checks')
    if z is not None:
        z=np.asarray(z,np.longdouble)
        if z.shape!=h.shape or not np.isfinite(z).all():return report
        dual=float(np.max(np.maximum(-z,0),initial=0)); station=float(np.max(abs(grad+G.T@z)/(1+abs(grad)+abs(G.T)@abs(z)),initial=0))
        comp=float(np.max(abs(z*(activity-h))/(1+abs(obj)+abs(z*h)),initial=0))
        gap=float(abs(z@(h-activity))/(1+abs(obj)))
        report.update(dual_residual=station,dual_sign_violation=dual,complementarity=comp,relative_duality_gap=gap,kkt_passed=report['feasible'] and max(dual,station,comp,gap)<=tol)
    return report

def safe_lower_bound(model,z):
    """Exact rational Lagrangian lower bound over finite variable box, LP only.
    G contains ALL constraints; double-counting box constraints is valid here.
    Every nonnegative z is dual admissible for this box-minimization bound.
    """
    G,h,_=model.inequalities(); z=[F(float(max(0,v))) for v in z]
    r=[F(float(v)) for v in model.c]; b=F(0)
    for i in range(len(h)):
        b-=F(float(h[i]))*z[i]
        for j in np.flatnonzero(G[i]):r[j]+=F(float(G[i,j]))*z[i]
    for j,v in enumerate(r):b+=v*F(float(model.lower[j] if v>=0 else model.upper[j]))
    return b

def downward_float(value):
    f=float(value)
    if F(f)>value:f=float(np.nextafter(f,-np.inf))
    return f

def exact_farkas(model,z):
    G,h,_=model.inequalities(); z=[F(float(v)) for v in z]
    if any(v<0 for v in z):return False
    for j in range(len(model.c)):
        if sum((F(float(G[i,j]))*z[i] for i in range(len(h))),F(0))!=0:return False
    return sum((F(float(h[i]))*z[i] for i in range(len(h))),F(0))<0
