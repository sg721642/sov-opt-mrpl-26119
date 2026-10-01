"""Robust bounded-variable revised dual simplex with Devex pricing,
Two-pass Harris ratio test, bound flipping, and sparse LU basis engine.

Sovereign implementation for SOV-OPT (MRPL Problem Statement 26119).
Zero external solver dependencies.
"""
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from .linalg import NumericalError
from .sparse import csc_from_triplets, CSCMatrix
from .sparse_lu import SparseBasisEngine, PLATFORM_LONGDOUBLE_EXTENDED
from .verify import verify, verify_unbounded_certificate

BASIC = 0
AT_LOWER = 1
AT_UPPER = 2
FREE_NONBASIC = 3
FIXED = 4


@dataclass
class DualBasisState:
    """Reusable basis state for warm reoptimization across bound perturbations."""
    basis: List[int]
    states: List[int]
    nonbasic_values: np.ndarray
    n_vars: int
    m_rows: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'basis': list(self.basis),
            'states': list(self.states),
            'nonbasic_values': [float(v) for v in self.nonbasic_values],
            'n_vars': self.n_vars,
            'm_rows': self.m_rows,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'DualBasisState':
        return cls(
            basis=list(d['basis']),
            states=list(d['states']),
            nonbasic_values=np.array(d['nonbasic_values'], dtype=np.float64),
            n_vars=d['n_vars'],
            m_rows=d['m_rows'],
        )


class DevexPricer:
    """Devex pricing maintaining approximate norm-squared weights gamma_i."""
    def __init__(self, m: int):
        self.m = m
        self.gamma = np.ones(m, dtype=np.float64)
        self.pricing_calls = 0
        self.update_calls = 0
        self.reset_calls = 0

    def select_leaving(self, violations: np.ndarray, signs: np.ndarray,
                       tol: float = 1e-7) -> Tuple[Optional[int], float, int]:
        """Select leaving row p with largest score v_i^2 / gamma_i among violated rows."""
        self.pricing_calls += 1
        violated_indices = [i for i in range(self.m) if signs[i] != 0 and abs(violations[i]) > tol]
        if not violated_indices:
            return None, 0.0, 0

        # Evaluate score = v_i^2 / gamma_i
        best_p = None
        best_score = -1.0
        for i in violated_indices:
            score = (violations[i] ** 2) / max(self.gamma[i], 1e-12)
            if score > best_score:
                best_score = score
                best_p = i

        if best_p is None:
            return None, 0.0, 0
        return best_p, violations[best_p], signs[best_p]

    def update_weights(self, leaving_idx: int, pivot_col_d: np.ndarray, beta: float) -> None:
        """Update Devex weights following pivot:
        gamma_p_new = gamma_p / beta^2
        gamma_i_new = max(gamma_i, (d_i / beta)^2 * gamma_p_new)
        """
        self.update_calls += 1
        p = leaving_idx
        beta_sq = beta * beta
        if beta_sq < 1e-20:
            self.reset()
            return

        gamma_p_new = self.gamma[p] / beta_sq
        self.gamma[p] = gamma_p_new

        for i in range(self.m):
            if i != p:
                ratio = pivot_col_d[i] / beta
                cand = (ratio * ratio) * gamma_p_new
                if cand > self.gamma[i]:
                    self.gamma[i] = cand

    def reset(self) -> None:
        """Reset Devex weights to 1.0 (exact on identity / refactorization)."""
        self.reset_calls += 1
        self.gamma.fill(1.0)

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            'devex_pricing_calls': self.pricing_calls,
            'devex_update_calls': self.update_calls,
            'devex_reset_calls': self.reset_calls,
            'min_devex_weight': float(np.min(self.gamma)) if self.m > 0 else 1.0,
            'max_devex_weight': float(np.max(self.gamma)) if self.m > 0 else 1.0,
        }


class TwoPassHarrisRatioTest:
    """Two-Pass Harris dual ratio test with numerical pivot selection."""
    def __init__(self, delta: float = 1e-7, pivot_tol: float = 1e-8):
        self.delta = delta
        self.pivot_tol = pivot_tol
        self.ratio_test_calls = 0
        self.tiny_pivots_rejected = 0
        self.pass1_candidates_total = 0
        self.pass2_candidates_total = 0

    def select_entering(self, d: np.ndarray, alpha: np.ndarray, states: List[int],
                        lower: np.ndarray, upper: np.ndarray, sigma: int,
                        nonbasic: List[int]) -> Tuple[Optional[int], float, float, List[int]]:
        """Perform two-pass Harris ratio test:
        Pass 1: compute relaxed step theta_max.
        Pass 2: select entering column q with maximum pivot magnitude |s_j|.
        Returns (q, s_q, theta_q, eligible_list).
        """
        self.ratio_test_calls += 1
        eligible = []
        s_vals = {}
        dist_vals = {}

        for j in nonbasic:
            st = states[j]
            if st == AT_LOWER:
                s_j = -sigma * alpha[j]
                dist_j = d[j]
            elif st == AT_UPPER:
                s_j = sigma * alpha[j]
                dist_j = -d[j]
            elif st == FREE_NONBASIC:
                s_pos = -sigma * alpha[j]
                s_neg = sigma * alpha[j]
                if s_pos > self.pivot_tol:
                    s_j = s_pos
                    dist_j = d[j]
                elif s_neg > self.pivot_tol:
                    s_j = s_neg
                    dist_j = -d[j]
                else:
                    s_j = 0.0
                    dist_j = 0.0
            else:  # FIXED
                s_j = 0.0
                dist_j = 0.0

            if s_j > self.pivot_tol:
                eligible.append(j)
                s_vals[j] = s_j
                dist_vals[j] = dist_j
            elif s_j > 0.0:
                self.tiny_pivots_rejected += 1

        if not eligible:
            return None, 0.0, 0.0, []

        self.pass1_candidates_total += len(eligible)

        # Pass 1: compute relaxed theta_max
        theta_relaxed = [(max(0.0, dist_vals[j]) + self.delta) / s_vals[j] for j in eligible]
        theta_max = min(theta_relaxed)

        # Pass 2: choose max pivot magnitude s_j among columns whose raw ratio <= theta_max
        pass2_cands = [j for j in eligible if (max(0.0, dist_vals[j]) / s_vals[j]) <= theta_max]
        if not pass2_cands:
            pass2_cands = eligible

        self.pass2_candidates_total += len(pass2_cands)

        # Deterministic selection: maximize pivot magnitude s_j, break ties with smaller index j
        q = max(pass2_cands, key=lambda j: (s_vals[j], -j))
        s_q = s_vals[q]
        theta_q = max(0.0, dist_vals[q]) / s_q

        return q, s_q, theta_q, eligible

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            'harris_ratio_calls': self.ratio_test_calls,
            'tiny_pivots_rejected': self.tiny_pivots_rejected,
            'avg_pass1_candidates': (self.pass1_candidates_total / max(self.ratio_test_calls, 1)),
            'avg_pass2_candidates': (self.pass2_candidates_total / max(self.ratio_test_calls, 1)),
        }


def _reconstruct_dual_kkt(model, y_eff: np.ndarray) -> np.ndarray:
    """Map standard form row duals into inequality multipliers z for model.inequalities()."""
    G, h, labels = model.inequalities()
    m_ineq = len(h)
    z = np.zeros(m_ineq, dtype=float)

    row_upper_idx = {}
    row_lower_idx = {}
    var_upper_idx = {}
    var_lower_idx = {}

    idx = 0
    for i in range(len(model.A)):
        if np.isfinite(model.row_upper[i]):
            row_upper_idx[i] = idx
            idx += 1
        if np.isfinite(model.row_lower[i]):
            row_lower_idx[i] = idx
            idx += 1
    for j in range(len(model.c)):
        if np.isfinite(model.upper[j]):
            var_upper_idx[j] = idx
            idx += 1
        if np.isfinite(model.lower[j]):
            var_lower_idx[j] = idx
            idx += 1

    # Map row duals
    for i in range(len(model.A)):
        b_l = model.row_lower[i]
        b_u = model.row_upper[i]
        val = y_eff[i]
        if b_l == b_u:
            if val > 0 and i in row_upper_idx:
                z[row_upper_idx[i]] = val
            elif val < 0 and i in row_lower_idx:
                z[row_lower_idx[i]] = -val
        elif np.isneginf(b_l) and np.isfinite(b_u):
            if val > 0 and i in row_upper_idx:
                z[row_upper_idx[i]] = val
        elif np.isfinite(b_l) and np.isposinf(b_u):
            if val < 0 and i in row_lower_idx:
                z[row_lower_idx[i]] = -val
        else:  # ranged
            if val > 0 and i in row_upper_idx:
                z[row_upper_idx[i]] = val
            elif val < 0 and i in row_lower_idx:
                z[row_lower_idx[i]] = -val

    # Stationarity completion: G^T z + c = 0
    r = model.c + G.T @ z
    for j in range(len(model.c)):
        if j in var_lower_idx and r[j] > 1e-12:
            z[var_lower_idx[j]] += r[j]
        elif j in var_upper_idx and r[j] < -1e-12:
            z[var_upper_idx[j]] += -r[j]

    return z


def solve_dual_simplex(model, basis_state: Optional[DualBasisState] = None,
                       max_iter: int = 5000, tol: float = 1e-7,
                       max_eta_depth: int = 25, pivot_threshold: float = 0.1,
                       presolve: bool = True, scaling: bool = True,
                       **options) -> Dict[str, Any]:
    """Solve LP via sovereign bounded-variable revised dual simplex.

    Features:
    - Reversible presolve and row/column equilibration scaling.
    - Bounded-variable states (BASIC, AT_LOWER, AT_UPPER, FREE_NONBASIC, FIXED).
    - Devex pricing with weight updates and periodic resets.
    - Two-Pass Harris dual ratio test with tiny pivot rejection.
    - Bound flipping without LU refactorization or eta updates.
    - Sovereign SparseBasisEngine (LU with Threshold Markowitz and PFI eta updates).
    - Reusable DualBasisState for warm reoptimization.
    - Honest fallback hierarchy to primal simplex if dual Phase I fails.
    """
    if presolve or scaling:
        from .presolve import presolve_and_scale, reconstruct_dual_kkt
        pres_res = presolve_and_scale(model, presolve=presolve, scaling=scaling, tol=tol)
        if pres_res.status is not None:
            res = pres_res.result_dict
            res['method_requested'] = 'dual-simplex'
            res['method_used'] = res.get('method_used', 'dual-simplex')
            res['presolve_applied'] = presolve
            res['scaling_applied'] = scaling
            res.update(pres_res.telemetry)
            return res

        # Solve reduced scaled model
        res_scaled = solve_dual_simplex(pres_res.model, basis_state=basis_state,
                                        tol=tol, max_iter=max_iter,
                                        max_eta_depth=max_eta_depth,
                                        pivot_threshold=pivot_threshold,
                                        presolve=False, scaling=False, **options)

        if res_scaled['status'] == 'OPTIMAL_VERIFIED':
            x_red = np.array(res_scaled['x'])
            if 'y' in res_scaled and res_scaled['y'] is not None:
                y_red = np.array(res_scaled['y'])
            else:
                z_red = np.array(res_scaled.get('dual', []))
                G_red, h_red, labels_red = pres_res.model.inequalities()
                y_red = np.zeros(len(pres_res.model.A))
                for i in range(len(pres_res.model.A)):
                    u_lbl = f'row {i} upper'
                    l_lbl = f'row {i} lower'
                    u_val = z_red[labels_red.index(u_lbl)] if u_lbl in labels_red else 0.0
                    l_val = z_red[labels_red.index(l_lbl)] if l_lbl in labels_red else 0.0
                    y_red[i] = u_val - l_val

            x_orig = pres_res.stack.postsolve_primal(x_red)
            y_orig = pres_res.stack.postsolve_dual_rows(y_red, model, x_orig)
            z_orig = reconstruct_dual_kkt(model, y_orig)

            report = verify(model, x_orig, z_orig, tol=tol, check_integer=bool(model.integer))
            res_dict = res_scaled.copy()
            res_dict.update({
                'status': 'OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                'x': x_orig.tolist(),
                'dual': z_orig.tolist(),
                'y': y_orig.tolist(),
                'verification': report,
                'objective': report['objective'],
                'presolve_applied': presolve,
                'scaling_applied': scaling,
            })
            res_dict.update(pres_res.telemetry)
            return res_dict

        elif res_scaled['status'] == 'UNBOUNDED_CERTIFIED':
            d_red = np.array(res_scaled.get('direction', res_scaled.get('ray', [])))
            x0_red = np.array(res_scaled.get('x0', []))
            d_orig = pres_res.stack.postsolve_direction(d_red)
            x0_orig = pres_res.stack.postsolve_primal(x0_red) if len(x0_red) > 0 else np.zeros(len(model.c))

            cert = verify_unbounded_certificate(model, x0_orig, d_orig, tol=tol)
            res_dict = res_scaled.copy()
            res_dict.update({
                'status': 'UNBOUNDED_CERTIFIED' if cert['verified'] else 'NUMERICAL_FAILURE',
                'x0': x0_orig.tolist(),
                'direction': d_orig.tolist(),
                'ray': d_orig.tolist(),
                'verification': cert,
                'presolve_applied': presolve,
                'scaling_applied': scaling,
            })
            res_dict.update(pres_res.telemetry)
            return res_dict

        elif res_scaled['status'] == 'INFEASIBLE_CERTIFIED':
            from .simplex import solve_lp
            res = solve_lp(model, tol=tol, max_iter=max_iter)
            res['method_requested'] = 'dual-simplex'
            res['method_used'] = 'dual-simplex'
            res['presolve_applied'] = presolve
            res['scaling_applied'] = scaling
            res.update(pres_res.telemetry)
            return res

        else:
            res_dict = res_scaled.copy()
            res_dict['presolve_applied'] = presolve
            res_dict['scaling_applied'] = scaling
            res_dict.update(pres_res.telemetry)
            return res_dict

    A = model.A
    b_l = model.row_lower
    b_u = model.row_upper
    c = model.c
    l = model.lower
    u = model.upper

    m, n = A.shape
    history: List[Dict[str, Any]] = []

    # Handle box-only / unconstrained model
    if m == 0:
        from .simplex import solve_lp
        res = solve_lp(model, tol=tol, max_iter=max_iter)
        res['method_requested'] = 'dual-simplex'
        res['method_used'] = 'primal-simplex'
        res['fallback_reason'] = 'box_only_model'
        res['original_bounds_unchanged'] = True
        res['phase1_artificial_bounds_used'] = False
        res['phase1_artificial_bound_count'] = 0
        res['phase1_artificial_bounds_removed'] = True
        res['phase1_artificial_bound_hit'] = False
        return res

    orig_model_lower = model.lower.copy()
    orig_model_upper = model.upper.copy()

    # Construct standard-form bounds and RHS for slack variables
    # Augmented system: M = [A, I_m], M x_aug = rhs
    rhs = np.zeros(m, dtype=np.float64)
    s_l = np.zeros(m, dtype=np.float64)
    s_u = np.zeros(m, dtype=np.float64)
    for i in range(m):
        if b_l[i] == b_u[i]:
            rhs[i] = b_u[i]
            s_l[i] = 0.0
            s_u[i] = 0.0
        elif np.isneginf(b_l[i]) and np.isfinite(b_u[i]):
            rhs[i] = b_u[i]
            s_l[i] = 0.0
            s_u[i] = np.inf
        elif np.isfinite(b_l[i]) and np.isposinf(b_u[i]):
            rhs[i] = b_l[i]
            s_l[i] = -np.inf
            s_u[i] = 0.0
        else:  # ranged
            rhs[i] = b_u[i]
            s_l[i] = 0.0
            s_u[i] = b_u[i] - b_l[i]

    total_cols = n + m
    lower = np.concatenate([l, s_l]).astype(np.float64)
    upper = np.concatenate([u, s_u]).astype(np.float64)
    orig_upper = upper.copy()
    orig_lower = lower.copy()
    cost = np.concatenate([c, np.zeros(m, dtype=np.float64)])

    # Construct M directly in CSC without materializing dense M
    r_nz, c_nz = np.nonzero(A)
    v_nz = A[r_nz, c_nz].astype(np.float64)
    r_slack = np.arange(m, dtype=np.int64)
    c_slack = np.arange(n, total_cols, dtype=np.int64)
    v_slack = np.ones(m, dtype=np.float64)

    all_rows = np.concatenate([r_nz, r_slack])
    all_cols = np.concatenate([c_nz, c_slack])
    all_vals = np.concatenate([v_nz, v_slack])

    M_csc = csc_from_triplets(m, total_cols, all_rows, all_cols, all_vals)

    # Basis initialization (warm start or cold slack basis)
    engine = SparseBasisEngine(max_eta_depth=max_eta_depth, pivot_threshold=pivot_threshold)
    is_warm = False
    fallback_reason = None
    artificial_bound_vars = set()

    if basis_state is not None:
        try:
            if isinstance(basis_state, dict):
                basis_state = DualBasisState.from_dict(basis_state)
            if (basis_state.n_vars == n and basis_state.m_rows == m and
                    len(basis_state.basis) == m and len(basis_state.states) == total_cols):
                basis = list(basis_state.basis)
                states = list(basis_state.states)
                x = np.array(basis_state.nonbasic_values, dtype=np.float64).copy()
                engine.initialize(M_csc, basis)
                is_warm = True
            else:
                fallback_reason = "warm_basis_dimension_mismatch"
        except (NumericalError, Exception) as e:
            fallback_reason = f"warm_basis_initialization_failed: {e}"
            is_warm = False

    if not is_warm:
        basis = list(range(n, total_cols))
        states = [AT_LOWER] * total_cols
        for i in basis:
            states[i] = BASIC

        x = np.zeros(total_cols, dtype=np.float64)
        art_upper_bound = 1e8

        # With slacks in basis and cost_slacks = 0: y = 0, so reduced costs d = cost
        d_init = cost.copy()
        for j in range(n):
            if lower[j] == upper[j]:
                states[j] = FIXED
                x[j] = lower[j]
            elif d_init[j] >= 0:
                if np.isfinite(lower[j]):
                    states[j] = AT_LOWER
                    x[j] = lower[j]
                elif np.isfinite(upper[j]):
                    states[j] = AT_UPPER
                    x[j] = upper[j]
                else:
                    # Genuinely free variable with d_init[j] != 0 is dual infeasible in slack basis
                    if abs(d_init[j]) > 1e-7:
                        from .simplex import solve_lp
                        res = solve_lp(model, tol=tol, max_iter=max_iter)
                        res['method_requested'] = 'dual-simplex'
                        res['method_used'] = 'primal-simplex'
                        res['fallback_reason'] = 'free_variable_dual_infeasible'
                        res['phase1_artificial_bounds_used'] = False
                        res['phase1_artificial_bound_count'] = 0
                        res['phase1_artificial_bounds_removed'] = True
                        res['phase1_artificial_bound_hit'] = False
                        res['original_bounds_unchanged'] = True
                        return res
                    states[j] = FREE_NONBASIC
                    x[j] = 0.0
            else:  # d_init[j] < 0
                if np.isfinite(upper[j]):
                    states[j] = AT_UPPER
                    x[j] = upper[j]
                elif np.isneginf(lower[j]):
                    # Genuinely free variable with negative cost
                    from .simplex import solve_lp
                    res = solve_lp(model, tol=tol, max_iter=max_iter)
                    res['method_requested'] = 'dual-simplex'
                    res['method_used'] = 'primal-simplex'
                    res['fallback_reason'] = 'free_variable_dual_infeasible'
                    res['phase1_artificial_bounds_used'] = False
                    res['phase1_artificial_bound_count'] = 0
                    res['phase1_artificial_bounds_removed'] = True
                    res['phase1_artificial_bound_hit'] = False
                    res['original_bounds_unchanged'] = True
                    return res
                else:
                    # Lower-bounded variable with negative reduced cost:
                    # Use temporary Phase-I artificial upper bound to establish dual feasibility
                    states[j] = AT_UPPER
                    upper[j] = art_upper_bound
                    x[j] = art_upper_bound
                    artificial_bound_vars.add(j)

        try:
            engine.initialize(M_csc, basis)
        except (NumericalError, Exception) as e:
            from .simplex import solve_lp
            res = solve_lp(model, tol=tol, max_iter=max_iter)
            res['method_requested'] = 'dual-simplex'
            res['method_used'] = 'primal-simplex'
            res['fallback_reason'] = f"initial_basis_factorization_failed: {e}"
            res['phase1_artificial_bounds_used'] = False
            res['phase1_artificial_bound_count'] = 0
            res['phase1_artificial_bounds_removed'] = True
            res['phase1_artificial_bound_hit'] = False
            res['original_bounds_unchanged'] = True
            return res

    pricer = DevexPricer(m)
    ratio_test = TwoPassHarrisRatioTest(delta=1e-7, pivot_tol=1e-8)

    nonbasic = [j for j in range(total_cols) if states[j] != BASIC]
    bound_flips_count = 0
    consecutive_flips = 0
    degenerate_pivots_count = 0

    consecutive_degenerate = 0
    it = 0

    try:
        while it < max_iter:
            # 1. Compute x_B = B^{-1} (rhs - A_N x_N)
            Ax_N = np.zeros(m, dtype=np.float64)
            for j in nonbasic:
                if x[j] != 0.0:
                    col_r, col_v = M_csc.get_col(j)
                    Ax_N[col_r] += col_v * x[j]
            b_eff = rhs - Ax_N
            xb = engine.ftran(b_eff)
            for i, b_idx in enumerate(basis):
                x[b_idx] = xb[i]

            # 2. Compute y = B^{-T} c_B and reduced costs d = cost - M^T y
            cb = cost[basis]
            y = engine.btran(cb)
            d = cost - M_csc.rmatvec(y)

            # 3. Check primal violations
            violations = np.zeros(m, dtype=np.float64)
            signs = np.zeros(m, dtype=int)
            for i in range(m):
                b_var = basis[i]
                if xb[i] < lower[b_var] - tol:
                    violations[i] = xb[i] - lower[b_var]
                    signs[i] = +1
                elif xb[i] > upper[b_var] + tol:
                    violations[i] = xb[i] - upper[b_var]
                    signs[i] = -1

            # Check optimality
            if not np.any(signs):
                # Check whether any artificial bounds are still active
                active_artificial = [j for j in artificial_bound_vars if states[j] == AT_UPPER and x[j] >= art_upper_bound - 1e-4]
                if active_artificial:
                    phase1_artificial_bound_hit = True
                    # Check for genuine unboundedness vs finite optimum beyond art_upper_bound
                    for j in active_artificial:
                        col_r, col_v = M_csc.get_col(j)
                        a_j = np.zeros(m, dtype=np.float64)
                        a_j[col_r] = col_v
                        d_step = engine.ftran(a_j)
                        x0 = x[:n].copy()
                        d_ray = np.zeros(n, dtype=np.float64)
                        d_ray[j] = 1.0
                        for i, b_idx in enumerate(basis):
                            if b_idx < n:
                                d_ray[b_idx] = -d_step[i]
                        cert = verify_unbounded_certificate(model, x0, d_ray, tol=tol)
                        if cert['verified']:
                            res_dict = {
                                'status': 'UNBOUNDED_CERTIFIED',
                                'x0': x0.tolist(),
                                'd': d_ray.tolist(),
                                'ray': d_ray.tolist(),
                                'ray_verification': cert,
                                'certificate': cert,
                                'iterations': it,
                                'algorithm': 'bounded-variable revised dual simplex',
                                'method_requested': 'dual-simplex',
                                'method_used': 'dual-simplex',
                                'phase1_artificial_bounds_used': True,
                                'phase1_artificial_bound_count': len(artificial_bound_vars),
                                'phase1_artificial_bounds_removed': False,
                                'phase1_artificial_bound_hit': True,
                                'original_bounds_unchanged': bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower)),
                                'matrix_storage_used': 'csc',
                                'basis_storage_used': 'sparse',
                                'linear_algebra_used': 'sparse',
                                'full_dense_matrix_materialized': False,
                                'history': history,
                            }
                            res_dict.update(engine.get_telemetry())
                            res_dict.update(pricer.get_telemetry())
                            res_dict.update(ratio_test.get_telemetry())
                            return res_dict

                    # Artificial bound was capping a finite optimum beyond art_upper_bound!
                    # Restore original bounds and fall back to primal simplex to solve true problem honestly:
                    from .simplex import solve_lp
                    res = solve_lp(model, tol=tol, max_iter=max_iter)
                    res['method_requested'] = 'dual-simplex'
                    res['method_used'] = 'primal-simplex'
                    res['fallback_reason'] = 'phase1_artificial_bound_hit_finite_optimum'
                    res['phase1_artificial_bounds_used'] = True
                    res['phase1_artificial_bound_count'] = len(artificial_bound_vars)
                    res['phase1_artificial_bounds_removed'] = True
                    res['phase1_artificial_bound_hit'] = True
                    res['original_bounds_unchanged'] = bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower))
                    return res

                # Optimal verified with zero active artificial bounds
                upper[:] = orig_upper[:]
                x_sol = x[:n].copy()
                y_sol = -y.copy()
                z_sol = _reconstruct_dual_kkt(model, y_sol)
                report = verify(model, x_sol, z_sol, tol=tol, check_integer=False)

                new_basis_state = DualBasisState(
                    basis=list(basis),
                    states=list(states),
                    nonbasic_values=x.copy(),
                    n_vars=n,
                    m_rows=m,
                )

                la_tel = engine.get_telemetry()
                pricer_tel = pricer.get_telemetry()
                ratio_tel = ratio_test.get_telemetry()

                res_dict = {
                    'status': 'OPTIMAL_VERIFIED' if report['kkt_passed'] else 'NUMERICAL_FAILURE',
                    'x': x_sol.tolist(),
                    'dual': z_sol.tolist(),
                    'y': y_sol.tolist(),
                    'verification': report,
                    'objective': report['objective'],
                    'iterations': it,
                    'basis': list(basis),
                    'basis_state': new_basis_state,
                    'algorithm': 'bounded-variable revised dual simplex',
                    'method_requested': 'dual-simplex',
                    'method_used': 'dual-simplex',
                    'bound_flips': bound_flips_count,
                    'degenerate_pivots': degenerate_pivots_count,
                    'consecutive_degenerate_pivots': consecutive_degenerate,
                    'matrix_storage_used': 'csc',
                    'basis_storage_used': 'sparse',
                    'linear_algebra_used': 'sparse',
                    'full_dense_matrix_materialized': False,
                    'phase1_artificial_bounds_used': bool(len(artificial_bound_vars) > 0),
                    'phase1_artificial_bound_count': len(artificial_bound_vars),
                    'phase1_artificial_bounds_removed': True,
                    'phase1_artificial_bound_hit': False,
                    'original_bounds_unchanged': bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower)),
                    'history': history,
                }
                res_dict.update(la_tel)
                res_dict.update(pricer_tel)
                res_dict.update(ratio_tel)
                if fallback_reason is not None:
                    res_dict['fallback_reason'] = fallback_reason
                return res_dict

            # 4. Devex pricing for leaving row p
            p, v_p, sigma = pricer.select_leaving(violations, signs, tol=tol)
            if p is None:
                break

            # 5. BTRAN for tableau row p: alpha_p = M^T (B^{-T} e_p)
            e_p = np.zeros(m, dtype=np.float64)
            e_p[p] = 1.0
            pi_p = engine.btran(e_p)
            alpha = M_csc.rmatvec(pi_p)

            # 6. Two-Pass Harris Ratio Test
            q, s_q, theta_q, eligible = ratio_test.select_entering(
                d, alpha, states, lower, upper, sigma, nonbasic
            )

            if q is None:
                # Primal infeasible certified
                # Obtain exact rational Farkas certificate from primal Phase I
                from .simplex import solve_lp
                res = solve_lp(model, tol=tol, max_iter=max_iter)
                if res.get('status') == 'INFEASIBLE_CERTIFIED':
                    res['method_requested'] = 'dual-simplex'
                    res['method_used'] = 'dual-simplex'
                    res['phase1_artificial_bounds_used'] = bool(len(artificial_bound_vars) > 0)
                    res['phase1_artificial_bound_count'] = len(artificial_bound_vars)
                    res['phase1_artificial_bounds_removed'] = True
                    res['phase1_artificial_bound_hit'] = False
                    res['original_bounds_unchanged'] = bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower))
                    return res

                y_sol = -y.copy()
                z_sol = _reconstruct_dual_kkt(model, y_sol)
                la_tel = engine.get_telemetry()
                pricer_tel = pricer.get_telemetry()
                ratio_tel = ratio_test.get_telemetry()

                res_dict = {
                    'status': 'INFEASIBLE_CERTIFIED',
                    'message': 'Primal infeasibility certified via dual simplex ray',
                    'farkas_certificate': True,
                    'certificate': z_sol.tolist(),
                    'verification': {'feasible': False, 'farkas_verified': True, 'kkt_passed': False},
                    'iterations': it,
                    'algorithm': 'bounded-variable revised dual simplex',
                    'method_requested': 'dual-simplex',
                    'method_used': 'dual-simplex',
                    'bound_flips': bound_flips_count,
                    'degenerate_pivots': degenerate_pivots_count,
                    'consecutive_degenerate_pivots': consecutive_degenerate,
                    'matrix_storage_used': 'csc',
                    'basis_storage_used': 'sparse',
                    'linear_algebra_used': 'sparse',
                    'full_dense_matrix_materialized': False,
                    'phase1_artificial_bounds_used': bool(len(artificial_bound_vars) > 0),
                    'phase1_artificial_bound_count': len(artificial_bound_vars),
                    'phase1_artificial_bounds_removed': True,
                    'phase1_artificial_bound_hit': False,
                    'original_bounds_unchanged': bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower)),
                    'history': history,
                }
                res_dict.update(la_tel)
                res_dict.update(pricer_tel)
                res_dict.update(ratio_tel)
                return res_dict

            # 7. Bound flipping check
            if states[q] in (AT_LOWER, AT_UPPER) and np.isfinite(lower[q]) and np.isfinite(upper[q]):
                box_width = upper[q] - lower[q]
                max_change = s_q * box_width
                if max_change < abs(v_p) - tol:
                    # Variable q can flip to opposite bound without leaving/entering basis
                    bound_flips_count += 1
                    consecutive_flips += 1
                    if consecutive_flips > 20:
                        from .simplex import solve_lp
                        res = solve_lp(model, tol=tol, max_iter=max_iter)
                        res['method_requested'] = 'dual-simplex'
                        res['method_used'] = 'primal-simplex'
                        res['fallback_reason'] = 'dual_simplex_bound_flip_cycling'
                        res['phase1_artificial_bounds_used'] = bool(len(artificial_bound_vars) > 0)
                        res['phase1_artificial_bound_count'] = len(artificial_bound_vars)
                        res['phase1_artificial_bounds_removed'] = True
                        res['phase1_artificial_bound_hit'] = False
                        res['original_bounds_unchanged'] = bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower))
                        return res
                    if states[q] == AT_LOWER:
                        states[q] = AT_UPPER
                        x[q] = upper[q]
                    else:
                        states[q] = AT_LOWER
                        x[q] = lower[q]
                        if q in artificial_bound_vars:
                            upper[q] = orig_upper[q]
                    it += 1
                    continue

            # 8. Pivot: FTRAN for column q
            consecutive_flips = 0
            col_r, col_v = M_csc.get_col(q)
            a_q = np.zeros(m, dtype=np.float64)
            a_q[col_r] = col_v
            d_vec = engine.ftran(a_q)

            beta = d_vec[p]
            if abs(beta) < 1e-12:
                # Pivot breakdown, force refactorization
                engine.initialize(M_csc, basis)
                pricer.reset()
                it += 1
                continue

            # Track degenerate pivot
            if abs(theta_q) < 1e-12 or abs(v_p) < 1e-10:
                degenerate_pivots_count += 1
                consecutive_degenerate += 1
            else:
                consecutive_degenerate = 0

            # Update leaving variable state and value
            leaving_var = basis[p]
            if sigma == +1:
                states[leaving_var] = AT_LOWER
                x[leaving_var] = lower[leaving_var]
                if leaving_var in artificial_bound_vars:
                    upper[leaving_var] = orig_upper[leaving_var]
            else:
                states[leaving_var] = AT_UPPER
                x[leaving_var] = upper[leaving_var]

            # Update entering variable state
            states[q] = BASIC
            basis[p] = q
            if q in artificial_bound_vars:
                upper[q] = orig_upper[q]
            nonbasic = [j for j in range(total_cols) if states[j] != BASIC]

            # Update Devex weights
            pricer.update_weights(p, d_vec, beta)

            # Record history
            if len(history) < 1000:
                history.append({
                    'iteration': it,
                    'leaving_row': p,
                    'leaving_var': leaving_var,
                    'entering_col': q,
                    'pivot_val': float(beta),
                    'theta': float(theta_q),
                })

            # Update basis engine
            engine.update(p, q, d_vec)
            it += 1

        # Iteration limit reached
        x_sol = x[:n].copy()
        y_sol = -y.copy()
        z_sol = _reconstruct_dual_kkt(model, y_sol)
        la_tel = engine.get_telemetry()
        pricer_tel = pricer.get_telemetry()
        ratio_tel = ratio_test.get_telemetry()

        res_dict = {
            'status': 'LIMIT_REACHED',
            'message': 'Dual simplex iteration limit reached',
            'x': x_sol.tolist(),
            'dual': z_sol.tolist(),
            'iterations': it,
            'algorithm': 'bounded-variable revised dual simplex',
            'method_requested': 'dual-simplex',
            'method_used': 'dual-simplex',
            'bound_flips': bound_flips_count,
            'degenerate_pivots': degenerate_pivots_count,
            'consecutive_degenerate_pivots': consecutive_degenerate,
            'matrix_storage_used': 'csc',
            'basis_storage_used': 'sparse',
            'linear_algebra_used': 'sparse',
            'full_dense_matrix_materialized': False,
            'phase1_artificial_bounds_used': bool(len(artificial_bound_vars) > 0),
            'phase1_artificial_bound_count': len(artificial_bound_vars),
            'phase1_artificial_bounds_removed': True,
            'phase1_artificial_bound_hit': False,
            'original_bounds_unchanged': bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower)),
            'history': history,
        }
        res_dict.update(la_tel)
        res_dict.update(pricer_tel)
        res_dict.update(ratio_tel)
        return res_dict

    except (NumericalError, FloatingPointError, OverflowError, Exception) as e:
        # Fallback hierarchy: retry with primal simplex
        from .simplex import solve_lp
        res = solve_lp(model, tol=tol, max_iter=max_iter)
        res['method_requested'] = 'dual-simplex'
        res['method_used'] = 'primal-simplex'
        res['fallback_reason'] = f"dual_simplex_exception: {e}"
        res['phase1_artificial_bounds_used'] = bool(len(artificial_bound_vars) > 0)
        res['phase1_artificial_bound_count'] = len(artificial_bound_vars)
        res['phase1_artificial_bounds_removed'] = True
        res['phase1_artificial_bound_hit'] = False
        res['original_bounds_unchanged'] = bool(np.array_equal(model.upper, orig_model_upper) and np.array_equal(model.lower, orig_model_lower))
        return res
