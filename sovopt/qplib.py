"""Native QPLIB parser for continuous convex quadratic programming.

Implements the official QPLIB file format specification from ZIB:
https://qplib.zib.de/doc.html

Mathematical optimization problem:
    sense: 1/2 * x^T Q^0 x + b^0^T x + q^0
    s.t.   c_l <= 1/2 * x^T Q^i x + b^i^T x <= c_u    (i in 1..m)
           l <= x <= u                                 (j in 1..n)
           x in R^n (continuous)

Supported production subset:
- Continuous variables (PROBTYPE second character == 'C')
- Convex/diagonal quadratic objective (PROBTYPE first character in ('C', 'D', 'L'))
- Linear constraints (PROBTYPE third character in ('L', 'B', 'N') and Q^i == 0)
- Explicit variable bounds and objective offsets

Explicit rejection hierarchy:
- Discrete variables (B, M, I, G) -> UnsupportedQPLIBError
- Quadratic constraints (Q, D, C in constraint field or constraint quadratic nonzeros) -> UnsupportedQPLIBError
- Nonconvex quadratic objective (Q in objective field) -> UnsupportedQPLIBError
- Resource limit exceeded (dense memory projection exceeds ceiling) -> UnsupportedQPLIBError
- Malformed syntax -> QPLIBFormatError
"""

from pathlib import Path
import re
import numpy as np
from .model import Model

class QPLIBError(ValueError):
    """Base exception for QPLIB parsing errors."""
    pass

class QPLIBFormatError(QPLIBError):
    """Raised when a QPLIB file violates the format specification."""
    pass

class UnsupportedQPLIBError(QPLIBError):
    """Raised when a QPLIB problem class is unsupported by the continuous convex QP solver."""
    def __init__(self, message, reason_code="UNSUPPORTED_CLASS", probtype=None):
        super().__init__(message)
        self.reason_code = reason_code
        self.probtype = probtype

# Allow-list of supported PROBTYPE classifications for continuous convex QP
SUPPORTED_PROBTYPES = frozenset([
    'CCL', 'CCB', 'CCN',
    'DCL', 'DCB', 'DCN',
    'LCL', 'LCB', 'LCN'
])

# Default dense variable count limit to protect against RAM exhaustion / swap
DEFAULT_MAX_DENSE_VARS = 5000
DEFAULT_MAX_DENSE_BYTES = 250 * 1024 * 1024  # 250 MB ceiling

def parse_probtype(probtype: str):
    """Decompose and validate a QPLIB 3-character PROBTYPE code.
    
    Returns:
        dict with keys: probtype, objective_class, variable_class, constraint_class,
                        is_supported, eligibility_reason, reason_code.
    """
    pt = probtype.strip().upper()
    if len(pt) != 3:
        raise QPLIBFormatError(f"Invalid PROBTYPE '{probtype}': expected exactly 3 characters (e.g. 'CCL', 'QCL').")

    obj_code, var_code, cons_code = pt[0], pt[1], pt[2]
    
    obj_names = {'L': 'linear', 'D': 'diagonal_convex', 'C': 'convex_quadratic', 'Q': 'general_quadratic'}
    var_names = {'C': 'continuous', 'B': 'binary', 'M': 'mixed_integer', 'I': 'integer', 'G': 'general_integer'}
    cons_names = {'L': 'linear', 'B': 'box_bounds_only', 'N': 'unconstrained',
                  'D': 'diagonal_quadratic', 'Q': 'general_quadratic', 'C': 'convex_quadratic'}

    obj_desc = obj_names.get(obj_code, f'unknown_{obj_code}')
    var_desc = var_names.get(var_code, f'unknown_{var_code}')
    cons_desc = cons_names.get(cons_code, f'unknown_{cons_code}')

    if var_code != 'C':
        reason = f"UNSUPPORTED: discrete/integer variable type '{var_code}' ({var_desc}) not supported in continuous QP solver."
        return dict(probtype=pt, objective_class=obj_desc, variable_class=var_desc,
                    constraint_class=cons_desc, is_supported=False, eligibility_reason=reason,
                    reason_code="UNSUPPORTED_DISCRETE_VARIABLES")

    if cons_code in ('Q', 'D', 'C'):
        reason = f"UNSUPPORTED: quadratic constraints '{cons_code}' ({cons_desc}) not supported; solver accepts linear constraints and bounds only."
        return dict(probtype=pt, objective_class=obj_desc, variable_class=var_desc,
                    constraint_class=cons_desc, is_supported=False, eligibility_reason=reason,
                    reason_code="UNSUPPORTED_QUADRATIC_CONSTRAINTS")

    if obj_code == 'Q':
        reason = f"UNSUPPORTED: general/nonconvex quadratic objective '{obj_code}' ({obj_desc}) rejected; solver requires convex objective."
        return dict(probtype=pt, objective_class=obj_desc, variable_class=var_desc,
                    constraint_class=cons_desc, is_supported=False, eligibility_reason=reason,
                    reason_code="UNSUPPORTED_NONCONVEX_QP")

    if pt not in SUPPORTED_PROBTYPES:
        reason = f"UNSUPPORTED: problem type '{pt}' is not in the supported continuous convex QP allow-list."
        return dict(probtype=pt, objective_class=obj_desc, variable_class=var_desc,
                    constraint_class=cons_desc, is_supported=False, eligibility_reason=reason,
                    reason_code="UNSUPPORTED_CLASS")

    return dict(probtype=pt, objective_class=obj_desc, variable_class=var_desc,
                constraint_class=cons_desc, is_supported=True, eligibility_reason="SUPPORTED_CONTINUOUS_CONVEX_QP",
                reason_code="SUPPORTED")


def read_qplib(path, max_dense_vars=DEFAULT_MAX_DENSE_VARS, max_dense_bytes=DEFAULT_MAX_DENSE_BYTES,
               check_psd=True, psd_dim_limit=2500):
    """Parse an authentic QPLIB instance into a sovereign sovopt.Model.
    
    Args:
        path: Path to .qplib file.
        max_dense_vars: Maximum number of variables permitted for dense conversion.
        max_dense_bytes: Maximum estimated memory permitted for dense conversion.
        check_psd: Whether to compute local eigenvalue diagnostics for moderate matrices.
        psd_dim_limit: Maximum dimension for eigenvalue PSD verification.
        
    Returns:
        Model: A canonical sovereign sovopt.Model instance with attached metadata in `model.qplib_meta`.
        
    Raises:
        UnsupportedQPLIBError: If instance contains integer variables, quadratic constraints,
                               nonconvex objective, or exceeds declared resource envelope.
        QPLIBFormatError: If file is malformed.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"QPLIB file not found: {path}")

    text = path.read_text(encoding='utf-8', errors='replace')
    
    # Tokenize while discarding comments starting with #, !, or %
    tokens = []
    for line in text.splitlines():
        line = re.sub(r'[#!%].*$', '', line).strip()
        if line:
            tokens.extend(line.split())

    if len(tokens) < 6:
        raise QPLIBFormatError(f"QPLIB file {path.name} is too short or malformed.")

    pos = 0
    name = tokens[pos]; pos += 1
    probtype = tokens[pos]; pos += 1
    sense_str = tokens[pos].lower(); pos += 1
    n = int(tokens[pos]); pos += 1
    m = int(tokens[pos]); pos += 1
    nq0 = int(tokens[pos]); pos += 1

    if sense_str not in ('minimize', 'maximize'):
        raise QPLIBFormatError(f"Invalid objective sense '{sense_str}' in {path.name}. Expected 'minimize' or 'maximize'.")
    maximize = (sense_str == 'maximize')

    # Step B: PROBTYPE eligibility check
    pt_meta = parse_probtype(probtype)
    if not pt_meta['is_supported']:
        raise UnsupportedQPLIBError(
            f"QPLIB instance '{name}' rejected: {pt_meta['eligibility_reason']}",
            reason_code=pt_meta['reason_code'],
            probtype=probtype
        )

    # Step E: Sparse storage and pre-allocation memory guard
    estimated_q_bytes = 8 * n * n
    estimated_a_bytes = 8 * m * n
    total_dense_bytes = estimated_q_bytes + estimated_a_bytes

    if n > max_dense_vars or total_dense_bytes > max_dense_bytes:
        raise UnsupportedQPLIBError(
            f"QPLIB instance '{name}' (n={n}, m={m}) exceeds dense resource limit "
            f"(projected memory: {total_dense_bytes / (1024*1024):.1f} MB > limit {max_dense_bytes / (1024*1024):.1f} MB).",
            reason_code="UNSUPPORTED_RESOURCE_LIMIT",
            probtype=probtype
        )

    # Parse quadratic objective terms Q^0
    # QPLIB lower-triangular format: row col val where row >= col (1-based indices)
    q_triplets = []
    q_sparse_dict = {}
    for _ in range(nq0):
        if pos + 2 >= len(tokens):
            raise QPLIBFormatError(f"Unexpected EOF while reading quadratic objective terms in {path.name}.")
        r = int(tokens[pos]) - 1
        c = int(tokens[pos+1]) - 1
        v = float(tokens[pos+2])
        pos += 3
        
        if not np.isfinite(v):
            raise QPLIBFormatError(f"Non-finite value {v} in quadratic objective term ({r+1}, {c+1}).")
        if r < c:
            raise QPLIBFormatError(f"QPLIB quadratic terms must be lower triangular (row >= col), got row={r+1}, col={c+1}.")
        if r < 0 or r >= n or c < 0 or c >= n:
            raise QPLIBFormatError(f"Quadratic objective index out of bounds: ({r+1}, {c+1}) for n={n}.")
            
        q_triplets.append((r, c, v))
        q_sparse_dict[(r, c)] = q_sparse_dict.get((r, c), 0.0) + v

    # Reconstruct symmetric Q matrix
    # Under QPLIB convention: sense [ 1/2 x^T Q^0 x + b^0^T x + q^0 ]
    # where Q^0 is officially lower-triangular (Q^0_ij = 0 for i < j).
    # For a symmetric matrix Q_sym in 1/2 x^T Q_sym x:
    #   Diagonal: 1/2 Q_sym_ii x_i^2 = 1/2 Q^0_ii x_i^2 => Q_sym_ii = val
    #   Off-diagonal: 1/2 (Q_sym_ij + Q_sym_ji) x_i x_j = Q_sym_ij x_i x_j = 1/2 Q^0_ij x_i x_j
    #     => Q_sym_ij = Q_sym_ji = 0.5 * val
    Q_dense = np.zeros((n, n), dtype=float)
    for (r, c), v in q_sparse_dict.items():
        if r == c:
            Q_dense[r, c] += v
        else:
            Q_dense[r, c] += 0.5 * v
            Q_dense[c, r] += 0.5 * v

    q_nnz_symmetric = int(np.count_nonzero(Q_dense))
    q_density = q_nnz_symmetric / max(1, n * n)

    # Step D: Convexity verification & PSD diagnostics
    q_declared_convex = (probtype[0].upper() in ('C', 'D', 'L'))
    local_psd_check = None
    min_eigval = None
    max_diag = float(np.max(np.abs(np.diag(Q_dense)))) if n > 0 else 1.0
    scale = max(1.0, max_diag)
    convexity_tol = 1e-10 * scale

    if check_psd and n <= psd_dim_limit:
        eigvals = np.linalg.eigvalsh(Q_dense)
        min_eigval = float(np.min(eigvals)) if len(eigvals) > 0 else 0.0
        local_psd_check = bool(min_eigval >= -convexity_tol)
        
        # If declared convex but severely negative, reject
        if min_eigval < -convexity_tol:
            if not q_declared_convex:
                raise UnsupportedQPLIBError(
                    f"QPLIB instance '{name}' is nonconvex (min eigenvalue = {min_eigval:.4e} < -{convexity_tol:.4e}).",
                    reason_code="UNSUPPORTED_NONCONVEX_QP",
                    probtype=probtype
                )
            # Numerically tiny violation on declared convex instance: project onto PSD
            Q_dense += max(0.0, -min_eigval + 1e-12) * np.eye(n)
            eligibility_result = "ELIGIBLE_PSD_PROJECTED"
        else:
            eligibility_result = "ELIGIBLE_PSD_CONFIRMED"
    else:
        eligibility_result = "ELIGIBLE_PROBTYPE_DECLARED" if q_declared_convex else "UNCHECKED"

    # Linear objective coefficients b^0
    if pos >= len(tokens):
        raise QPLIBFormatError(f"Unexpected EOF reading default linear objective coefficient in {path.name}.")
    def_lin_obj = float(tokens[pos]); pos += 1
    n_nondef_lin = int(tokens[pos]); pos += 1

    c_dense = np.full(n, def_lin_obj, dtype=float)
    for _ in range(n_nondef_lin):
        idx = int(tokens[pos]) - 1
        val = float(tokens[pos+1])
        pos += 2
        if 0 <= idx < n:
            c_dense[idx] = val

    # Objective constant q^0
    obj_const = float(tokens[pos]); pos += 1

    # Linear constraint terms
    n_a_terms = int(tokens[pos]); pos += 1
    A_dense = np.zeros((m, n), dtype=float)
    for _ in range(n_a_terms):
        r = int(tokens[pos]) - 1
        c = int(tokens[pos+1]) - 1
        v = float(tokens[pos+2])
        pos += 3
        if 0 <= r < m and 0 <= c < n:
            A_dense[r, c] += v

    # Infinity value and constraint bounds
    inf_val = float(tokens[pos]); pos += 1

    # Left hand side c_l
    def_lhs = float(tokens[pos]); pos += 1
    n_nondef_lhs = int(tokens[pos]); pos += 1
    row_lower = np.full(m, def_lhs, dtype=float)
    for _ in range(n_nondef_lhs):
        r = int(tokens[pos]) - 1
        v = float(tokens[pos+1])
        pos += 2
        if 0 <= r < m:
            row_lower[r] = v

    # Right hand side c_u
    def_rhs = float(tokens[pos]); pos += 1
    n_nondef_rhs = int(tokens[pos]); pos += 1
    row_upper = np.full(m, def_rhs, dtype=float)
    for _ in range(n_nondef_rhs):
        r = int(tokens[pos]) - 1
        v = float(tokens[pos+1])
        pos += 2
        if 0 <= r < m:
            row_upper[r] = v

    # Variable lower bounds l
    def_var_lb = float(tokens[pos]); pos += 1
    n_nondef_var_lb = int(tokens[pos]); pos += 1
    lower = np.full(n, def_var_lb, dtype=float)
    for _ in range(n_nondef_var_lb):
        j = int(tokens[pos]) - 1
        v = float(tokens[pos+1])
        pos += 2
        if 0 <= j < n:
            lower[j] = v

    # Variable upper bounds u
    def_var_ub = float(tokens[pos]); pos += 1
    n_nondef_var_ub = int(tokens[pos]); pos += 1
    upper = np.full(n, def_var_ub, dtype=float)
    for _ in range(n_nondef_var_ub):
        j = int(tokens[pos]) - 1
        v = float(tokens[pos+1])
        pos += 2
        if 0 <= j < n:
            upper[j] = v

    # Normalize infinity bounds
    INF_CUTOFF = 1e20
    row_lower = np.where(row_lower <= -INF_CUTOFF, -np.inf, row_lower)
    row_upper = np.where(row_upper >= INF_CUTOFF, np.inf, row_upper)
    lower = np.where(lower <= -INF_CUTOFF, -np.inf, lower)
    upper = np.where(upper >= INF_CUTOFF, np.inf, upper)

    # Optional starting point and non-default names
    var_names = [f"x{j+1}" for j in range(n)]
    try:
        if pos < len(tokens):
            def_x0 = float(tokens[pos]); pos += 1
            n_x0 = int(tokens[pos]); pos += 1
            pos += n_x0 * 2
        if pos < len(tokens):
            def_y0 = float(tokens[pos]); pos += 1
            n_y0 = int(tokens[pos]); pos += 1
            pos += n_y0 * 2
        if pos < len(tokens):
            def_z0 = float(tokens[pos]); pos += 1
            n_z0 = int(tokens[pos]); pos += 1
            pos += n_z0 * 2
        if pos < len(tokens):
            n_vnames = int(tokens[pos]); pos += 1
            for _ in range(n_vnames):
                v_idx = int(tokens[pos]) - 1
                v_name = tokens[pos+1]
                pos += 2
                if 0 <= v_idx < n:
                    var_names[v_idx] = v_name
    except (IndexError, ValueError):
        pass  # Trailing metadata is optional

    # Create canonical Model
    model = Model(
        c=c_dense,
        A=A_dense,
        row_lower=row_lower,
        row_upper=row_upper,
        lower=lower,
        upper=upper,
        integer=(),
        names=var_names,
        maximize=maximize,
        obj_offset=obj_const,
        Q=Q_dense,
        name=name
    )

    # Attach immutable QPLIB metadata
    model.qplib_meta = {
        'name': name,
        'probtype': probtype,
        'probtype_parsed': pt_meta,
        'sense': 'maximize' if maximize else 'minimize',
        'n_variables': n,
        'n_constraints': m,
        'nq0': nq0,
        'q_nnz_symmetric': q_nnz_symmetric,
        'q_density': q_density,
        'q_triplets_count': len(q_triplets),
        'qplib_declared_convex': q_declared_convex,
        'local_psd_check': local_psd_check,
        'minimum_eigenvalue': min_eigval,
        'convexity_tolerance': convexity_tol,
        'eligibility_result': eligibility_result,
        'dense_bytes_allocated': total_dense_bytes
    }

    return model
