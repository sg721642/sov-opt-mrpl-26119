"""Infeasible-start primal-dual Mehrotra predictor-corrector for convex QP.
Native equality-aware interior-point architecture:
- Equality constraints (row_lower == row_upper and fixed variables) are handled natively in the saddle-point system.
- Slacks (s > 0) and nonnegativity duals (z >= 0) are allocated strictly for genuine inequalities and finite variable bounds.
- Dual multipliers y for equality constraints are free (unrestricted in sign).
- Matrix factorizations use NumPy linear algebra LAPACK routines with regularized augmented saddle-point systems and iterative refinement.
- Independent original-model verification via sovopt.verify.verify() confirms all KKT conditions prior to OPTIMAL_VERIFIED.
"""
import numpy as np
from .verify import verify


def canonicalize_qp(model, tol=1e-12):
    """Partition model into native linear equalities E*x = f and inequalities G*x <= h.
    
    Returns:
        E (ndarray): equality constraint matrix (m_e, n)
        f (ndarray): equality constraint RHS (m_e,)
        eq_map (list): metadata mapping equality rows back to model indices
        G (ndarray): inequality constraint matrix (m_i, n)
        h (ndarray): inequality constraint RHS (m_i,)
        ineq_map (list): metadata mapping inequality rows back to model indices
    """
    n = len(model.c)
    eq_rows, eq_rhs, eq_map = [], [], []
    ineq_rows, ineq_rhs, ineq_map = [], [], []

    # 1. Row constraints from model.A
    for i in range(len(model.A)):
        lo, hi = model.row_lower[i], model.row_upper[i]
        if np.isfinite(lo) and np.isfinite(hi) and abs(lo - hi) <= tol * max(1.0, abs(lo)):
            eq_rows.append(model.A[i])
            eq_rhs.append(hi)
            eq_map.append(('row_eq', i))
        else:
            if np.isfinite(hi):
                ineq_rows.append(model.A[i])
                ineq_rhs.append(hi)
                ineq_map.append(('row_upper', i))
            if np.isfinite(lo):
                ineq_rows.append(-model.A[i])
                ineq_rhs.append(-lo)
                ineq_map.append(('row_lower', i))

    # 2. Variable bounds from model.lower, model.upper
    for j in range(n):
        lj, uj = model.lower[j], model.upper[j]
        if np.isfinite(lj) and np.isfinite(uj) and abs(lj - uj) <= tol * max(1.0, abs(lj)):
            e = np.zeros(n)
            e[j] = 1.0
            eq_rows.append(e)
            eq_rhs.append(uj)
            eq_map.append(('var_eq', j))
        else:
            if np.isfinite(uj):
                e = np.zeros(n)
                e[j] = 1.0
                ineq_rows.append(e)
                ineq_rhs.append(uj)
                ineq_map.append(('var_upper', j))
            if np.isfinite(lj):
                e = np.zeros(n)
                e[j] = -1.0
                ineq_rows.append(e)
                ineq_rhs.append(-lj)
                ineq_map.append(('var_lower', j))

    E = np.array(eq_rows, dtype=float).reshape((-1, n)) if eq_rows else np.zeros((0, n))
    f = np.array(eq_rhs, dtype=float) if eq_rhs else np.zeros(0)
    G = np.array(ineq_rows, dtype=float).reshape((-1, n)) if ineq_rows else np.zeros((0, n))
    h = np.array(ineq_rhs, dtype=float) if ineq_rhs else np.zeros(0)

    return E, f, eq_map, G, h, ineq_map


def map_duals(model, y, z, eq_map, ineq_map, scale_e, scale_g):
    """Map solver internal dual multipliers (y free, z >= 0) to original model.inequalities() dual vector.
    
    For an equality row A_i x = b_i:
        model.inequalities() has 'row i upper' (A_i x <= b_i) and 'row i lower' (-A_i x <= -b_i).
        If y_i >= 0: z['row i upper'] = y_i, z['row i lower'] = 0.
        If y_i < 0:  z['row i upper'] = 0,   z['row i lower'] = -y_i.
    This preserves nonnegativity (z >= 0) and exact stationarity:
        (z_upper - z_lower) A_i = y_i A_i.
    """
    y_orig = y / scale_e if len(y) > 0 else y
    z_orig = z / scale_g if len(z) > 0 else z
    _, _, labels = model.inequalities()
    lbl_map = {lbl: i for i, lbl in enumerate(labels)}
    z_legacy = np.zeros(len(labels))

    for k, (t, idx) in enumerate(eq_map):
        val = y_orig[k]
        if t == 'row_eq':
            u_idx = lbl_map.get(f'row {idx} upper')
            l_idx = lbl_map.get(f'row {idx} lower')
        elif t == 'var_eq':
            name = model.names[idx] if idx < len(model.names) else f'x{idx}'
            u_idx = lbl_map.get(f'{name} upper')
            l_idx = lbl_map.get(f'{name} lower')
        else:
            u_idx, l_idx = None, None

        if val >= 0:
            if u_idx is not None:
                z_legacy[u_idx] = val
        else:
            if l_idx is not None:
                z_legacy[l_idx] = -val

    for k, (t, idx) in enumerate(ineq_map):
        val = z_orig[k]
        if t == 'row_upper':
            lbl = f'row {idx} upper'
        elif t == 'row_lower':
            lbl = f'row {idx} lower'
        elif t == 'var_upper':
            name = model.names[idx] if idx < len(model.names) else f'x{idx}'
            lbl = f'{name} upper'
        elif t == 'var_lower':
            name = model.names[idx] if idx < len(model.names) else f'x{idx}'
            lbl = f'{name} lower'
        else:
            lbl = None

        if lbl is not None:
            i_leg = lbl_map.get(lbl)
            if i_leg is not None:
                z_legacy[i_leg] = val

    return z_legacy


def step_length(v, d, fraction=1.0):
    """Compute maximum step alpha in [0, 1] preserving v + alpha*d >= (1 - fraction)*v."""
    mask = d < 0
    return min(1.0, fraction * float(np.min(-v[mask] / d[mask]))) if mask.any() else 1.0


def solve_qp(model, tol=1e-7, max_iter=150, scaling=True):
    """Solve convex quadratic program using equality-aware primal-dual Mehrotra IPM."""
    n = len(model.c)
    if model.Q is None:
        raise ValueError('solve_qp requires quadratic objective matrix Q')

    # Internal objective conventions:
    # Model convention: c and Q are always stored in canonical internal minimization form.
    # If original problem was maximize, c and Q are already negated on entry.
    c_use = model.c.copy()
    Q_use = np.asarray(model.Q, dtype=float).copy()
    Q_use = 0.5 * (Q_use + Q_use.T)

    # Numerical eigenvalue inspection with scale-aware tolerance
    scale_q = max(1.0, float(np.max(np.abs(np.diag(Q_use))))) if n > 0 else 1.0
    convexity_tol = 1e-10 * scale_q
    if n <= 2500:
        eigvals = np.linalg.eigvalsh(Q_use)
        min_ev = float(np.min(eigvals)) if len(eigvals) > 0 else 0.0
        if min_ev < -convexity_tol:
            raise ValueError(f'Nonconvex QP rejected: objective Hessian is not numerically positive semidefinite (min eigenvalue = {min_ev:.4e} < -{convexity_tol:.4e})')
        if min_ev < 0:
            Q_use += max(0.0, -min_ev + 1e-12) * np.eye(n)

    E, f, eq_map, G, h, ineq_map = canonicalize_qp(model)
    me = len(f)
    mi = len(h)

    # Pre-allocation memory safety guard (250 MB ceiling)
    kkt_dim = n + me
    estimated_bytes = kkt_dim * kkt_dim * 8
    if estimated_bytes > 250 * 1024 * 1024:
        from .qplib import UnsupportedQPLIBError
        raise UnsupportedQPLIBError(
            f'KKT matrix size ({kkt_dim}x{kkt_dim}, {estimated_bytes / (1024*1024):.1f} MB) exceeds declared dense memory guard of 250 MB',
            'UNSUPPORTED_RESOURCE_LIMIT'
        )

    # Equilibrated scaling
    scale_e = np.maximum(np.max(np.abs(E), axis=1), 1e-30) if (scaling and me > 0) else np.ones(me)
    E_s = E / scale_e[:, None] if me > 0 else E
    f_s = f / scale_e if me > 0 else f

    scale_g = np.maximum(np.max(np.abs(G), axis=1), 1e-30) if (scaling and mi > 0) else np.ones(mi)
    G_s = G / scale_g[:, None] if mi > 0 else G
    h_s = h / scale_g if mi > 0 else h

    # Sovereign internal initialization (strictly no external reference solutions used)
    # Solve regularized equality KKT system for initial (x_0, y_0)
    try:
        if me > 0:
            H_init = Q_use + scale_q * 1e-4 * np.eye(n)
            K1 = np.hstack([H_init, E_s.T])
            K2 = np.hstack([E_s, -1e-8 * np.eye(me)])
            K_aug = np.vstack([K1, K2])
            rhs_init = np.concatenate([-c_use, f_s])
            sol_init = np.linalg.solve(K_aug, rhs_init)
            x = sol_init[:n]
            y = sol_init[n:]
        else:
            H_init = Q_use + scale_q * 1e-4 * np.eye(n)
            x = np.linalg.solve(H_init, -c_use)
            y = np.zeros(0)
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError):
        # Fallback to variable midpoint
        x = np.where(np.isfinite(model.upper) & np.isfinite(model.lower),
                     0.5 * (model.lower + model.upper),
                     np.where(np.isfinite(model.lower), model.lower + 1.0,
                              np.where(np.isfinite(model.upper), model.upper - 1.0, 0.0))).astype(float)
        y = np.zeros(me)

    s_slack = h_s - G_s @ x if mi > 0 else np.zeros(0)
    delta_s = max(0.0, -1.5 * float(np.min(s_slack))) if mi > 0 else 0.0
    s = np.maximum(s_slack + delta_s, 10.0) if mi > 0 else np.zeros(0)

    res_stat = -(Q_use @ x + c_use + (E_s.T @ y if me > 0 else 0))
    if mi > 0:
        z_ls = np.linalg.lstsq(G_s.T, res_stat, rcond=None)[0]
        delta_z = max(0.0, -1.5 * float(np.min(z_ls)))
        z = np.maximum(z_ls + delta_z, 10.0)
    else:
        z = np.zeros(0)

    history = []
    reg_p = 1e-12 * scale_q
    reg_d = 1e-12
    last_lin_res = 0.0

    def solve_system(A, b):
        sol = np.linalg.solve(A, b)
        # 1 step of iterative refinement
        res = b - A @ sol
        sol += np.linalg.solve(A, res)
        return sol, float(np.max(np.abs(res)))

    try:
        for k in range(max_iter):
            rd = Q_use @ x + c_use + (E_s.T @ y if me > 0 else 0) + (G_s.T @ z if mi > 0 else 0)
            re = E_s @ x - f_s if me > 0 else np.zeros(0)
            rp = G_s @ x + s - h_s if mi > 0 else np.zeros(0)
            mu = float(s @ z / mi) if mi > 0 else 0.0
            scale_obj = 1.0 + abs(float(c_use @ x + 0.5 * x @ Q_use @ x))
            mu_norm = float(s @ z / (mi * scale_obj)) if mi > 0 else 0.0

            re_norm = np.max(np.abs(re)) / (1.0 + np.max(np.abs(f_s))) if me > 0 else 0.0
            rp_norm = np.max(np.abs(rp)) / (1.0 + np.max(np.abs(h_s))) if mi > 0 else 0.0
            rd_norm = np.max(np.abs(rd)) / (1.0 + np.max(np.abs(c_use)) + np.max(np.abs(Q_use @ x)))

            history.append(dict(
                iteration=k,
                primal_residual=float(max(re_norm, rp_norm)),
                dual_residual=float(rd_norm),
                complementarity=float(mu_norm)
            ))

            # Scaled stopping check
            if max(re_norm, rp_norm, rd_norm, mu_norm) <= tol:
                z_legacy = map_duals(model, y, z, eq_map, ineq_map, scale_e, scale_g)
                rep = verify(model, x, z_legacy, tol=tol)
                if rep.get('kkt_passed'):
                    return dict(
                        status='OPTIMAL_VERIFIED',
                        algorithm='equality-aware primal-dual predictor-corrector QP',
                        x=x.tolist(),
                        dual=z_legacy.tolist(),
                        objective=rep['objective'],
                        verification=rep,
                        iterations=k,
                        history=history,
                        solver_generated_x=True,
                        initialization_source='SOVOPT_INTERNAL',
                        reference_solution_used_as_initialization=False,
                        reference_solution_used_in_search=False,
                        regularization_primal=reg_p,
                        regularization_dual=reg_d,
                        linear_solve_residual=last_lin_res,
                        refinement_steps=1,
                    )

            D = z / s if mi > 0 else np.zeros(0)
            H = Q_use.copy()
            if mi > 0:
                H += G_s.T @ (D[:, None] * G_s)

            if me > 0:
                K1 = np.hstack([H + reg_p * np.eye(n), E_s.T])
                K2 = np.hstack([E_s, -reg_d * np.eye(me)])
                K_aug = np.vstack([K1, K2])

                def solve_kkt(rc):
                    nonlocal last_lin_res
                    rhs_x = -rd + (G_s.T @ ((rc - z * rp) / s) if mi > 0 else 0)
                    rhs = np.concatenate([rhs_x, -re])
                    sol, lin_res = solve_system(K_aug, rhs)
                    last_lin_res = lin_res
                    dx = sol[:n]
                    dy = sol[n:]
                    ds = -rp - G_s @ dx if mi > 0 else np.zeros(0)
                    dz = (-rc - z * ds) / s if mi > 0 else np.zeros(0)
                    return dx, dy, ds, dz
            else:
                H_reg = H + reg_p * np.eye(n)

                def solve_kkt(rc):
                    nonlocal last_lin_res
                    rhs_x = -rd + (G_s.T @ ((rc - z * rp) / s) if mi > 0 else 0)
                    sol, lin_res = solve_system(H_reg, rhs_x)
                    last_lin_res = lin_res
                    dx = sol
                    dy = np.zeros(0)
                    ds = -rp - G_s @ dx if mi > 0 else np.zeros(0)
                    dz = (-rc - z * ds) / s if mi > 0 else np.zeros(0)
                    return dx, dy, ds, dz

            # 1. Predictor step (sigma = 0)
            dx_a, dy_a, ds_a, dz_a = solve_kkt(s * z if mi > 0 else np.zeros(0))
            if mi > 0:
                ap_a = step_length(s, ds_a)
                ad_a = step_length(z, dz_a)
                mu_a = float((s + ap_a * ds_a) @ (z + ad_a * dz_a) / mi)
                sigma = min(1.0, max(0.0, (mu_a / mu)**3)) if mu > 1e-15 else 0.0

                # 2. Corrector step with second-order term
                rc = s * z + ds_a * dz_a - sigma * mu
                dx, dy, ds, dz = solve_kkt(rc)

                # 3. Fraction-to-boundary step length (eta = 0.995)
                ap = step_length(s, ds, 0.995)
                ad = step_length(z, dz, 0.995)
            else:
                dx, dy, ds, dz = dx_a, dy_a, ds_a, dz_a
                ap, ad = 1.0, 1.0

            x += ap * dx
            if me > 0:
                y += ad * dy
            if mi > 0:
                s += ap * ds
                z += ad * dz

            if not np.isfinite(x).all() or (mi > 0 and min(s.min(), z.min()) <= 0):
                return dict(
                    status='NUMERICAL_FAILURE',
                    algorithm='equality-aware primal-dual predictor-corrector QP',
                    message='Iterate became nonfinite or slacks nonpositive',
                    history=history,
                    solver_generated_x=False,
                )

        # Max iterations reached: check final status via verify
        z_legacy = map_duals(model, y, z, eq_map, ineq_map, scale_e, scale_g)
        rep = verify(model, x, z_legacy, tol=tol)
        st = 'OPTIMAL_VERIFIED' if rep.get('kkt_passed') else 'LIMIT_REACHED'
        return dict(
            status=st,
            algorithm='equality-aware primal-dual predictor-corrector QP',
            x=x.tolist(),
            dual=z_legacy.tolist(),
            objective=rep['objective'],
            verification=rep,
            iterations=max_iter,
            history=history,
            solver_generated_x=True,
            initialization_source='SOVOPT_INTERNAL',
            reference_solution_used_as_initialization=False,
            reference_solution_used_in_search=False,
            regularization_primal=reg_p,
            regularization_dual=reg_d,
            linear_solve_residual=last_lin_res,
            refinement_steps=1,
        )

    except (np.linalg.LinAlgError, FloatingPointError, OverflowError) as e:
        return dict(
            status='NUMERICAL_FAILURE',
            algorithm='equality-aware primal-dual predictor-corrector QP',
            message=str(e),
            history=history,
            solver_generated_x=False,
        )
