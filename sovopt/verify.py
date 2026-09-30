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
        Q_use = np.zeros((len(x), len(x)), dtype=np.longdouble)
    else:
        Q_use = np.asarray(Q, dtype=np.longdouble)
    raw = float(cld @ xld + xld @ Q_use @ xld / 2.0)
    if model.maximize:
        return -raw + model.obj_offset
    return raw + model.obj_offset

def verify(model, x, z=None, tol=1e-7, check_integer=True):
    x = np.asarray(x, np.longdouble)
    G, h, _ = model.inequalities()
    G = G.astype(np.longdouble)
    h = h.astype(np.longdouble)

    if x.shape != model.c.shape or not np.isfinite(x).all():
        return {'feasible': False, 'kkt_passed': False, 'reason': 'nonfinite or invalid candidate'}

    # Verify variable bounds explicitly (including infinite ones)
    lb_viol = np.maximum(model.lower - np.asarray(x, float), 0.0)
    ub_viol = np.maximum(np.asarray(x, float) - model.upper, 0.0)
    box_viol = float(max(lb_viol.max() if len(lb_viol) else 0.0, ub_viol.max() if len(ub_viol) else 0.0))

    if len(h) > 0:
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
    Q_arr = np.zeros((len(x), len(x)), dtype=float) if model.Q is None else np.asarray(model.Q, dtype=float)
    grad = Q_arr.astype(np.longdouble) @ x + model.c
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
            return report
        raw_obj = float(model.c.astype(np.longdouble) @ x + x @ Q_arr.astype(np.longdouble) @ x / 2.0)
        scale_obj = 1.0 + abs(raw_obj)
        dual = float(np.max(np.maximum(-z, 0.0), initial=0.0))
        stat_denom = 1.0 + np.max(np.abs(grad)) + np.max(np.abs(G.T) @ np.abs(z))
        station = float(np.max(np.abs(grad + G.T @ z)) / stat_denom)
        comp_denom = scale_obj + np.max(np.abs(z * h))
        comp = float(np.max(np.abs(z * (activity - h))) / comp_denom)
        gap_denom = scale_obj + abs(float(z @ h))
        gap = float(abs(z @ (h - activity)) / gap_denom)
        kkt_ok = report['feasible'] and max(dual, station, comp, gap) <= tol
        report.update(
            dual_residual=station,
            dual_sign_violation=dual,
            complementarity=comp,
            relative_duality_gap=gap,
            kkt_passed=kkt_ok
        )
    elif len(h) == 0:
        # No inequality constraints: stationarity requires grad == 0 (or bounded box stationarity)
        grad_norm = float(np.max(np.abs(grad)))
        report.update(
            dual_residual=grad_norm / (1.0 + grad_norm),
            dual_sign_violation=0.0,
            complementarity=0.0,
            relative_duality_gap=0.0,
            kkt_passed=report['feasible'] and grad_norm <= tol
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
