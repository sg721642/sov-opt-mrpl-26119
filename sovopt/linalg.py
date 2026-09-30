"""Original dense partial-pivot LU with residual refinement; no numpy.linalg solves."""
import numpy as np

class NumericalError(RuntimeError): pass

class LU:
    def __init__(self,A):
        self.original=np.array(A,float,copy=True); self.a=self.original.copy(); n=len(A); self.p=np.arange(n)
        if self.a.shape!=(n,n) or not np.isfinite(self.a).all(): raise NumericalError('Invalid linear system')
        scale=max(1.,float(np.max(np.abs(self.a),initial=0)))
        for k in range(n):
            p=k+int(np.argmax(abs(self.a[k:,k])))
            if abs(self.a[p,k])<1e-14*scale: raise NumericalError('Singular or unsafe pivot')
            if p!=k:self.a[[k,p]]=self.a[[p,k]]; self.p[[k,p]]=self.p[[p,k]]
            if k+1<n:
                self.a[k+1:,k]/=self.a[k,k]
                self.a[k+1:,k+1:]-=np.outer(self.a[k+1:,k],self.a[k,k+1:])
    def raw(self,b):
        x=np.asarray(b,float)[self.p].copy(); n=len(x)
        for i in range(n):x[i]-=self.a[i,:i]@x[:i]
        for i in range(n-1,-1,-1):x[i]=(x[i]-self.a[i,i+1:]@x[i+1:])/self.a[i,i]
        return x
    def solve(self,b):
        x=self.raw(b)
        for _ in range(2):
            r=np.asarray(np.asarray(b,np.longdouble)-np.asarray(self.original,np.longdouble)@np.asarray(x,np.longdouble),float)
            if np.max(abs(r),initial=0)<=1e-13*(1+np.max(abs(b),initial=0)): break
            x+=self.raw(r)
        if not np.isfinite(x).all():raise NumericalError('Nonfinite solve')
        return x

def positive_semidefinite(Q):
    # Pivoted Schur complements (floating-point numerical heuristic; not an exact rational PSD certificate).
    # Conservative: no negative pivot is accepted.
    a=Q.copy(); n=len(a)
    for k in range(n):
        p=k+int(np.argmax(np.diag(a)[k:])); a[[p,k],:]=a[[k,p],:]; a[:,[p,k]]=a[:,[k,p]]
        if a[k,k]<0:return False
        if a[k,k]==0:return bool(np.all(a[k:,k:]==0))
        if k+1<n:a[k+1:,k+1:]-=np.outer(a[k+1:,k],a[k,k+1:])/a[k,k]
    return True
