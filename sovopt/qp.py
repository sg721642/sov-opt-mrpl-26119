"""Infeasible-start primal-dual Mehrotra predictor-corrector for convex QP.
Supports finite or infinite variable bounds, handles unconstrained (m=0) models,
and validates positive semidefiniteness.
"""
import numpy as np
from .linalg import LU, NumericalError
from .verify import verify

def step(v, d, fraction=1.0):
    mask = d < 0
    return min(1.0, fraction * float(np.min(-v[mask] / d[mask]))) if mask.any() else 1.0

def solve_qp(model, tol=1e-7, max_iter=150, scaling=True):
    n = len(model.c)
    if model.Q is None:
        raise ValueError('solve_qp requires quadratic objective matrix Q')

    # Internal objective coefficients
    if model.maximize:
        # Maximize c^T x + 1/2 x^T Q x <=> Minimize -c^T x - 1/2 x^T Q x
        c_use = -model.c
        Q_use = -np.asarray(model.Q, dtype=float)
    else:
        c_use = model.c.copy()
        Q_use = np.asarray(model.Q, dtype=float).copy()

    # Symmetrize Q
    Q_use = 0.5 * (Q_use + Q_use.T)

    # Check positive semidefiniteness
    eigvals = np.linalg.eigvalsh(Q_use)
    if np.min(eigvals) < -1e-10:
        raise ValueError('Nonconvex QP rejected: objective Hessian is not positive semidefinite')

    G0, h0, _ = model.inequalities()
    m = len(h0)
    history = []

    # Handle unconstrained QP (m == 0: no row inequalities and no finite bounds)
    if m == 0:
        reg = 1e-11 * max(1.0, float(np.max(abs(np.diag(Q_use)))))
        try:
            lu = LU(Q_use + reg * np.eye(n))
            x = lu.solve(-c_use)
            report = verify(model, x, None, tol)
            return dict(status='OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                        algorithm='primal-dual predictor-corrector QP',
                        x=x.tolist(), dual=[], objective=report['objective'],
                        verification=report, iterations=1, history=history)
        except NumericalError as e:
            return dict(status='NUMERICAL_FAILURE', algorithm='primal-dual predictor-corrector QP',
                        message=str(e), history=history)

    scale = np.maximum(np.max(abs(G0), axis=1), 1e-30) if (scaling and m > 0) else np.ones(m)
    G = G0 / scale[:, None]
    h = h0 / scale

    # Initial point: midpoint for finite box, or lower+1 / upper-1 / 0 for infinite bounds
    x = np.where(np.isfinite(model.upper) & np.isfinite(model.lower),
                 (model.lower + model.upper) / 2.0,
                 np.where(np.isfinite(model.lower), model.lower + 1.0,
                          np.where(np.isfinite(model.upper), model.upper - 1.0, 0.0))).astype(float)
    s = np.maximum(1.0, h - G @ x)
    z = np.ones(m)

    try:
        for k in range(max_iter):
            report = verify(model, x, z / scale, tol)
            if report.get('kkt_passed'):
                return dict(status='OPTIMAL_VERIFIED', algorithm='primal-dual predictor-corrector QP',
                            x=x.tolist(), dual=(z / scale).tolist(), objective=report['objective'],
                            verification=report, iterations=k, history=history)

            rd = Q_use @ x + c_use + G.T @ z
            rp = G @ x + s - h
            mu = float(s @ z / m)

            history.append(dict(iteration=k, primal_residual=report.get('primal_residual', float('nan')),
                                dual_residual=report.get('dual_residual', float('nan')), complementarity=mu))

            K = Q_use + G.T @ ((z / s)[:, None] * G)
            reg = 1e-11 * max(1.0, float(np.max(abs(np.diag(K)))))
            lu = LU(K + reg * np.eye(n))

            def direction(rc):
                dx = lu.solve(-rd + G.T @ ((rc - z * rp) / s))
                ds = -rp - G @ dx
                dz = (-rc - z * ds) / s
                return dx, ds, dz

            da, sa, za = direction(s * z)
            ap = step(s, sa)
            ad = step(z, za)
            mua = float((s + ap * sa) @ (z + ad * za) / m)
            sigma = min(1.0, max(0.0, (mua / mu)**3))
            dx, ds, dz = direction(s * z + sa * za - sigma * mu)
            ap = step(s, ds, 0.995)
            ad = step(z, dz, 0.995)
            x += ap * dx
            s += ap * ds
            z += ad * dz
            if not np.isfinite(x).all() or min(s.min(), z.min()) <= 0:
                raise NumericalError('IPM iterate invalid')

        report = verify(model, x, z / scale, tol)
        return dict(status='LIMIT_REACHED', algorithm='primal-dual predictor-corrector QP',
                    x=x.tolist(), objective=report['objective'], verification=report,
                    iterations=max_iter, history=history)
    except (NumericalError, FloatingPointError, OverflowError) as e:
        return dict(status='NUMERICAL_FAILURE', algorithm='primal-dual predictor-corrector QP',
                    message=str(e), history=history)
