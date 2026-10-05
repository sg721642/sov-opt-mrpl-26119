"""Reversible canonical model transformations.
Preserves integer lattices, original constraints, and exact dual mappings.

Supported variable types:
- LOWER: x_j >= lower_j (finite lower, upper=+inf) -> x_j = lower_j + t_k (t_k >= 0)
- BOX: lower_j <= x_j <= upper_j (both finite)   -> x_j = lower_j + t_k (0 <= t_k <= upper_j - lower_j)
- UPPER_ONLY: x_j <= upper_j (lower=-inf, finite upper) -> x_j = upper_j - t_k (t_k >= 0)
- FREE: -inf < x_j < +inf                        -> x_j = t_k+ - t_k- (t_k+, t_k- >= 0)
- FIXED: lower_j == upper_j                      -> x_j = lower_j (exact elimination)
"""
from dataclasses import dataclass
import numpy as np

@dataclass
class TransformedModel:
    # Standard-form matrix representation:
    # Variables t >= 0
    # Equality rows: A_eq @ t == b_eq
    # Inequality rows: A_le @ t <= b_le
    c: np.ndarray             # (n_trans,)
    A_eq: np.ndarray          # (m_eq, n_trans)
    b_eq: np.ndarray          # (m_eq,)
    A_le: np.ndarray          # (m_le, n_trans)
    b_le: np.ndarray          # (m_le,)
    # Metadata for postsolve
    var_specs: list           # per original variable: type, indices, offsets
    n_orig: int
    obj_constant: float       # constant added to objective by shifts / fixed vars
    orig_eq_rows: list        # indices of equality rows in original model
    orig_le_rows: list        # indices of LE rows in original model
    orig_ge_rows: list        # indices of GE rows in original model

def transform_model(model):
    """Transform model into standard non-negative variables t >= 0 with separated equality and inequality rows."""
    n = len(model.c)
    m = len(model.A)
    A_mat = model.A.to_dense() if hasattr(model.A, 'to_dense') else model.A
    var_specs = []
    curr_trans_idx = 0
    obj_constant = 0.0

    # 1. Analyze variables
    for j in range(n):
        l = model.lower[j]
        u = model.upper[j]
        c_j = model.c[j]

        if l > u:
            raise ValueError(f'Contradictory bounds on variable {j}: {l} > {u}')

        if l == u:
            # Fixed variable: eliminate
            spec = {'type': 'FIXED', 'orig_idx': j, 'val': l, 'trans_indices': []}
            obj_constant += c_j * l
        elif np.isfinite(l) and not np.isfinite(u):
            # Finite lower only: x_j = l + t
            spec = {'type': 'LOWER', 'orig_idx': j, 'shift': l, 'trans_indices': [curr_trans_idx]}
            obj_constant += c_j * l
            curr_trans_idx += 1
        elif np.isfinite(l) and np.isfinite(u):
            # Finite box: x_j = l + t, t <= u - l
            spec = {'type': 'BOX', 'orig_idx': j, 'shift': l, 'range': u - l, 'trans_indices': [curr_trans_idx]}
            obj_constant += c_j * l
            curr_trans_idx += 1
        elif not np.isfinite(l) and np.isfinite(u):
            # Upper only: x_j = u - t (t >= 0)
            spec = {'type': 'UPPER_ONLY', 'orig_idx': j, 'shift': u, 'trans_indices': [curr_trans_idx]}
            obj_constant += c_j * u
            curr_trans_idx += 1
        else:
            # Free variable: x_j = t+ - t-
            spec = {'type': 'FREE', 'orig_idx': j, 'trans_indices': [curr_trans_idx, curr_trans_idx + 1]}
            curr_trans_idx += 2
        var_specs.append(spec)

    n_trans = curr_trans_idx

    # 2. Build transformed objective vector c_trans
    c_trans = np.zeros(n_trans, dtype=float)
    for spec in var_specs:
        j = spec['orig_idx']
        c_j = model.c[j]
        vtype = spec['type']
        if vtype in ('LOWER', 'BOX'):
            c_trans[spec['trans_indices'][0]] = c_j
        elif vtype == 'UPPER_ONLY':
            # x_j = u - t => c_j * x_j = c_j * u - c_j * t => coeff on t is -c_j
            c_trans[spec['trans_indices'][0]] = -c_j
        elif vtype == 'FREE':
            # x_j = t+ - t- => c_j * t+ - c_j * t-
            c_trans[spec['trans_indices'][0]] = c_j
            c_trans[spec['trans_indices'][1]] = -c_j

    # 3. Classify original rows
    orig_eq_rows = []
    orig_le_rows = []
    orig_ge_rows = []
    for i in range(m):
        rl = model.row_lower[i]
        ru = model.row_upper[i]
        if rl == ru and np.isfinite(rl):
            orig_eq_rows.append(i)
        else:
            if np.isfinite(ru):
                orig_le_rows.append(i)
            if np.isfinite(rl):
                orig_ge_rows.append(i)

    # 4. Construct equality matrix and RHS: A_eq @ t == b_eq
    A_eq_rows = []
    b_eq_rows = []
    for i in orig_eq_rows:
        rhs_val = model.row_upper[i]
        row_t = np.zeros(n_trans, dtype=float)
        for spec in var_specs:
            j = spec['orig_idx']
            a_ij = A_mat[i, j]
            if a_ij == 0.0:
                continue
            vtype = spec['type']
            if vtype == 'FIXED':
                rhs_val -= a_ij * spec['val']
            elif vtype in ('LOWER', 'BOX'):
                rhs_val -= a_ij * spec['shift']
                row_t[spec['trans_indices'][0]] += a_ij
            elif vtype == 'UPPER_ONLY':
                rhs_val -= a_ij * spec['shift']
                row_t[spec['trans_indices'][0]] -= a_ij
            elif vtype == 'FREE':
                row_t[spec['trans_indices'][0]] += a_ij
                row_t[spec['trans_indices'][1]] -= a_ij
        A_eq_rows.append(row_t)
        b_eq_rows.append(rhs_val)

    # 5. Construct inequality matrix and RHS: A_le @ t <= b_le
    A_le_rows = []
    b_le_rows = []
    # From original LE rows:
    for i in orig_le_rows:
        rhs_val = model.row_upper[i]
        row_t = np.zeros(n_trans, dtype=float)
        for spec in var_specs:
            j = spec['orig_idx']
            a_ij = A_mat[i, j]
            if a_ij == 0.0:
                continue
            vtype = spec['type']
            if vtype == 'FIXED':
                rhs_val -= a_ij * spec['val']
            elif vtype in ('LOWER', 'BOX'):
                rhs_val -= a_ij * spec['shift']
                row_t[spec['trans_indices'][0]] += a_ij
            elif vtype == 'UPPER_ONLY':
                rhs_val -= a_ij * spec['shift']
                row_t[spec['trans_indices'][0]] -= a_ij
            elif vtype == 'FREE':
                row_t[spec['trans_indices'][0]] += a_ij
                row_t[spec['trans_indices'][1]] -= a_ij
        A_le_rows.append(row_t)
        b_le_rows.append(rhs_val)

    # From original GE rows: row_lower <= a_i @ x  <=> -a_i @ x <= -row_lower
    for i in orig_ge_rows:
        rhs_val = -model.row_lower[i]
        row_t = np.zeros(n_trans, dtype=float)
        for spec in var_specs:
            j = spec['orig_idx']
            a_ij = -A_mat[i, j]
            if a_ij == 0.0:
                continue
            vtype = spec['type']
            if vtype == 'FIXED':
                rhs_val -= a_ij * spec['val']
            elif vtype in ('LOWER', 'BOX'):
                rhs_val -= a_ij * spec['shift']
                row_t[spec['trans_indices'][0]] += a_ij
            elif vtype == 'UPPER_ONLY':
                rhs_val -= a_ij * spec['shift']
                row_t[spec['trans_indices'][0]] -= a_ij
            elif vtype == 'FREE':
                row_t[spec['trans_indices'][0]] += a_ij
                row_t[spec['trans_indices'][1]] -= a_ij
        A_le_rows.append(row_t)
        b_le_rows.append(rhs_val)

    # From BOX variable upper bounds: t_k <= u_j - l_j
    box_upper_indices = []
    for spec in var_specs:
        if spec['type'] == 'BOX':
            k = spec['trans_indices'][0]
            row_t = np.zeros(n_trans, dtype=float)
            row_t[k] = 1.0
            box_upper_indices.append(len(A_le_rows))
            A_le_rows.append(row_t)
            b_le_rows.append(spec['range'])

    if n_trans == 0:
        A_eq = np.zeros((len(A_eq_rows), 0), dtype=float)
        A_le = np.zeros((len(A_le_rows), 0), dtype=float)
    else:
        A_eq = np.array(A_eq_rows, dtype=float).reshape((len(A_eq_rows), n_trans)) if A_eq_rows else np.zeros((0, n_trans), dtype=float)
        A_le = np.array(A_le_rows, dtype=float).reshape((len(A_le_rows), n_trans)) if A_le_rows else np.zeros((0, n_trans), dtype=float)
    b_eq = np.array(b_eq_rows, dtype=float) if b_eq_rows else np.zeros(0, dtype=float)
    b_le = np.array(b_le_rows, dtype=float) if b_le_rows else np.zeros(0, dtype=float)

    return TransformedModel(
        c=c_trans, A_eq=A_eq, b_eq=b_eq, A_le=A_le, b_le=b_le,
        var_specs=var_specs, n_orig=n, obj_constant=obj_constant,
        orig_eq_rows=orig_eq_rows, orig_le_rows=orig_le_rows, orig_ge_rows=orig_ge_rows
    )

def postsolve_primal(t, trans_model):
    """Recover original x from transformed solution t."""
    x = np.zeros(trans_model.n_orig, dtype=float)
    for spec in trans_model.var_specs:
        j = spec['orig_idx']
        vtype = spec['type']
        if vtype == 'FIXED':
            x[j] = spec['val']
        elif vtype in ('LOWER', 'BOX'):
            x[j] = spec['shift'] + t[spec['trans_indices'][0]]
        elif vtype == 'UPPER_ONLY':
            x[j] = spec['shift'] - t[spec['trans_indices'][0]]
        elif vtype == 'FREE':
            x[j] = t[spec['trans_indices'][0]] - t[spec['trans_indices'][1]]
    return x

def postsolve_direction(d_t, trans_model):
    """Recover original recession direction d from transformed direction d_t using strictly linear mapping.

    CRITICAL MATHEMATICAL DISTINCTION:
    For an affine solution transformation x = D t + s, primal points use the shift s:
        x_sol = D t_sol + s
    However, a recession direction d transforms purely through the LINEAR part D:
        d_x = D d_t
    The affine shift s MUST NOT be added to directions. Adding s would corrupt the
    direction whenever variables have non-zero lower bounds, upper bounds, or fixed values.

    Transformation rules for directions:
      - FIXED:       d_j = 0.0                      (fixed variable cannot change)
      - LOWER:       d_j = d_t[trans_idx]           (shift s_j = l_j is NOT applied)
      - BOX:         d_j = d_t[trans_idx]           (shift s_j = l_j is NOT applied)
      - UPPER_ONLY:  d_j = -d_t[trans_idx]          (shift s_j = u_j is NOT applied; x = u - t => dx = -dt)
      - FREE:        d_j = d_t[pos_idx] - d_t[neg_idx] (x = t+ - t- => dx = dt+ - dt-)
    """
    d = np.zeros(trans_model.n_orig, dtype=float)
    for spec in trans_model.var_specs:
        j = spec['orig_idx']
        vtype = spec['type']
        if vtype == 'FIXED':
            d[j] = 0.0
        elif vtype in ('LOWER', 'BOX'):
            d[j] = d_t[spec['trans_indices'][0]]
        elif vtype == 'UPPER_ONLY':
            d[j] = -d_t[spec['trans_indices'][0]]
        elif vtype == 'FREE':
            d[j] = d_t[spec['trans_indices'][0]] - d_t[spec['trans_indices'][1]]
    return d

postsolve_ray = postsolve_direction  # Backward-compatibility alias

def postsolve_dual(original_model, x, y_eq, y_le, trans_model, farkas=False):
    """Recover original model inequality dual multipliers z corresponding to original_model.inequalities().
    If farkas=True, objective gradient is zero (KKT stationarity condition G^T z == 0).
    """
    G, h, labels = original_model.inequalities()
    m_ineq = len(h)
    z = np.zeros(m_ineq, dtype=float)

    row_upper_idx = {}
    row_lower_idx = {}
    var_upper_idx = {}
    var_lower_idx = {}

    idx = 0
    for i in range(len(original_model.A)):
        if np.isfinite(original_model.row_upper[i]):
            row_upper_idx[i] = idx
            idx += 1
        if np.isfinite(original_model.row_lower[i]):
            row_lower_idx[i] = idx
            idx += 1
    for j in range(len(original_model.c)):
        if np.isfinite(original_model.upper[j]):
            var_upper_idx[j] = idx
            idx += 1
        if np.isfinite(original_model.lower[j]):
            var_lower_idx[j] = idx
            idx += 1

    # Map equality row duals:
    for k, i in enumerate(trans_model.orig_eq_rows):
        if k < len(y_eq):
            val = y_eq[k]
            if val > 0 and i in row_upper_idx:
                z[row_upper_idx[i]] = val
            elif val < 0 and i in row_lower_idx:
                z[row_lower_idx[i]] = -val

    # Map LE rows:
    le_count = len(trans_model.orig_le_rows)
    for k, i in enumerate(trans_model.orig_le_rows):
        if k < len(y_le):
            val = max(0.0, y_le[k])
            if i in row_upper_idx:
                z[row_upper_idx[i]] = val

    # Map GE rows:
    for k, i in enumerate(trans_model.orig_ge_rows):
        le_idx = le_count + k
        if le_idx < len(y_le):
            val = max(0.0, y_le[le_idx])
            if i in row_lower_idx:
                z[row_lower_idx[i]] = val

    # Map BOX variable upper bounds from A_le:
    box_start = le_count + len(trans_model.orig_ge_rows)
    box_row = 0
    for spec in trans_model.var_specs:
        if spec['type'] == 'BOX':
            if box_start + box_row < len(y_le):
                val = max(0.0, y_le[box_start + box_row])
                j = spec['orig_idx']
                if j in var_upper_idx:
                    z[var_upper_idx[j]] += val
            box_row += 1

    # Bound multipliers via stationarity:
    # Optimality: G^T z + c == 0
    # Infeasibility certificate (Farkas): G^T z == 0
    if farkas:
        r = G.T @ z
    else:
        r = original_model.c + G.T @ z

    for j in range(len(original_model.c)):
        if j in var_lower_idx and r[j] > 1e-12:
            z[var_lower_idx[j]] += r[j]
        elif j in var_upper_idx and r[j] < -1e-12:
            z[var_upper_idx[j]] += -r[j]

    return z

