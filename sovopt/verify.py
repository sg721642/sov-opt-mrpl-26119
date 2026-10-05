"""Checks original model independently of solver stopping rules.
KKT checks are numerical, NOT formal interval/exact optimality certificates.
Exact rational LP lower bounds and Farkas checks use the parsed IEEE 754
binary64 floating-point coefficients represented losslessly as Fractions.

Objective recovery:
- For minimization: c^T x + 1/2 x^T Q x + obj_offset
- For maximization: -(c^T x + 1/2 x^T Q x) + obj_offset (where c and Q are internal minimization coefficients)
"""
from fractions import Fraction as F
import math
import numpy as np

def _reported_objective(model, x, Q=None):
    """Compute objective in the original problem sense (accounting for maximization and offset)."""
    xld = np.asarray(x, np.longdouble)
    cld = model.c.astype(np.longdouble)
    if Q is None:
        raw = float(cld @ xld)
    elif hasattr(Q, 'dot'):
        raw = float(cld @ xld + xld @ Q.dot(xld) / 2.0)
    else:
        Q_use = np.asarray(Q, dtype=np.longdouble)
        raw = float(cld @ xld + xld @ Q_use @ xld / 2.0)
    if model.maximize:
        return -raw + model.obj_offset
    return raw + model.obj_offset

def verify(model, x, z=None, tol=1e-7, check_integer=True):
    x = np.asarray(x, np.longdouble)
    from .sparse import CSRMatrix
    is_sparse = isinstance(model.A, CSRMatrix)
    if is_sparse:
        G, h, _ = model.sparse_inequalities(bounds=True)
    else:
        G, h, _ = model.inequalities()
        G = G.astype(np.longdouble)
    h = h.astype(np.longdouble)

    if x.shape != model.c.shape or not np.isfinite(x).all():
        return {
            'feasible': False,
            'kkt_passed': False,
            'reason': 'nonfinite or invalid candidate',
            'primal_feasibility_passed': False,
            'dual_feasibility_passed': False,
            'stationarity_passed': False,
            'complementarity_passed': False,
        }

    # Verify variable bounds explicitly (including infinite ones)
    lb_viol = np.maximum(model.lower - np.asarray(x, float), 0.0)
    ub_viol = np.maximum(np.asarray(x, float) - model.upper, 0.0)
    box_viol = float(max(lb_viol.max() if len(lb_viol) else 0.0, ub_viol.max() if len(ub_viol) else 0.0))

    if len(h) > 0:
        if is_sparse:
            activity = G.dot(x)
            violation = np.maximum(activity - h, 0.0)
            scale = 1.0 + np.abs(h) + G.abs_dot(np.abs(x))
        else:
            activity = G @ x
            violation = np.maximum(activity - h, 0.0)
            scale = 1.0 + np.abs(h) + np.abs(G) @ np.abs(x)
        primal = float(np.max(violation / scale, initial=0.0))
        absolute = float(np.max(violation, initial=0.0))
    else:
        primal = 0.0
        absolute = 0.0

    primal = max(primal, box_viol / (1.0 + np.max(np.abs(model.upper[np.isfinite(model.upper)]), initial=1.0)))
    absolute = max(absolute, box_viol)

    integ = float(max((abs(x[j] - np.rint(x[j])) for j in model.integer), default=0.0))
    if model.Q is None:
        grad = model.c.astype(np.longdouble)
        obj = _reported_objective(model, x, None)
    elif hasattr(model.Q, 'dot'):
        grad = model.Q.dot(x).astype(np.longdouble) + model.c
        obj = _reported_objective(model, x, model.Q)
    else:
        Q_arr = np.asarray(model.Q, dtype=np.longdouble)
        grad = Q_arr @ x + model.c
        obj = _reported_objective(model, x, Q_arr)

    report = dict(
        feasible=primal <= tol and (not check_integer or integ <= tol),
        objective=obj,
        primal_residual=primal,
        absolute_primal_violation=absolute,
        integrality_residual=integ,
        kkt_passed=False,
        precision_bits=int(np.finfo(np.longdouble).nmant + 1),
        certification='floating-point residual checks'
    )

    if z is not None and len(h) > 0:
        z = np.asarray(z, np.longdouble)
        if z.shape != h.shape or not np.isfinite(z).all():
            report.update(
                primal_feasibility_passed=bool(report['feasible']),
                dual_feasibility_passed=False,
                stationarity_passed=False,
                complementarity_passed=False,
            )
            return report
        if model.Q is None:
            raw_obj = float(model.c.astype(np.longdouble) @ x)
        elif hasattr(model.Q, 'dot'):
            raw_obj = float(model.c.astype(np.longdouble) @ x + x @ model.Q.dot(x) / 2.0)
        else:
            raw_obj = float(model.c.astype(np.longdouble) @ x + x @ Q_arr @ x / 2.0)
        scale_obj = 1.0 + abs(raw_obj)
        dual = float(np.max(np.maximum(-z, 0.0), initial=0.0))
        if is_sparse:
            abs_GTz = G.abs_transpose_dot(np.abs(z))
            stat_denom = 1.0 + np.max(np.abs(grad)) + np.max(abs_GTz)
            station = float(np.max(np.abs(grad + G.transpose_dot(z))) / stat_denom)
        else:
            stat_denom = 1.0 + np.max(np.abs(grad)) + np.max(np.abs(G.T) @ np.abs(z))
            station = float(np.max(np.abs(grad + G.T @ z)) / stat_denom)
        comp_denom = scale_obj + np.max(np.abs(z * h))
        comp = float(np.max(np.abs(z * (activity - h))) / comp_denom)
        gap_denom = scale_obj + abs(float(z @ h))
        gap = float(abs(z @ (h - activity)) / gap_denom)
        primal_ok = bool(report['feasible'])
        dual_ok = bool(dual <= tol)
        station_ok = bool(station <= tol)
        comp_ok = bool(comp <= tol and gap <= tol)
        kkt_ok = primal_ok and dual_ok and station_ok and comp_ok
        report.update(
            dual_residual=station,
            dual_sign_violation=dual,
            complementarity=comp,
            relative_duality_gap=gap,
            kkt_passed=kkt_ok,
            kkt_evaluated=True,
            kkt_status='FULL_KKT_PASSED' if kkt_ok else 'FULL_KKT_FAILED',
            primal_feasibility_passed=primal_ok,
            dual_feasibility_passed=dual_ok,
            stationarity_passed=station_ok,
            complementarity_passed=comp_ok,
        )
    elif len(h) == 0:
        # No inequality constraints: stationarity requires grad == 0 (or bounded box stationarity)
        grad_norm = float(np.max(np.abs(grad)))
        primal_ok = bool(report['feasible'])
        station_ok = bool(grad_norm <= tol)
        kkt_ok = primal_ok and station_ok
        report.update(
            dual_residual=grad_norm / (1.0 + grad_norm),
            dual_sign_violation=0.0,
            complementarity=0.0,
            relative_duality_gap=0.0,
            kkt_passed=kkt_ok,
            kkt_evaluated=True,
            kkt_status='FULL_KKT_PASSED' if kkt_ok else 'FULL_KKT_FAILED',
            primal_feasibility_passed=primal_ok,
            dual_feasibility_passed=True,
            stationarity_passed=station_ok,
            complementarity_passed=True,
        )
    else:
        report.update(
            kkt_evaluated=False,
            kkt_status='PRIMAL_FEASIBILITY_ONLY',
            primal_feasibility_passed=bool(report['feasible']),
            dual_feasibility_passed=False,
            stationarity_passed=False,
            complementarity_passed=False,
        )

    return report

def safe_lower_bound(model, z):
    """Exact rational Lagrangian lower bound over variable box, LP only.
    G contains ALL constraints. Every non-negative z is dual admissible.
    Returns None if any nonzero reduced cost has an unbounded minimizing direction.
    Zero reduced cost contributes strictly 0 regardless of bounds.
    """
    G, h, _ = model.inequalities()
    if len(h) == 0 or z is None:
        return None
    z_frac = [max(F(0), v) if isinstance(v, F) else F(float(max(0.0, v))) for v in z]
    r = [F(float(v)) for v in model.c]
    b = F(0)

    for i in range(len(h)):
        b -= F(float(h[i])) * z_frac[i]
        for j in np.flatnonzero(G[i]):
            r[j] += F(float(G[i, j])) * z_frac[i]

    for j, v in enumerate(r):
        if v > 0:
            if np.isneginf(model.lower[j]):
                return None  # unbounded below with positive coeff
            b += v * F(float(model.lower[j]))
        elif v < 0:
            if np.isposinf(model.upper[j]):
                return None  # unbounded above with negative coeff
            b += v * F(float(model.upper[j]))
        # v == 0: strictly 0 contribution, independent of variable bounds

    return b

def downward_float(value):
    """Convert an exact Fraction to float rounded conservatively downward."""
    if value is None:
        return None
    if value == -math.inf:
        return -math.inf
    if value == math.inf:
        return math.inf
    f = float(value)
    if F(f) > value:
        f = float(np.nextafter(f, -np.inf))
    return f

def upward_float(value):
    """Convert an exact Fraction to float rounded conservatively upward."""
    if value is None:
        return None
    if value == -math.inf:
        return -math.inf
    if value == math.inf:
        return math.inf
    f = float(value)
    if F(f) < value:
        f = float(np.nextafter(f, np.inf))
    return f

def exact_farkas(model, z):
    """Verify exact binary-rational Farkas certificate G^T z == 0, h^T z < 0, z >= 0."""
    G, h, _ = model.inequalities()
    if len(h) == 0 or len(z) != len(h):
        return False
    z_F = [v if isinstance(v, F) else F(str(v)) if isinstance(v, str) else F(float(v)) for v in z]
    if any(v < 0 for v in z_F):
        return False
    for j in range(len(model.c)):
        col_sum = sum((F(float(G[i, j])) * z_F[i] for i in range(len(h))), F(0))
        if col_sum != 0:
            return False
    h_sum = sum((F(float(h[i])) * z_F[i] for i in range(len(h))), F(0))
    return h_sum < 0


def verify_unbounded_certificate(model, x0, d, tol=1e-7):
    """Verify a complete unbounded certificate (x0, d) against the original model.

    An UNBOUNDED_CERTIFIED result is justified iff BOTH:
      (A) x0 is a feasible base point satisfying all original model constraints, AND
      (B) d is a valid recession direction satisfying all original row and bound conditions,
          with an improving objective direction in the original problem sense.

    This function verifies all conditions independently from the solver and is the
    sole gate for returning UNBOUNDED_CERTIFIED from any code path.

    Objective sense:
    - model.c is stored in INTERNAL CANONICAL (minimization) form.
    - If model.maximize is True, the original objective was maximisation; c was negated
      before storage. An improving INTERNAL direction has c^T d < 0 (internal minimises
      a larger-and-larger negated value, meaning the original maximisation objective
      goes to +inf). We verify c^T d < 0 in BOTH senses because the stored c is always
      the internal min coefficient.

    Row recession conditions (for each row i):
      Equality (row_lower[i] == row_upper[i] and both finite): A[i] @ d == 0
      Upper bound only (finite row_upper[i]): A[i] @ d <= 0
      Lower bound only (finite row_lower[i]): A[i] @ d >= 0
      No finite bound: unrestricted

    Variable bound directions (for each j):
      Both bounds finite:    d[j] == 0   (bounded variable; no recession direction)
      Lower bound only:      d[j] >= 0
      Upper bound only:      d[j] <= 0
      Free variable:         unrestricted

    Returns a dict:
      verified:               bool — True iff BOTH base_feasible and ray_verified
      base_feasible:          bool — x0 satisfies all constraints within tol
      ray_verified:           bool — d is a valid recession direction within tol
      base_primal_residual:   float — worst scaled constraint violation at x0
      objective_direction:    float — c^T d (internal; < 0 means improving)
      max_row_direction_violation: float — worst row recession violation
      max_bound_direction_violation: float — worst variable bound direction violation
      message:                str — human-readable summary
    """
    n = len(model.c)

    # --- Part A: base point feasibility ---
    if x0 is None:
        base_report = dict(base_feasible=False, base_primal_residual=float('inf'),
                           message_base='no base point provided')
    else:
        x0 = np.asarray(x0, dtype=float)
        if x0.shape != (n,) or not np.isfinite(x0).all():
            base_report = dict(base_feasible=False, base_primal_residual=float('inf'),
                               message_base='base point is nonfinite or wrong dimension')
        else:
            # Check variable bounds
            lb_viol = np.maximum(model.lower - x0, 0.0)
            ub_viol = np.maximum(x0 - model.upper, 0.0)
            box_abs = float(max(lb_viol.max(), ub_viol.max()))

            # Check row constraints
            m_rows = len(model.A)
            row_viols_abs = []
            row_viols_scaled = []
            for i in range(m_rows):
                ai_x = float(model.A[i] @ x0)
                rl, ru = model.row_lower[i], model.row_upper[i]
                if np.isfinite(ru):
                    v = max(0.0, ai_x - float(ru))
                    scale = 1.0 + abs(float(ru)) + float(np.abs(model.A[i]) @ np.abs(x0))
                    row_viols_abs.append(v)
                    row_viols_scaled.append(v / scale)
                if np.isfinite(rl):
                    v = max(0.0, float(rl) - ai_x)
                    scale = 1.0 + abs(float(rl)) + float(np.abs(model.A[i]) @ np.abs(x0))
                    row_viols_abs.append(v)
                    row_viols_scaled.append(v / scale)

            bound_scale = 1.0 + float(np.max(np.abs(model.upper[np.isfinite(model.upper)]), initial=1.0))
            primal_res_scaled = max(max(row_viols_scaled, default=0.0),
                                    box_abs / bound_scale)
            base_feasible = primal_res_scaled <= tol
            base_report = dict(base_feasible=base_feasible,
                               base_primal_residual=primal_res_scaled,
                               message_base='base point feasible' if base_feasible else
                                            f'base point infeasible (scaled residual {primal_res_scaled:.4g})')

    # --- Part B: direction verification ---
    d = np.asarray(d, dtype=float)
    if d.shape != (n,) or not np.isfinite(d).all():
        dir_report = dict(ray_verified=False,
                          objective_direction=None,
                          max_row_direction_violation=float('inf'),
                          max_bound_direction_violation=float('inf'),
                          message_dir='recession direction is nonfinite or wrong dimension')
    else:
        # B1: Improving objective direction
        # model.c is always internal minimization form. An improving direction has c^T d < 0.
        # For maximisation models: c was negated before storage, so c^T d < 0 still means
        # the stored min objective decreases, which equals the original max objective
        # going to +inf. We always check c^T d < 0.
        obj_dir = float(model.c @ d)
        c_scale = tol * (1.0 + float(np.max(np.abs(model.c))) * float(np.max(np.abs(d), initial=1.0)))
        obj_ok = obj_dir < -c_scale

        # B2: Row recession
        m_rows = len(model.A)
        row_dir_viols = []
        for i in range(m_rows):
            ad = float(model.A[i] @ d)
            rtol = tol * (1.0 + float(np.abs(model.A[i]) @ np.abs(d)))
            rl, ru = model.row_lower[i], model.row_upper[i]
            if np.isfinite(rl) and np.isfinite(ru):
                # Finite lower AND finite upper (equality or ranged row): A_i @ d must == 0
                row_dir_viols.append(abs(ad) - rtol)
            elif np.isfinite(ru):
                # Finite upper only: A_i @ d <= 0
                row_dir_viols.append(ad - rtol)
            elif np.isfinite(rl):
                # Finite lower only: A_i @ d >= 0
                row_dir_viols.append(-ad - rtol)
            # No finite bounds: unrestricted

        max_row_viol = float(max(row_dir_viols, default=0.0))
        row_ok = max_row_viol <= 0.0

        # B3: Variable bound directions
        bound_dir_viols = []
        for j in range(n):
            lj, uj = model.lower[j], model.upper[j]
            fin_lo = np.isfinite(lj)
            fin_hi = np.isfinite(uj)
            if fin_lo and fin_hi:
                bound_dir_viols.append(abs(d[j]) - tol)  # d[j] must be == 0
            elif fin_lo:
                bound_dir_viols.append(-d[j] - tol)       # d[j] must be >= 0
            elif fin_hi:
                bound_dir_viols.append(d[j] - tol)        # d[j] must be <= 0
            # free: no constraint

        max_bound_viol = float(max(bound_dir_viols, default=0.0))
        bound_ok = max_bound_viol <= 0.0

        ray_verified = obj_ok and row_ok and bound_ok
        msg_parts = []
        orig_obj_dir = float(-obj_dir if model.maximize else obj_dir)
        if not obj_ok:
            sense = 'max (internal neg-c)' if model.maximize else 'min'
            msg_parts.append(f'c^T d = {obj_dir:.4g} not improving for {sense}')
        if not row_ok:
            msg_parts.append(f'row recession violated ({max_row_viol:.4g})')
        if not bound_ok:
            msg_parts.append(f'bound direction violated ({max_bound_viol:.4g})')

        dir_report = dict(
            ray_verified=ray_verified,
            objective_direction=obj_dir,
            original_objective_direction=orig_obj_dir,
            max_row_direction_violation=max_row_viol,
            max_bound_direction_violation=max_bound_viol,
            message_dir='; '.join(msg_parts) if msg_parts else
                        'direction verified as valid recession direction',
        )

    # --- Combine ---
    base_feasible = base_report['base_feasible']
    ray_verified = dir_report['ray_verified']
    verified = base_feasible and ray_verified

    msg = []
    if not base_feasible:
        msg.append(base_report['message_base'])
    if not ray_verified:
        msg.append(dir_report['message_dir'])
    if verified:
        msg.append('unbounded certificate (x0, d) fully verified')

    return dict(
        verified=verified,
        base_feasible=base_feasible,
        ray_verified=ray_verified,
        base_primal_residual=base_report['base_primal_residual'],
        objective_direction=dir_report['objective_direction'],
        obj_direction=dir_report['objective_direction'],
        original_objective_direction=dir_report.get('original_objective_direction'),
        max_row_direction_violation=dir_report['max_row_direction_violation'],
        max_bound_direction_violation=dir_report['max_bound_direction_violation'],
        max_row_violation=dir_report['max_row_direction_violation'],
        max_bound_violation=dir_report['max_bound_direction_violation'],
        message='; '.join(msg),
    )


def verify_unbounded_ray(model, d, x0=None, tol=1e-7):
    """Direction-only verification subcheck (backward compatibility wrapper).

    Calls verify_unbounded_certificate(model, x0, d, tol).

    If x0 is None, base point feasibility check is SKIPPED and only direction
    checks (B1-B3) are evaluated. This is used in tests of direction-only
    logic. Production UNBOUNDED_CERTIFIED paths must use verify_unbounded_certificate
    with a valid x0.

    Returns the same dict structure as verify_unbounded_certificate with
    base_feasible=True assumed when x0 is None (direction-only mode).
    """
    if x0 is None:
        # Direction-only subcheck: skip base point feasibility
        d = np.asarray(d, dtype=float)
        n = len(model.c)
        if d.shape != (n,) or not np.isfinite(d).all():
            return dict(verified=False, base_feasible=None, ray_verified=False,
                        base_primal_residual=None, objective_direction=None,
                        obj_direction=None,
                        max_row_violation=None, max_bound_violation=None,
                        max_row_direction_violation=None, max_bound_direction_violation=None,
                        message='ray direction is nonfinite or wrong shape')
        # Reuse certificate logic with a dummy feasible x0 at lower bounds
        x0_dummy = np.where(np.isfinite(model.lower), model.lower,
                            np.where(np.isfinite(model.upper), model.upper, 0.0))
        cert = verify_unbounded_certificate(model, x0_dummy, d, tol)
        # Report direction result only; mask base_feasible to None to indicate skip
        return dict(
            verified=cert['ray_verified'],     # direction-only: ray_verified is the gate
            base_feasible=None,                # skipped
            ray_verified=cert['ray_verified'],
            base_primal_residual=None,         # skipped
            objective_direction=cert['objective_direction'],
            obj_direction=cert['objective_direction'],
            original_objective_direction=cert.get('original_objective_direction'),
            max_row_violation=cert['max_row_direction_violation'],
            max_bound_violation=cert['max_bound_direction_violation'],
            max_row_direction_violation=cert['max_row_direction_violation'],
            max_bound_direction_violation=cert['max_bound_direction_violation'],
            message=cert['message_dir'] if 'message_dir' in cert else cert['message'],
        )
    return verify_unbounded_certificate(model, x0, d, tol)
