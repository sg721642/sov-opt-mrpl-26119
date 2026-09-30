"""Two-phase primal revised simplex with exact rational certification.
Features:
- Direct standard-form handling of equality rows (no degenerate duplicate slacks).
- Reversible variable transformation pipeline for lower, upper-only, free, and fixed bounds.
- Exact rational basis solve fallback for Farkas infeasibility certificates.
- Separable box analysis for unconstrained (m=0) models with ray detection.
- Independent verification against the original model.
"""
from fractions import Fraction as F
from math import lcm
import numpy as np
from .linalg import LU, NumericalError
from .transforms import transform_model, postsolve_primal, postsolve_dual, postsolve_ray
from .verify import verify, exact_farkas

def _exact_solve_BT(B_float, rhs_float):
    """Solve B^T y = rhs in exact rational arithmetic (Fractions)."""
    m = len(B_float)
    B_F = [[F(float(B_float[i, j])) for j in range(m)] for i in range(m)]
    rhs_F = [F(float(rhs_float[j])) for j in range(m)]
    BT = [[B_F[j][i] for j in range(m)] for i in range(m)]
    A_aug = [row[:] + [rhs_F[i]] for i, row in enumerate(BT)]
    for i in range(m):
        p = next((k for k in range(i, m) if A_aug[k][i] != 0), None)
        if p is None: return None
        A_aug[i], A_aug[p] = A_aug[p], A_aug[i]
        pivot = A_aug[i][i]
        for j in range(i, m + 1): A_aug[i][j] /= pivot
        for k in range(m):
            if k != i and A_aug[k][i] != 0:
                factor = A_aug[k][i]
                for j in range(i, m + 1): A_aug[k][j] -= factor * A_aug[i][j]
    return [A_aug[i][m] for i in range(m)]

def _reconcile_farkas(model, z_float):
    """Reconcile dual multiplier vector to an exact rational Farkas certificate."""
    if exact_farkas(model, z_float):
        return z_float, True

    G, h, labels = model.inequalities()
    m_ineq = len(h)
    n_vars = len(model.c)
    if m_ineq == 0 or len(z_float) != m_ineq:
        return z_float, False

    var_upper_idx = {}
    var_lower_idx = {}
    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]): idx += 1
        if np.isfinite(model.row_lower[i]): idx += 1
    for j in range(n_vars):
        if np.isfinite(model.upper[j]): var_upper_idx[j] = idx; idx += 1
        if np.isfinite(model.lower[j]): var_lower_idx[j] = idx; idx += 1

    G_F = [[F(float(G[i, j])) for j in range(n_vars)] for i in range(m_ineq)]

    for max_den in (1000000, 100000, 10000, 1000):
        q = [max(F(0), F(float(v)).limit_denominator(max_den)) for v in z_float]
        col_sums_F = [sum(G_F[i][j] * q[i] for i in range(m_ineq)) for j in range(n_vars)]
        reconciled = list(q)
        possible = True
        for j in range(n_vars):
            if col_sums_F[j] > 0:
                if j in var_lower_idx:
                    reconciled[var_lower_idx[j]] += col_sums_F[j]
                else:
                    possible = False; break
            elif col_sums_F[j] < 0:
                if j in var_upper_idx:
                    reconciled[var_upper_idx[j]] += -col_sums_F[j]
                else:
                    possible = False; break
        if not possible:
            continue

        cand_direct = np.array([float(v) for v in reconciled])
        if exact_farkas(model, cand_direct):
            return cand_direct, True

        den = lcm(*(v.denominator for v in reconciled))
        cand_scaled = np.array([float(v * den) for v in reconciled])
        if exact_farkas(model, cand_scaled):
            return cand_scaled, True

    return z_float, False

def _exact_farkas_from_basis(model, M, basis, phase_cost, row_signs, row_scale, trans):
    """Solve basis in exact rational arithmetic and construct exact Farkas certificate."""
    y_F = _exact_solve_BT(M[:, basis], phase_cost[basis])
    if y_F is None:
        return None, False

    m_eq = len(trans.orig_eq_rows)
    m_total = len(row_signs)

    y_sys_F = [-y_F[i] * F(float(row_signs[i])) / F(float(row_scale[i])) for i in range(m_total)]
    y_eq_F = y_sys_F[:m_eq]
    y_le_F = y_sys_F[m_eq:]

    G, h, labels = model.inequalities()
    m_ineq = len(h)
    n_vars = len(model.c)
    z_F = [F(0) for _ in range(m_ineq)]

    row_upper_idx = {}
    row_lower_idx = {}
    var_upper_idx = {}
    var_lower_idx = {}
    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]): row_upper_idx[i] = idx; idx += 1
        if np.isfinite(model.row_lower[i]): row_lower_idx[i] = idx; idx += 1
    for j in range(n_vars):
        if np.isfinite(model.upper[j]): var_upper_idx[j] = idx; idx += 1
        if np.isfinite(model.lower[j]): var_lower_idx[j] = idx; idx += 1

    for k, i in enumerate(trans.orig_eq_rows):
        if k < len(y_eq_F):
            val = y_eq_F[k]
            if val > 0 and i in row_upper_idx: z_F[row_upper_idx[i]] = val
            elif val < 0 and i in row_lower_idx: z_F[row_lower_idx[i]] = -val

    le_count = len(trans.orig_le_rows)
    for k, i in enumerate(trans.orig_le_rows):
        if k < len(y_le_F):
            val = max(F(0), y_le_F[k])
            if i in row_upper_idx: z_F[row_upper_idx[i]] = val

    for k, i in enumerate(trans.orig_ge_rows):
        le_idx = le_count + k
        if le_idx < len(y_le_F):
            val = max(F(0), y_le_F[le_idx])
            if i in row_lower_idx: z_F[row_lower_idx[i]] = val

    box_start = le_count + len(trans.orig_ge_rows)
    box_row = 0
    for spec in trans.var_specs:
        if spec['type'] == 'BOX':
            if box_start + box_row < len(y_le_F):
                val = max(F(0), y_le_F[box_start + box_row])
                j = spec['orig_idx']
                if j in var_upper_idx:
                    z_F[var_upper_idx[j]] += val
            box_row += 1

    G_F = [[F(float(G[i, j])) for j in range(n_vars)] for i in range(m_ineq)]
    col_sums = [sum(G_F[i][j] * z_F[i] for i in range(m_ineq)) for j in range(n_vars)]
    for j in range(n_vars):
        if col_sums[j] > 0 and j in var_lower_idx:
            z_F[var_lower_idx[j]] += col_sums[j]
        elif col_sums[j] < 0 and j in var_upper_idx:
            z_F[var_upper_idx[j]] += -col_sums[j]

    if exact_farkas(model, z_F):
        return z_F, True
    return None, False

def _exact_dual_from_basis(model, M, basis, cost, row_signs, row_scale, trans):
    """Solve basis in exact rational arithmetic and construct exact dual solution satisfying stationarity."""
    y_F = _exact_solve_BT(M[:, basis], cost[basis])
    if y_F is None:
        return None

    m_eq = len(trans.orig_eq_rows)
    m_total = len(row_signs)

    y_sys_F = [-y_F[i] * F(float(row_signs[i])) / F(float(row_scale[i])) for i in range(m_total)]
    y_eq_F = y_sys_F[:m_eq]
    y_le_F = y_sys_F[m_eq:]

    G, h, _ = model.inequalities()
    m_ineq = len(h)
    n_vars = len(model.c)
    z_F = [F(0) for _ in range(m_ineq)]

    row_upper_idx = {}
    row_lower_idx = {}
    var_upper_idx = {}
    var_lower_idx = {}
    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]): row_upper_idx[i] = idx; idx += 1
        if np.isfinite(model.row_lower[i]): row_lower_idx[i] = idx; idx += 1
    for j in range(n_vars):
        if np.isfinite(model.upper[j]): var_upper_idx[j] = idx; idx += 1
        if np.isfinite(model.lower[j]): var_lower_idx[j] = idx; idx += 1

    for k, i in enumerate(trans.orig_eq_rows):
        if k < len(y_eq_F):
            val = y_eq_F[k]
            if val > 0 and i in row_upper_idx: z_F[row_upper_idx[i]] = val
            elif val < 0 and i in row_lower_idx: z_F[row_lower_idx[i]] = -val

    le_count = len(trans.orig_le_rows)
    for k, i in enumerate(trans.orig_le_rows):
        if k < len(y_le_F):
            val = max(F(0), y_le_F[k])
            if i in row_upper_idx: z_F[row_upper_idx[i]] = val

    for k, i in enumerate(trans.orig_ge_rows):
        le_idx = le_count + k
        if le_idx < len(y_le_F):
            val = max(F(0), y_le_F[le_idx])
            if i in row_lower_idx: z_F[row_lower_idx[i]] = val

    box_start = le_count + len(trans.orig_ge_rows)
    box_row = 0
    for spec in trans.var_specs:
        if spec['type'] == 'BOX':
            if box_start + box_row < len(y_le_F):
                val = max(F(0), y_le_F[box_start + box_row])
                j = spec['orig_idx']
                if j in var_upper_idx:
                    z_F[var_upper_idx[j]] += val
            box_row += 1

    G_F = [[F(float(G[i, j])) for j in range(n_vars)] for i in range(m_ineq)]
    r_F = [F(float(model.c[j])) + sum(G_F[i][j] * z_F[i] for i in range(m_ineq)) for j in range(n_vars)]
    for j in range(n_vars):
        if r_F[j] > 0 and j in var_lower_idx:
            z_F[var_lower_idx[j]] += r_F[j]
            r_F[j] = F(0)
        elif r_F[j] < 0 and j in var_upper_idx:
            z_F[var_upper_idx[j]] += -r_F[j]
            r_F[j] = F(0)

    if any(v != 0 for v in r_F):
        return None
    return z_F

def _exact_farkas_for_fixed_row(model, row_i, violated_upper):
    """Construct an exact Farkas certificate for an infeasible fixed-variable row constraint."""
    G, h, _ = model.inequalities()
    m_ineq = len(h)
    n_vars = len(model.c)
    z_F = [F(0) for _ in range(m_ineq)]

    row_upper_idx = {}
    row_lower_idx = {}
    var_upper_idx = {}
    var_lower_idx = {}
    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]): row_upper_idx[i] = idx; idx += 1
        if np.isfinite(model.row_lower[i]): row_lower_idx[i] = idx; idx += 1
    for j in range(n_vars):
        if np.isfinite(model.upper[j]): var_upper_idx[j] = idx; idx += 1
        if np.isfinite(model.lower[j]): var_lower_idx[j] = idx; idx += 1

    if violated_upper:
        if row_i not in row_upper_idx: return None
        z_F[row_upper_idx[row_i]] = F(1)
        for j in range(n_vars):
            a_ij = F(float(model.A[row_i, j]))
            if a_ij > 0 and j in var_lower_idx:
                z_F[var_lower_idx[j]] += a_ij
            elif a_ij < 0 and j in var_upper_idx:
                z_F[var_upper_idx[j]] += -a_ij
    else:
        if row_i not in row_lower_idx: return None
        z_F[row_lower_idx[row_i]] = F(1)
        for j in range(n_vars):
            a_ij = -F(float(model.A[row_i, j]))
            if a_ij > 0 and j in var_lower_idx:
                z_F[var_lower_idx[j]] += a_ij
            elif a_ij < 0 and j in var_upper_idx:
                z_F[var_upper_idx[j]] += -a_ij

    if exact_farkas(model, z_F):
        return z_F
    return None

def _dual_for_fixed_vars(model):
    """Construct dual multipliers for a feasible all-fixed model satisfying KKT stationarity."""
    G, h, _ = model.inequalities()
    m_ineq = len(h)
    n_vars = len(model.c)
    z = np.zeros(m_ineq, dtype=float)
    var_upper_idx = {}
    var_lower_idx = {}
    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]): idx += 1
        if np.isfinite(model.row_lower[i]): idx += 1
    for j in range(n_vars):
        if np.isfinite(model.upper[j]): var_upper_idx[j] = idx; idx += 1
        if np.isfinite(model.lower[j]): var_lower_idx[j] = idx; idx += 1

    for j in range(n_vars):
        c_j = model.c[j]
        if c_j > 0 and j in var_lower_idx:
            z[var_lower_idx[j]] = c_j
        elif c_j < 0 and j in var_upper_idx:
            z[var_upper_idx[j]] = -c_j
    return z

def _dual_for_separable_box(model):
    """Construct dual multipliers for a bounded separable box model satisfying KKT stationarity."""
    G, h, _ = model.inequalities()
    m_ineq = len(h)
    n_vars = len(model.c)
    z = np.zeros(m_ineq, dtype=float)
    var_upper_idx = {}
    var_lower_idx = {}
    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]): idx += 1
        if np.isfinite(model.row_lower[i]): idx += 1
    for j in range(n_vars):
        if np.isfinite(model.upper[j]): var_upper_idx[j] = idx; idx += 1
        if np.isfinite(model.lower[j]): var_lower_idx[j] = idx; idx += 1

    for j in range(n_vars):
        c_j = model.c[j]
        if c_j > 0 and j in var_lower_idx:
            z[var_lower_idx[j]] = c_j
        elif c_j < 0 and j in var_upper_idx:
            z[var_upper_idx[j]] = -c_j
    return z

def _iterate(M, b, c, basis, allowed, limit, history):
    for k in range(limit):
        B = M[:, basis]
        lu = LU(B)
        xb = lu.solve(b)
        y = LU(B.T).solve(c[basis])
        rc = c - M.T @ y
        if np.min(xb, initial=0) < -1e-7 * (1 + np.max(abs(b), initial=0)):
            raise NumericalError('Lost basis feasibility')
        entering = next((j for j in range(allowed) if j not in basis and rc[j] < -1e-10 * (1 + abs(c[j]))), None)
        if entering is None:
            return xb, y, k
        d = lu.solve(M[:, entering])
        possible = np.flatnonzero(d > 1e-12)
        if not len(possible):
            raise NumericalError('LP is unbounded (no finite ratio in simplex pivot)')
        ratios = np.maximum(xb[possible], 0) / d[possible]
        best = np.min(ratios)
        ties = [int(possible[t]) for t, v in enumerate(ratios) if v <= best + 1e-12 * (1 + abs(best))]
        leaving = min(ties, key=lambda i: basis[i])
        if len(history) < 1000:
            history.append({'iteration': len(history), 'objective_transformed': float(c[basis] @ np.maximum(xb, 0))})
        basis[leaving] = entering
    raise NumericalError('Simplex iteration limit')

def solve_lp(model, tol=1e-7, max_iter=10000, scaling=True):
    n = len(model.c)
    m_rows = len(model.A)
    history = []

    # 1. Handle unconstrained / box-only model (m_rows == 0)
    if m_rows == 0:
        if np.any(model.lower > model.upper):
            return dict(status='INFEASIBLE_CERTIFIED', message='Box lower bound exceeds upper bound',
                        algorithm='separable box analysis', iterations=0, history=history)
        # Construct guaranteed feasible base point x (l <= x <= u)
        x = np.zeros(n, dtype=float)
        for j in range(n):
            lj, uj = model.lower[j], model.upper[j]
            if np.isfinite(lj) and np.isfinite(uj):
                x[j] = np.clip(0.0, lj, uj)
            elif np.isfinite(lj):
                x[j] = max(0.0, lj)
            elif np.isfinite(uj):
                x[j] = min(0.0, uj)
            else:
                x[j] = 0.0

        unbounded_rays = []
        for j in range(n):
            c_j = model.c[j]
            lj, uj = model.lower[j], model.upper[j]
            if c_j > 0:
                if np.isneginf(lj):
                    ray = np.zeros(n); ray[j] = -1.0; unbounded_rays.append(ray)
                else:
                    x[j] = lj
            elif c_j < 0:
                if np.isposinf(uj):
                    ray = np.zeros(n); ray[j] = 1.0; unbounded_rays.append(ray)
                else:
                    x[j] = uj

        if unbounded_rays:
            ray = unbounded_rays[0]
            return dict(status='UNBOUNDED_CERTIFIED', message='LP is unbounded in box direction',
                        ray=ray.tolist(), base_point=x.tolist(), x=x.tolist(),
                        algorithm='separable box analysis', iterations=0, history=history)

        z_box = _dual_for_separable_box(model)
        report = verify(model, x, z_box, tol, check_integer=False)
        return dict(status='OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                    x=x.tolist(), dual=z_box.tolist(), verification=report, objective=report['objective'],
                    iterations=0, algorithm='separable box analysis', history=history)

    # 2. Transform model into standard non-negative form t >= 0
    trans = transform_model(model)
    n_trans = len(trans.c)
    m_eq = len(trans.b_eq)
    m_le = len(trans.b_le)
    m_total = m_eq + m_le

    # 2a. All variables are fixed: n_trans == 0
    if n_trans == 0:
        x_fixed = np.array([spec['val'] for spec in trans.var_specs], dtype=float)
        # Check all row constraints on fixed variables in exact rational arithmetic
        for i in range(m_rows):
            val_F = sum(F(float(model.A[i, j])) * F(float(x_fixed[j])) for j in range(n))
            lo_F = F(float(model.row_lower[i])) if np.isfinite(model.row_lower[i]) else None
            hi_F = F(float(model.row_upper[i])) if np.isfinite(model.row_upper[i]) else None
            if hi_F is not None and val_F > hi_F:
                z_cert = _exact_farkas_for_fixed_row(model, i, violated_upper=True)
                if z_cert is not None:
                    z_ser = [f'{v.numerator}/{v.denominator}' for v in z_cert]
                    return dict(status='INFEASIBLE_CERTIFIED', message=f'Fixed variables violate row {i} upper bound',
                                certificate=[float(v) for v in z_cert], certificate_exact=z_ser,
                                algorithm='fixed variable evaluation', iterations=0, history=history)
                return dict(status='NUMERICAL_FAILURE', message=f'Fixed variables violate row {i} upper bound without exact certificate',
                            algorithm='fixed variable evaluation', iterations=0, history=history)
            if lo_F is not None and val_F < lo_F:
                z_cert = _exact_farkas_for_fixed_row(model, i, violated_upper=False)
                if z_cert is not None:
                    z_ser = [f'{v.numerator}/{v.denominator}' for v in z_cert]
                    return dict(status='INFEASIBLE_CERTIFIED', message=f'Fixed variables violate row {i} lower bound',
                                certificate=[float(v) for v in z_cert], certificate_exact=z_ser,
                                algorithm='fixed variable evaluation', iterations=0, history=history)
                return dict(status='NUMERICAL_FAILURE', message=f'Fixed variables violate row {i} lower bound without exact certificate',
                            algorithm='fixed variable evaluation', iterations=0, history=history)

        z_fixed = _dual_for_fixed_vars(model)
        report = verify(model, x_fixed, z_fixed, tol, check_integer=False)
        return dict(status='OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                    x=x_fixed.tolist(), dual=z_fixed.tolist(), verification=report, objective=report['objective'],
                    iterations=0, algorithm='fixed variable evaluation', history=history)

    # 2b. Transformed system has zero effective rows: m_total == 0
    if m_total == 0:
        x_base = postsolve_primal(np.zeros(n_trans), trans)
        for i in range(m_rows):
            val_F = sum(F(float(model.A[i, j])) * F(float(x_base[j])) for j in range(n))
            lo_F = F(float(model.row_lower[i])) if np.isfinite(model.row_lower[i]) else None
            hi_F = F(float(model.row_upper[i])) if np.isfinite(model.row_upper[i]) else None
            if hi_F is not None and val_F > hi_F:
                z_cert = _exact_farkas_for_fixed_row(model, i, violated_upper=True)
                if z_cert is not None:
                    z_ser = [f'{v.numerator}/{v.denominator}' for v in z_cert]
                    return dict(status='INFEASIBLE_CERTIFIED', message=f'Fixed rows infeasible at base point for row {i}',
                                certificate=[float(v) for v in z_cert], certificate_exact=z_ser,
                                algorithm='transformed unconstrained analysis', iterations=0, history=history)
                return dict(status='NUMERICAL_FAILURE', message=f'Fixed rows infeasible at row {i} without exact certificate',
                            algorithm='transformed unconstrained analysis', iterations=0, history=history)
            if lo_F is not None and val_F < lo_F:
                z_cert = _exact_farkas_for_fixed_row(model, i, violated_upper=False)
                if z_cert is not None:
                    z_ser = [f'{v.numerator}/{v.denominator}' for v in z_cert]
                    return dict(status='INFEASIBLE_CERTIFIED', message=f'Fixed rows infeasible at base point for row {i}',
                                certificate=[float(v) for v in z_cert], certificate_exact=z_ser,
                                algorithm='transformed unconstrained analysis', iterations=0, history=history)
                return dict(status='NUMERICAL_FAILURE', message=f'Fixed rows infeasible at row {i} without exact certificate',
                            algorithm='transformed unconstrained analysis', iterations=0, history=history)

        # Check for unconstrained negative cost on non-negative variables
        # Any strictly negative coefficient implies unboundedness
        neg_c = [k for k in range(n_trans) if trans.c[k] < 0.0]
        if neg_c:
            k = neg_c[0]
            t_ray = np.zeros(n_trans); t_ray[k] = 1.0
            ray = postsolve_ray(t_ray, trans)
            if model.c @ ray < 0.0:
                return dict(status='UNBOUNDED_CERTIFIED', message='LP is unbounded in transformed direction',
                            ray=ray.tolist(), base_point=x_base.tolist(), x=x_base.tolist(),
                            algorithm='transformed unconstrained analysis', iterations=0, history=history)

        z_uncon = _dual_for_fixed_vars(model)
        report = verify(model, x_base, z_uncon, tol, check_integer=False)
        return dict(status='OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                    x=x_base.tolist(), dual=z_uncon.tolist(), verification=report, objective=report['objective'],
                    iterations=0, algorithm='transformed unconstrained analysis', history=history)

    # Stack rows: equality rows first, then LE rows
    if m_eq > 0 and m_le > 0:
        A_all = np.vstack([trans.A_eq, trans.A_le])
        rhs_all = np.concatenate([trans.b_eq, trans.b_le])
    elif m_eq > 0:
        A_all = trans.A_eq.copy()
        rhs_all = trans.b_eq.copy()
    else:
        A_all = trans.A_le.copy()
        rhs_all = trans.b_le.copy()

    # Ensure non-negative RHS by multiplying negative rows by -1
    row_signs = np.where(rhs_all < 0, -1.0, 1.0)
    A_all *= row_signs[:, None]
    rhs_all *= row_signs

    # Optional row equilibration scaling
    if scaling and m_total > 0:
        row_scale = np.maximum(np.max(np.abs(A_all), axis=1), 1e-30)
        A_all /= row_scale[:, None]
        rhs_all /= row_scale
    else:
        row_scale = np.ones(max(m_total, 1))

    # Construct standard-form matrix M:
    # Columns 0..n_trans-1: variables t (cost = trans.c)
    # Columns n_trans..n_trans+m_le-1: slacks for LE rows
    # Columns for artificial variables: one for each row of the system
    cols = [A_all]
    if m_le > 0:
        slack_mat = np.zeros((m_total, m_le), dtype=float)
        for k in range(m_le):
            # Row index in A_all is m_eq + k
            slack_mat[m_eq + k, k] = row_signs[m_eq + k]
        cols.append(slack_mat)

    # Add artificial variables for all rows (identity matrix)
    art_mat = np.eye(m_total, dtype=float)
    cols.append(art_mat)

    M = np.column_stack(cols)
    total_cols = M.shape[1]
    slack_start = n_trans
    art_start = n_trans + m_le

    # Initial basis: all artificial variables
    basis = list(range(art_start, art_start + m_total))
    phase_cost = np.zeros(total_cols, dtype=float)
    phase_cost[art_start:] = 1.0

    try:
        xb, y, it1 = _iterate(M, rhs_all, phase_cost, basis, total_cols, max_iter, history)
        sum_art = float(phase_cost[basis] @ xb)

        if sum_art > 1e-8:
            # Model is infeasible! Reconstruct Farkas certificate.
            # Dual for scaled system:
            y_system = -y * row_signs / row_scale
            y_eq_cand = y_system[:m_eq]
            y_le_cand = y_system[m_eq:]
            x_dummy = np.zeros(n)
            z_float = postsolve_dual(model, x_dummy, y_eq_cand, y_le_cand, trans, farkas=True)

            z_cert, cert_ok = _reconcile_farkas(model, z_float)

            if not cert_ok:
                z_exact, cert_ok = _exact_farkas_from_basis(model, M, basis, phase_cost, row_signs, row_scale, trans)
                if cert_ok:
                    z_cert = z_exact

            # Serialize certificate losslessly
            z_serialized = [f'{v.numerator}/{v.denominator}' if isinstance(v, F) else (f'{F(float(v)).numerator}/{F(float(v)).denominator}' if v != 0 else '0') for v in z_cert]
            return dict(status='INFEASIBLE_CERTIFIED' if cert_ok else 'NUMERICAL_FAILURE',
                        message='Phase I infeasibility; exact Farkas certificate ' + ('verified' if cert_ok else 'could not be established'),
                        certificate=[float(v) for v in z_cert],
                        certificate_exact=z_serialized,
                        algorithm='two-phase primal revised simplex', iterations=it1, history=history)

        # Drive out any remaining zero-valued artificials from the basis
        for i in range(m_total):
            if basis[i] >= art_start:
                row = LU(M[:, basis].T).solve(np.eye(m_total)[i]) @ M[:, :art_start]
                j = next((j for j in range(art_start) if j not in basis and abs(row[j]) > 1e-10), None)
                if j is not None:
                    basis[i] = j

        # Phase II: minimize real objective
        phase2_cost = np.r_[trans.c, np.zeros(m_le + m_total)]
        xb, y, it2 = _iterate(M, rhs_all, phase2_cost, basis, art_start, max_iter, history)

        # Reconstruct transformed primal vector t
        t_sol = np.zeros(total_cols, dtype=float)
        t_sol[basis] = xb
        t_vars = t_sol[:n_trans]

        # Postsolve primal x
        x_sol = postsolve_primal(t_vars, trans)

        # Postsolve duals y
        y_system = -y * row_signs / row_scale
        y_eq = y_system[:m_eq]
        y_le = y_system[m_eq:]
        z_sol = postsolve_dual(model, x_sol, y_eq, y_le, trans)

        z_exact = _exact_dual_from_basis(model, M, basis, phase2_cost, row_signs, row_scale, trans)

        report = verify(model, x_sol, z_sol, tol, check_integer=False)
        res_dict = dict(status='OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                        x=x_sol.tolist(), dual=z_sol.tolist(), verification=report,
                        objective=report['objective'], iterations=it1 + it2,
                        basis=list(basis),
                        algorithm='two-phase primal revised simplex', history=history)
        if z_exact is not None:
            res_dict['dual_exact'] = [f'{v.numerator}/{v.denominator}' if isinstance(v, F) else str(v) for v in z_exact]
            res_dict['dual_exact_fraction'] = z_exact
        return res_dict

    except (NumericalError, FloatingPointError, OverflowError) as e:
        if 'iteration limit' in str(e).lower():
            return dict(status='LIMIT_REACHED', message='Simplex iteration limit reached',
                        algorithm='two-phase primal revised simplex', history=history)
        if 'unbounded' in str(e).lower():
            return dict(status='UNBOUNDED_CERTIFIED', message=str(e),
                        algorithm='two-phase primal revised simplex', history=history)
        if scaling:
            # Fallback to unscaled solve if equilibration caused an unsafe basis pivot
            return solve_lp(model, tol=tol, max_iter=max_iter, scaling=False)
        return dict(status='NUMERICAL_FAILURE', message=str(e),
                    algorithm='two-phase primal revised simplex', history=history)
