"""Finite-box canonical model. No optimizer dependency.

Variable bounds may be infinite (unbounded variables are supported).
Row bounds may be +/-inf (one-sided constraints are supported).
Objective sense may be MIN (default) or MAX (stored as negated c with maximize=True).

JSON Representation:
- name: string, model identifier.
- names: list of n unique strings for variable identifiers.
- c: list of n floats, linear objective coefficients.
- A: list of m rows, each row being a list of n floats (dense constraint matrix).
- row_lower: list of m floats or nulls (null = -inf), lower bounds on A[i] @ x.
- row_upper: list of m floats or nulls (null = +inf), upper bounds on A[i] @ x.
- lower: list of n floats or nulls (null = 0.0 by default in from_dict, or -inf if specified).
- upper: list of n floats or nulls (null = +inf by default in from_dict).
- integer: list of 0-based integer variable indices.
- Q: optional list of n rows, each a list of n floats, representing 0.5 * x^T * Q * x.
- maximize: optional boolean (default false); if true, original problem is maximization.
- obj_offset: optional float constant offset added to the objective value.
"""
from dataclasses import dataclass, field
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
    maximize: bool = False   # True: original problem maximizes; c is negated for internal min
    obj_offset: float = 0.0  # Objective constant from MPS RHS on N row; added back to reported value

    @classmethod
    def from_dict(cls, d):
        c=np.asarray(d['c'],dtype=float); n=len(c)
        A=np.asarray(d.get('A',[]),dtype=float).reshape((-1,n))
        def vec(k,default):
            return np.asarray([default if v is None else v for v in d.get(k,[default]*len(A))],float)
        # Default upper bound is +inf (unbounded above) when not specified
        upper_raw = d.get('upper', None)
        if upper_raw is None:
            upper = np.full(n, np.inf)
        else:
            upper = np.asarray([np.inf if v is None else v for v in upper_raw], float)
        lower_raw = d.get('lower', None)
        if lower_raw is None:
            lower = np.zeros(n)
        else:
            lower = np.asarray([-np.inf if v is None else v for v in lower_raw], float)
        obj=cls(c,A,vec('row_lower',-np.inf),vec('row_upper',np.inf),
                lower, upper,
                tuple(d.get('integer',[])),None if d.get('Q') is None else np.asarray(d['Q'],float),
                d.get('name','model'),tuple(d.get('names',[f'x{i}' for i in range(n)])),
                bool(d.get('maximize',False)),float(d.get('obj_offset',0.0)))
        obj.validate(); return obj

    def validate(self):
        n=len(self.c); m=len(self.A)
        if not 0<n<=250 or m>1000: raise ValueError('Dense prototype limit: 1..250 variables, <=1000 input rows')
        if self.A.shape!=(m,n) or any(v.shape!=(n,) for v in [self.lower,self.upper]): raise ValueError('Invalid dimensions')
        if any(v.shape!=(m,) for v in [self.row_lower,self.row_upper]): raise ValueError('Invalid row bound dimensions')
        # c and A must be finite; variable bounds may be infinite
        if not (np.isfinite(self.c).all() and np.isfinite(self.A).all()): raise ValueError('Objective coefficients and constraint matrix must be finite')
        if not np.isfinite(self.obj_offset): raise ValueError('obj_offset must be finite')
        if np.isnan(self.lower).any() or np.isnan(self.upper).any(): raise ValueError('NaN variable bounds')
        if np.isnan(self.row_lower).any() or np.isnan(self.row_upper).any(): raise ValueError('NaN row bounds')
        if (self.lower>self.upper).any() or (self.row_lower>self.row_upper).any(): raise ValueError('Contradictory bounds')
        if np.isposinf(self.lower).any() or np.isneginf(self.upper).any(): raise ValueError('Invalid variable infinity')
        if np.isposinf(self.row_lower).any() or np.isneginf(self.row_upper).any(): raise ValueError('Invalid row infinity')
        if any(type(i) is not int or not 0<=i<n for i in self.integer) or len(set(self.integer))!=len(self.integer): raise ValueError('Invalid integer indices')
        if len(self.names)!=n or len(set(self.names))!=n: raise ValueError('Variable names must be unique and match dimension n')
        if self.Q is not None:
            if self.Q.shape!=(n,n) or not np.isfinite(self.Q).all() or not np.array_equal(self.Q,self.Q.T): raise ValueError('Q must be finite and exactly symmetric')
            if self.integer: raise ValueError('MIQP is not supported')
            from .linalg import positive_semidefinite
            if not positive_semidefinite(self.Q): raise ValueError('Q is not demonstrably positive semidefinite')

    def __post_init__(self):
        if not self.names or len(self.names) != len(self.c):
            self.names = tuple(f'x{i}' for i in range(len(self.c)))

    def inequalities(self, bounds=True):
        """Return (G, h, labels) for G*x <= h encoding all finite constraints.
        Infinite variable bounds produce no bound row; the unbounded direction
        is handled by the simplex ratio test (no leaving variable => LP is unbounded).
        The original model (including infinite bounds) is preserved in self.lower/upper.
        """
        rows=[]; rhs=[]; labels=[]
        for i,a in enumerate(self.A):
            if np.isfinite(self.row_upper[i]): rows.append(a); rhs.append(self.row_upper[i]); labels.append(f'row {i} upper')
            if np.isfinite(self.row_lower[i]): rows.append(-a); rhs.append(-self.row_lower[i]); labels.append(f'row {i} lower')
        if bounds:
            for i in range(len(self.c)):
                e=np.zeros(len(self.c)); e[i]=1
                var_name = self.names[i] if i < len(self.names) else f'x{i}'
                if np.isfinite(self.upper[i]): rows.append(e.copy()); rhs.append(self.upper[i]); labels.append(f'{var_name} upper')
                if np.isfinite(self.lower[i]): rows.append(-e.copy()); rhs.append(-self.lower[i]); labels.append(f'{var_name} lower')
        if not rows:
            return np.zeros((0,len(self.c)),float), np.zeros(0,float), []
        return np.asarray(rows,float).reshape((-1,len(self.c))),np.asarray(rhs,float),labels

    def to_dict(self):
        fin=lambda a:[None if not np.isfinite(v) else float(v) for v in a]
        d=dict(name=self.name,names=list(self.names),c=self.c.tolist(),A=self.A.tolist(),
               row_lower=fin(self.row_lower),row_upper=fin(self.row_upper),
               lower=fin(self.lower),upper=fin(self.upper),
               integer=list(self.integer),Q=None if self.Q is None else self.Q.tolist())
        if self.maximize: d['maximize']=True
        if self.obj_offset!=0.0: d['obj_offset']=self.obj_offset
        return d

    def fingerprint(self): return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def load(path):
    if str(path).lower().endswith(('.mps', '.qps')):
        from .mps import read_mps
        return read_mps(path)
    with open(path) as f:return Model.from_dict(json.load(f))
