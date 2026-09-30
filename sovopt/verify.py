"""Checks original model independently of solver stopping rules.
KKT checks are numerical, NOT formal interval/exact optimality certificates.
Exact rational LP lower bounds and Farkas checks use the input float values exactly.

Objective recovery: for maximize problems, c is stored negated internally. The
reported objective is the original-sense value: -(c^T x) + obj_offset for MAX,
or c^T x + obj_offset for MIN.
"""
from fractions import Fraction as F
import numpy as np

def _reported_objective(model, x, Q=None):
    """Compute the objective in the original problem sense (before internal negation)."""
    xld = np.asarray(x, np.longdouble)
    cld = model.c.astype(np.longdouble)
    if Q is None:
        Q_use = np.zeros((len(x), len(x)))
    else:
        Q_use = Q
    raw = float(cld @ xld + xld @ Q_use.astype(np.longdouble) @ xld / 2)
    if model.maximize:
        return -raw + model.obj_offset   # negate back to original maximization sense
    return raw + model.obj_offset

def verify(model,x,z=None,tol=1e-7,check_integer=True):
    x=np.asarray(x,np.longdouble); G,h,_=model.inequalities(); G=G.astype(np.longdouble); h=h.astype(np.longdouble)
    if x.shape!=model.c.shape or not np.isfinite(x).all():return {'feasible':False,'kkt_passed':False,'reason':'nonfinite or invalid candidate'}
    # Verify variable bounds explicitly (including infinite ones)
    lb_viol = np.maximum(model.lower - np.asarray(x,float), 0)
    ub_viol = np.maximum(np.asarray(x,float) - model.upper, 0)
    box_viol = float(max(lb_viol.max() if len(lb_viol) else 0, ub_viol.max() if len(ub_viol) else 0))
    activity=G@x; violation=np.maximum(activity-h,0)
    scale=1+np.abs(h)+np.abs(G)@np.abs(x)
    primal=float(np.max(violation/scale,initial=0)); absolute=float(np.max(violation,initial=0))
    primal=max(primal, box_viol / (1 + np.max(np.abs(model.upper[np.isfinite(model.upper)]), initial=1)))
    absolute=max(absolute, box_viol)
    integ=float(max((abs(x[j]-np.rint(x[j])) for j in model.integer),default=0))
    Q_arr=np.zeros((len(x),len(x))) if model.Q is None else model.Q
    grad=Q_arr.astype(np.longdouble)@x+model.c  # grad in internal (minimization) space
    obj=_reported_objective(model, x, Q_arr)
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
    """Exact rational Lagrangian lower bound over variable box, LP only.
    G contains ALL constraints; double-counting box constraints is valid here.
    Every nonneg z is dual admissible for this box-minimization bound.
    Returns None if any coefficient direction is unbounded (infinite variable bound
    with wrong-sign reduced cost), making the bound uninformative.
    """
    G,h,_=model.inequalities(); z=[F(float(max(0,v))) for v in z]
    r=[F(float(v)) for v in model.c]; b=F(0)
    for i in range(len(h)):
        b-=F(float(h[i]))*z[i]
        for j in np.flatnonzero(G[i]):r[j]+=F(float(G[i,j]))*z[i]
    for j,v in enumerate(r):
        if v>=0:
            if np.isneginf(model.lower[j]): return None  # unbounded below with positive coeff
            b+=v*F(float(model.lower[j]))
        else:
            if np.isposinf(model.upper[j]): return None  # unbounded above with negative coeff
            b+=v*F(float(model.upper[j]))
    return b

def downward_float(value):
    if value is None: return None
    f=float(value)
    if F(f)>value:f=float(np.nextafter(f,-np.inf))
    return f

def exact_farkas(model,z):
    G,h,_=model.inequalities(); z=[F(float(v)) for v in z]
    if any(v<0 for v in z):return False
    for j in range(len(model.c)):
        if sum((F(float(G[i,j]))*z[i] for i in range(len(h))),F(0))!=0:return False
    return sum((F(float(h[i]))*z[i] for i in range(len(h))),F(0))<0
