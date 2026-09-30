"""Infeasible-start primal-dual Mehrotra predictor-corrector for convex QP."""
import numpy as np
from .linalg import LU,NumericalError
from .verify import verify

def step(v,d,fraction=1.):
    mask=d<0
    return min(1.,fraction*float(np.min(-v[mask]/d[mask]))) if mask.any() else 1.

def solve_qp(model,tol=1e-7,max_iter=150,scaling=True):
    G0,h0,_=model.inequalities(); n=len(model.c); m=len(h0)
    scale=np.maximum(np.max(abs(G0),axis=1),1e-30) if scaling else np.ones(m)
    G=G0/scale[:,None];h=h0/scale;Q=model.Q
    x=(model.lower+model.upper)/2; s=np.maximum(1.,h-G@x);z=np.ones(m);history=[]
    try:
        for k in range(max_iter):
            report=verify(model,x,z/scale,tol)
            if report['kkt_passed']:return dict(status='OPTIMAL_VERIFIED',algorithm='primal-dual predictor-corrector QP',x=x.tolist(),dual=(z/scale).tolist(),objective=report['objective'],verification=report,iterations=k,history=history)
            rd=Q@x+model.c+G.T@z;rp=G@x+s-h;mu=float(s@z/m)
            history.append(dict(iteration=k,primal_residual=report['primal_residual'],dual_residual=report['dual_residual'],complementarity=mu))
            K=Q+G.T@((z/s)[:,None]*G)
            # Regularization stabilizes Newton directions; final acceptance remains unregularized.
            reg=1e-11*max(1.,float(np.max(abs(np.diag(K)))))
            lu=LU(K+reg*np.eye(n))
            def direction(rc):
                dx=lu.solve(-rd+G.T@((rc-z*rp)/s));ds=-rp-G@dx;dz=(-rc-z*ds)/s
                return dx,ds,dz
            da,sa,za=direction(s*z); ap=step(s,sa);ad=step(z,za)
            mua=float((s+ap*sa)@(z+ad*za)/m);sigma=min(1.,max(0.,(mua/mu)**3))
            dx,ds,dz=direction(s*z+sa*za-sigma*mu)
            ap=step(s,ds,.995);ad=step(z,dz,.995)
            x+=ap*dx;s+=ap*ds;z+=ad*dz
            if not np.isfinite(x).all() or min(s.min(),z.min())<=0:raise NumericalError('IPM iterate invalid')
        report=verify(model,x,z/scale,tol)
        return dict(status='LIMIT_REACHED',algorithm='primal-dual predictor-corrector QP',x=x.tolist(),objective=report['objective'],verification=report,iterations=max_iter,history=history)
    except (NumericalError,FloatingPointError,OverflowError) as e:
        return dict(status='NUMERICAL_FAILURE',algorithm='primal-dual predictor-corrector QP',message=str(e),history=history)
