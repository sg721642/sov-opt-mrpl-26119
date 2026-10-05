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
        A_raw = d.get('A', [])
        from .sparse import CSRMatrix
        if isinstance(A_raw, CSRMatrix):
            A = A_raw
        elif d.get('A_format') == 'csr':
            A = CSRMatrix(d['A_shape'][0], d['A_shape'][1],
                          np.asarray(d['A_indptr'], dtype=np.int64),
                          np.asarray(d['A_indices'], dtype=np.int64),
                          np.asarray(d['A_data'], dtype=np.float64),
                          validate=False)
        else:
            A=np.asarray(A_raw,dtype=float).reshape((-1,n))
        def vec(k,default):
            num_rows = A.shape[0] if hasattr(A, 'shape') else len(A)
            return np.asarray([default if v is None else v for v in d.get(k,[default]*num_rows)],float)
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

    def validate(self, max_vars=None, max_rows=None):
        from .sparse import CSRMatrix
        is_sparse = isinstance(self.A, CSRMatrix)
        n = len(self.c)
        m = self.A.shape[0] if hasattr(self.A, 'shape') else len(self.A)

        if is_sparse:
            # Sovereign sparse memory and dimension guard:
            # Safe for large-scale models up to 10M variables / rows provided sparse bytes <= 2.0 GB
            if not (0 < n <= 10_000_000 and 0 <= m <= 10_000_000):
                raise ValueError(f'Declared sparse dimension limit: 1..10000000 vars/rows (got {n} vars, {m} rows)')
            if self.A.shape != (m, n):
                raise ValueError('Invalid dimensions: sparse matrix shape does not match (m, n)')
            if self.A.memory_bytes > 2_000_000_000:
                raise ValueError(f'Sparse model exceeds memory guard: {self.A.memory_bytes / 1e6:.1f} MB > 2000 MB')
            if not np.all(np.isfinite(self.A.data)):
                raise ValueError('Objective coefficients and constraint matrix must be finite')
        else:
            if max_vars is None:
                max_vars = 5000 if (self.Q is not None or hasattr(self, 'qplib_meta')) else (5000 if self.integer else 5000)
            if max_rows is None:
                max_rows = 15000 if (self.Q is not None or hasattr(self, 'qplib_meta')) else (5000 if self.integer else 5000)
            if not (0 < n <= max_vars and 0 <= m <= max_rows):
                raise ValueError(f'Declared resource limit: 1..{max_vars} variables, <={max_rows} input rows (got {n} vars, {m} rows)')
            if self.A.shape != (m, n):
                raise ValueError('Invalid dimensions')
            if not np.isfinite(self.A).all():
                raise ValueError('Objective coefficients and constraint matrix must be finite')

        if any(v.shape!=(n,) for v in [self.lower,self.upper]): raise ValueError('Invalid dimensions')
        if any(v.shape!=(m,) for v in [self.row_lower,self.row_upper]): raise ValueError('Invalid row bound dimensions')
        if not np.isfinite(self.c).all(): raise ValueError('Objective coefficients and constraint matrix must be finite')
        if not np.isfinite(self.obj_offset): raise ValueError('obj_offset must be finite')
        if np.isnan(self.lower).any() or np.isnan(self.upper).any(): raise ValueError('NaN variable bounds')
        if np.isnan(self.row_lower).any() or np.isnan(self.row_upper).any(): raise ValueError('NaN row bounds')
        if (self.lower>self.upper).any() or (self.row_lower>self.row_upper).any(): raise ValueError('Contradictory bounds')
        if np.isposinf(self.lower).any() or np.isneginf(self.upper).any(): raise ValueError('Invalid variable infinity')
        if np.isposinf(self.row_lower).any() or np.isneginf(self.row_upper).any(): raise ValueError('Invalid row infinity')
        if any(type(i) is not int or not 0<=i<n for i in self.integer) or len(set(self.integer))!=len(self.integer): raise ValueError('Invalid integer indices')
        if len(self.names)!=n or len(set(self.names))!=n: raise ValueError('Variable names must be unique and match dimension n')
        if self.Q is not None:
            if self.Q.shape!=(n,n) or not np.isfinite(self.Q).all() or not np.allclose(self.Q, self.Q.T, atol=1e-12):
                raise ValueError('Q must be finite and exactly symmetric')
            if self.integer: raise ValueError('MIQP is not supported')
            if hasattr(self, 'qplib_meta'):
                if not self.qplib_meta.get('qplib_declared_convex', False):
                    raise ValueError('QPLIB model is not declared convex')
            elif n <= 250:
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
        from .sparse import CSRMatrix
        if isinstance(self.A, CSRMatrix):
            m, n = self.A.shape
            if m * n > 25_000_000:
                raise ValueError(f"Cannot materialize dense inequalities for large sparse model ({m}x{n}). Use sparse_inequalities() instead.")
            A_mat = self.A.to_dense()
        else:
            A_mat = self.A

        rows=[]; rhs=[]; labels=[]
        for i,a in enumerate(A_mat):
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

    def sparse_inequalities(self, bounds=False):
        """Return (G_csr, h, labels) for G*x <= h in sovereign CSRMatrix format without dense arrays."""
        from .sparse import CSRMatrix, csr_from_dense
        n = len(self.c)
        m = self.A.shape[0] if hasattr(self.A, 'shape') else len(self.A)

        upper_finite = np.isfinite(self.row_upper)
        lower_finite = np.isfinite(self.row_lower)
        rhs = []
        labels = []

        if isinstance(self.A, CSRMatrix):
            new_indptr = [0]
            indices_list = []
            data_list = []

            for i in range(m):
                start = self.A.indptr[i]
                end = self.A.indptr[i + 1]
                row_cols = self.A.indices[start:end]
                row_vals = self.A.data[start:end]

                if upper_finite[i]:
                    indices_list.append(row_cols)
                    data_list.append(row_vals)
                    new_indptr.append(new_indptr[-1] + len(row_cols))
                    rhs.append(float(self.row_upper[i]))
                    labels.append(f'row {i} upper')

                if lower_finite[i]:
                    indices_list.append(row_cols)
                    data_list.append(-row_vals)
                    new_indptr.append(new_indptr[-1] + len(row_cols))
                    rhs.append(float(-self.row_lower[i]))
                    labels.append(f'row {i} lower')

            if bounds:
                for j in range(n):
                    var_name = self.names[j] if j < len(self.names) else f'x{j}'
                    if np.isfinite(self.upper[j]):
                        indices_list.append(np.array([j], dtype=np.int64))
                        data_list.append(np.array([1.0], dtype=np.float64))
                        new_indptr.append(new_indptr[-1] + 1)
                        rhs.append(float(self.upper[j]))
                        labels.append(f'{var_name} upper')
                    if np.isfinite(self.lower[j]):
                        indices_list.append(np.array([j], dtype=np.int64))
                        data_list.append(np.array([-1.0], dtype=np.float64))
                        new_indptr.append(new_indptr[-1] + 1)
                        rhs.append(float(-self.lower[j]))
                        labels.append(f'{var_name} lower')

            m_ineq = len(new_indptr) - 1
            if indices_list:
                new_indices = np.concatenate(indices_list)
                new_data = np.concatenate(data_list)
            else:
                new_indices = np.zeros(0, dtype=np.int64)
                new_data = np.zeros(0, dtype=np.float64)

            G_csr = CSRMatrix(m_ineq, n, np.array(new_indptr, dtype=np.int64), new_indices, new_data, validate=False)
            return G_csr, np.asarray(rhs, dtype=np.float64), labels
        else:
            G, h, labels = self.inequalities(bounds=bounds)
            return csr_from_dense(G), h, labels

    def to_dict(self):
        from .sparse import CSRMatrix
        fin=lambda a:[None if not np.isfinite(v) else float(v) for v in a]
        d=dict(name=self.name,names=list(self.names),c=self.c.tolist(),
               row_lower=fin(self.row_lower),row_upper=fin(self.row_upper),
               lower=fin(self.lower),upper=fin(self.upper),
               integer=list(self.integer),Q=None if self.Q is None else self.Q.tolist())
        if isinstance(self.A, CSRMatrix):
            d['A_format'] = 'csr'
            d['A_shape'] = list(self.A.shape)
            d['A_indptr'] = self.A.indptr.tolist()
            d['A_indices'] = self.A.indices.tolist()
            d['A_data'] = self.A.data.tolist()
            d['A'] = []
        else:
            d['A'] = self.A.tolist()
        if self.maximize: d['maximize']=True
        if self.obj_offset!=0.0: d['obj_offset']=self.obj_offset
        return d

    def fingerprint(self): return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def load(path):
    p = str(path).lower()
    if p.endswith(('.mps', '.qps')):
        from .mps import read_mps
        return read_mps(path)
    elif p.endswith('.qplib'):
        from .qplib import read_qplib
        return read_qplib(path)
    with open(path) as f: return Model.from_dict(json.load(f))
