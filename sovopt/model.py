"""Finite-box canonical model. No optimizer dependency."""
from dataclasses import dataclass
import json, hashlib
import numpy as np

@dataclass
class Model:
    c: np.ndarray
    A: np.ndarray
    row_lower: np.ndarray
    row_upper: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    integer: tuple = ()
    Q: np.ndarray | None = None
    name: str = 'model'
    names: tuple = ()

    @classmethod
    def from_dict(cls, d):
        c=np.asarray(d['c'],dtype=float); n=len(c)
        A=np.asarray(d.get('A',[]),dtype=float).reshape((-1,n))
        def vec(k,default):
            return np.asarray([default if v is None else v for v in d.get(k,[default]*len(A))],float)
        obj=cls(c,A,vec('row_lower',-np.inf),vec('row_upper',np.inf),
                np.asarray(d.get('lower',[0]*n),float),np.asarray(d['upper'],float),
                tuple(d.get('integer',[])),None if d.get('Q') is None else np.asarray(d['Q'],float),
                d.get('name','model'),tuple(d.get('names',[f'x{i}' for i in range(n)])))
        obj.validate(); return obj

    def validate(self):
        n=len(self.c); m=len(self.A)
        if not 0<n<=250 or m>1000: raise ValueError('Dense prototype limit: 1..250 variables, <=1000 input rows')
        if self.A.shape!=(m,n) or any(v.shape!=(n,) for v in [self.lower,self.upper]): raise ValueError('Invalid dimensions')
        if any(v.shape!=(m,) for v in [self.row_lower,self.row_upper]): raise ValueError('Invalid row bound dimensions')
        if not all(np.isfinite(a).all() for a in [self.c,self.A,self.lower,self.upper]): raise ValueError('Coefficients and variable bounds must be finite')
        if np.isnan(self.row_lower).any() or np.isnan(self.row_upper).any(): raise ValueError('NaN row bounds')
        if (self.lower>self.upper).any() or (self.row_lower>self.row_upper).any(): raise ValueError('Contradictory bounds')
        if np.isposinf(self.row_lower).any() or np.isneginf(self.row_upper).any(): raise ValueError('Invalid row infinity')
        if any(type(i) is not int or not 0<=i<n for i in self.integer) or len(set(self.integer))!=len(self.integer): raise ValueError('Invalid integer indices')
        if len(self.names)!=n: raise ValueError('Invalid names')
        if self.Q is not None:
            if self.Q.shape!=(n,n) or not np.isfinite(self.Q).all() or not np.array_equal(self.Q,self.Q.T): raise ValueError('Q must be finite and exactly symmetric')
            if self.integer: raise ValueError('MIQP is not supported')
            from .linalg import positive_semidefinite
            if not positive_semidefinite(self.Q): raise ValueError('Q is not demonstrably positive semidefinite')

    def inequalities(self, bounds=True):
        rows=[]; rhs=[]; labels=[]
        for i,a in enumerate(self.A):
            if np.isfinite(self.row_upper[i]): rows.append(a); rhs.append(self.row_upper[i]); labels.append(f'row {i} upper')
            if np.isfinite(self.row_lower[i]): rows.append(-a); rhs.append(-self.row_lower[i]); labels.append(f'row {i} lower')
        if bounds:
            for i in range(len(self.c)):
                e=np.zeros(len(self.c)); e[i]=1
                rows.extend([e,-e]); rhs.extend([self.upper[i],-self.lower[i]]); labels.extend([f'{self.names[i]} upper',f'{self.names[i]} lower'])
        return np.asarray(rows,float).reshape((-1,len(self.c))),np.asarray(rhs,float),labels

    def to_dict(self):
        finite=lambda a:[None if not np.isfinite(v) else float(v) for v in a]
        return dict(name=self.name,names=list(self.names),c=self.c.tolist(),A=self.A.tolist(),row_lower=finite(self.row_lower),row_upper=finite(self.row_upper),lower=self.lower.tolist(),upper=self.upper.tolist(),integer=list(self.integer),Q=None if self.Q is None else self.Q.tolist())

    def fingerprint(self): return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def load(path):
    if str(path).lower().endswith('.mps'):
        from .mps import read_mps
        return read_mps(path)
    with open(path) as f:return Model.from_dict(json.load(f))
