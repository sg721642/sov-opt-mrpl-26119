"""MRPL Refinery Planning Digital Twin for Problem Statement 26119.

PROVENANCE DISCLAIMER:
This model is an original engineering formulation developed for MRPL SIH PS 26119
demonstration, verification, and benchmarking. It is constructed from public,
open-domain refining engineering literature (Gary & Handwerk, 'Petroleum Refining:
Technology and Economics'; Meyers, 'Handbook of Petroleum Refining Processes')
and does not contain proprietary MRPL operating data, actual commercial contracts,
or confidential refinery telemetry. All units, yields, and economics are representative
engineering approximations.

The twin provides a single unified parameterised formulation with 4 operational variants:
1. 'lp': Continuous multi-period economic planning (linear yields, blending, inventories).
2. 'milp': Discrete unit commitment with binary on/off states and minimum turndown limits.
3. 'qp': Smooth operational dispatch with positive semidefinite quadratic throughput-flutter
   penalties to protect heavy processing units (FCC, Reformer) against thermal cycling.
4. 'infeasible': Diagnostic scenario with demand exceeding maximum intake, certifying
   infeasibility via an exact Farkas certificate.
"""

import numpy as np
from .model import Model

def build_refinery_twin(variant='lp', periods=2, finite_capacity=150.0):
    """Construct an MRPL Refinery Planning Twin instance.
    
    Args:
        variant: One of 'lp', 'milp', 'qp', 'infeasible'.
        periods: Number of planning periods (default 2).
        finite_capacity: Physical maximum bound on stream rates to ensure finite box bounds.
    
    Returns:
        Model: A sovereign sovopt.Model instance.
    """
    v = variant.lower()
    if v not in ('lp', 'milp', 'qp', 'infeasible'):
        raise ValueError(f"Unknown variant '{variant}'. Expected 'lp', 'milp', 'qp', or 'infeasible'.")

    # Variables per period t:
    #  0: x_c0_t (Arab Light crude intake)
    #  1: x_c1_t (Basrah crude intake)
    #  2: f_cdu_t (CDU throughput = x_c0 + x_c1)
    #  3: f_fcc_t (FCC feed throughput)
    #  4: f_ref_t (Reformer feed throughput)
    #  5: b_ref_gas_t (Reformate to gasoline blend)
    #  6: b_cat_gas_t (FCC CatGas to gasoline blend)
    #  7: b_dist_dsl_t (Distillate to diesel blend)
    #  8: b_lco_dsl_t (FCC LCO to diesel blend)
    #  9: s_gas_t (Gasoline shipment)
    # 10: s_dsl_t (Diesel shipment)
    # 11: s_fo_t (Fuel Oil shipment)
    # 12: inv_naph_t (Naphtha intermediate inventory)
    # 13: inv_ref_t (Reformate intermediate inventory)
    # 14: inv_dist_t (Distillate intermediate inventory)
    # 15: inv_cat_t (CatGas intermediate inventory)
    # 16: inv_lco_t (LCO intermediate inventory)
    # 17: inv_fo_t (Fuel Oil intermediate inventory)
    N_PER_T = 18
    n_cont = N_PER_T * periods

    var_names = []
    for t in range(periods):
        var_names.extend([
            f'x_c0_t{t}', f'x_c1_t{t}', f'f_cdu_t{t}', f'f_fcc_t{t}', f'f_ref_t{t}',
            f'b_ref_gas_t{t}', f'b_cat_gas_t{t}', f'b_dist_dsl_t{t}', f'b_lco_dsl_t{t}',
            f's_gas_t{t}', f's_dsl_t{t}', f's_fo_t{t}',
            f'inv_naph_t{t}', f'inv_ref_t{t}', f'inv_dist_t{t}', f'inv_cat_t{t}', f'inv_lco_t{t}', f'inv_fo_t{t}'
        ])

    lower = np.zeros(n_cont)
    upper = np.full(n_cont, float(finite_capacity))

    # Unit capacity physical upper bounds
    for t in range(periods):
        b = t * N_PER_T
        upper[b + 0] = 80.0   # crude 0 max purchase
        upper[b + 1] = 80.0   # crude 1 max purchase
        upper[b + 2] = 100.0  # CDU max throughput
        upper[b + 3] = 50.0   # FCC max throughput
        upper[b + 4] = 30.0   # Reformer max throughput
        for k in range(6):
            upper[b + 12 + k] = 25.0  # Tankage inventory bounds [0, 25]

    # Linear objective coefficients (minimization: operating costs - product revenue)
    c = np.zeros(n_cont)
    for t in range(periods):
        b = t * N_PER_T
        c[b + 0] = 70.0    # Arab Light cost ($/bbl)
        c[b + 1] = 62.0    # Basrah cost ($/bbl)
        c[b + 2] = 2.5     # CDU opex ($/bbl)
        c[b + 3] = 4.0     # FCC opex ($/bbl)
        c[b + 4] = 3.0     # Reformer opex ($/bbl)
        c[b + 9] = -115.0  # Gasoline netback revenue ($/bbl)
        c[b + 10] = -105.0 # Diesel netback revenue ($/bbl)
        c[b + 11] = -55.0  # Fuel Oil netback revenue ($/bbl)
        for k in range(6):
            c[b + 12 + k] = 0.5  # Holding cost per period ($/bbl)

    rows = []
    row_lower = []
    row_upper = []

    def add_row(coeffs, lo, hi):
        r = np.zeros(n_cont)
        for idx, val in coeffs:
            r[idx] = val
        rows.append(r)
        row_lower.append(lo)
        row_upper.append(hi)

    init_inv = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

    for t in range(periods):
        b = t * N_PER_T
        b_prev = (t - 1) * N_PER_T

        # 1. CDU feed balance: f_cdu_t - x_c0_t - x_c1_t = 0
        add_row([(b + 2, 1.0), (b + 0, -1.0), (b + 1, -1.0)], 0.0, 0.0)

        # 2. Material balances for intermediate blendstocks:
        # Naphtha: inv_naph_t - inv_naph_{t-1} - 0.25 x_c0 - 0.15 x_c1 + f_ref = 0
        coeffs = [(b + 12, 1.0), (b + 0, -0.25), (b + 1, -0.15), (b + 4, 1.0)]
        if t == 0:
            add_row(coeffs, init_inv[0], init_inv[0])
        else:
            coeffs.append((b_prev + 12, -1.0))
            add_row(coeffs, 0.0, 0.0)

        # Reformate: inv_ref_t - inv_ref_{t-1} - 0.85 f_ref + b_ref_gas = 0
        coeffs = [(b + 13, 1.0), (b + 4, -0.85), (b + 5, 1.0)]
        if t == 0:
            add_row(coeffs, init_inv[1], init_inv[1])
        else:
            coeffs.append((b_prev + 13, -1.0))
            add_row(coeffs, 0.0, 0.0)

        # Distillate: inv_dist_t - inv_dist_{t-1} - 0.45 x_c0 - 0.40 x_c1 + b_dist_dsl = 0
        coeffs = [(b + 14, 1.0), (b + 0, -0.45), (b + 1, -0.40), (b + 7, 1.0)]
        if t == 0:
            add_row(coeffs, init_inv[2], init_inv[2])
        else:
            coeffs.append((b_prev + 14, -1.0))
            add_row(coeffs, 0.0, 0.0)

        # CatGas: inv_cat_t - inv_cat_{t-1} - 0.60 f_fcc + b_cat_gas = 0
        coeffs = [(b + 15, 1.0), (b + 3, -0.60), (b + 6, 1.0)]
        if t == 0:
            add_row(coeffs, init_inv[3], init_inv[3])
        else:
            coeffs.append((b_prev + 15, -1.0))
            add_row(coeffs, 0.0, 0.0)

        # LCO: inv_lco_t - inv_lco_{t-1} - 0.30 f_fcc + b_lco_dsl = 0
        coeffs = [(b + 16, 1.0), (b + 3, -0.30), (b + 8, 1.0)]
        if t == 0:
            add_row(coeffs, init_inv[4], init_inv[4])
        else:
            coeffs.append((b_prev + 16, -1.0))
            add_row(coeffs, 0.0, 0.0)

        # Fuel Oil: inv_fo_t - inv_fo_{t-1} - 0.30 x_c0 - 0.45 x_c1 + f_fcc + s_fo = 0
        coeffs = [(b + 17, 1.0), (b + 0, -0.30), (b + 1, -0.45), (b + 3, 1.0), (b + 11, 1.0)]
        if t == 0:
            add_row(coeffs, init_inv[5], init_inv[5])
        else:
            coeffs.append((b_prev + 17, -1.0))
            add_row(coeffs, 0.0, 0.0)

        # 3. Product blending balances:
        # Gasoline: s_gas - b_ref_gas - b_cat_gas = 0
        add_row([(b + 9, 1.0), (b + 5, -1.0), (b + 6, -1.0)], 0.0, 0.0)
        # Diesel: s_dsl - b_dist_dsl - b_lco_dsl = 0
        add_row([(b + 10, 1.0), (b + 7, -1.0), (b + 8, -1.0)], 0.0, 0.0)

        # 4. Quality specifications:
        # Octane: 98 b_ref + 92 b_cat >= 93 s_gas <=> 5 b_ref - 1 b_cat >= 0
        add_row([(b + 5, 5.0), (b + 6, -1.0)], 0.0, np.inf)
        # Cetane: 52 b_dist + 42 b_lco >= 48 s_dsl <=> 4 b_dist - 6 b_lco >= 0
        add_row([(b + 7, 4.0), (b + 8, -6.0)], 0.0, np.inf)

        # 5. Product demands:
        # Diagnostic infeasible scenario: gasoline demand set to 500.0 (max refinery intake is 100.0)
        dem_gas = 500.0 if v == 'infeasible' else 20.0
        dem_dsl = 30.0
        dem_fo = 10.0
        add_row([(b + 9, 1.0)], dem_gas, np.inf)
        add_row([(b + 10, 1.0)], dem_dsl, np.inf)
        add_row([(b + 11, 1.0)], dem_fo, np.inf)
        if v == 'infeasible':
            upper[b + 9] = 1000.0

    A = np.array(rows, dtype=np.float64)
    row_lower = np.array(row_lower, dtype=np.float64)
    row_upper = np.array(row_upper, dtype=np.float64)

    Q = None
    integer = ()

    if v == 'milp':
        # Add discrete on/off binary variables: y_cdu_t, y_fcc_t, y_ref_t for each period t
        n_bin = 3 * periods
        n_total = n_cont + n_bin

        c_milp = np.zeros(n_total)
        c_milp[:n_cont] = c
        # Fixed operational commitment cost: .0 per operating unit period
        c_milp[n_cont:] = 15.0

        lower_milp = np.zeros(n_total)
        lower_milp[:n_cont] = lower
        upper_milp = np.zeros(n_total)
        upper_milp[:n_cont] = upper
        upper_milp[n_cont:] = 1.0  # binary bounds [0, 1]

        A_milp = np.hstack([A, np.zeros((len(A), n_bin))])
        rows_extra = []
        rlo_extra = []
        rhi_extra = []

        # Coupling constraints:
        # Maximum capacity coupling: f_{u,t} <= U_u * y_{u,t} <=> f_{u,t} - U_u * y_{u,t} <= 0
        # Minimum turndown limit:     f_{u,t} >= L_u * y_{u,t} <=> f_{u,t} - L_u * y_{u,t} >= 0
        unit_caps = [100.0, 50.0, 30.0]
        unit_mins = [20.0, 10.0, 5.0]

        for t in range(periods):
            b = t * N_PER_T
            for u in range(3):
                feed_idx = b + 2 + u
                bin_idx = n_cont + t * 3 + u
                # f - U * y <= 0
                r1 = np.zeros(n_total); r1[feed_idx] = 1.0; r1[bin_idx] = -unit_caps[u]
                rows_extra.append(r1); rlo_extra.append(-np.inf); rhi_extra.append(0.0)
                # f - L * y >= 0
                r2 = np.zeros(n_total); r2[feed_idx] = 1.0; r2[bin_idx] = -unit_mins[u]
                rows_extra.append(r2); rlo_extra.append(0.0); rhi_extra.append(np.inf)

        A = np.vstack([A_milp, rows_extra])
        row_lower = np.concatenate([row_lower, rlo_extra])
        row_upper = np.concatenate([row_upper, rhi_extra])
        c = c_milp
        lower = lower_milp
        upper = upper_milp
        integer = tuple(range(n_cont, n_total))
        for t in range(periods):
            for u in range(3):
                var_names.append(f'y_{["cdu", "fcc", "ref"][u]}_t{t}')

    elif v == 'qp':
        # Genuinely convex operational objective:
        # min C_linear + lambda1 * sum (f_{u,t} - f_{target})^2 + lambda2 * sum (f_{u,t} - f_{u,t-1})^2
        lambda1 = 0.05
        lambda2 = 0.08
        target_feed = [75.0, 35.0, 20.0]

        Q = np.zeros((n_cont, n_cont), dtype=np.float64)
        for t in range(periods):
            b = t * N_PER_T
            for u in range(3):
                idx = b + 2 + u
                # In 0.5 * x^T Q x, diagonal element is 2 * lambda1
                Q[idx, idx] += 2.0 * lambda1
                c[idx] -= 2.0 * lambda1 * target_feed[u]

        # Inter-period throughput swing penalty: lambda2 * (f_{u,t} - f_{u,t-1})^2
        for t in range(1, periods):
            b_prev = (t - 1) * N_PER_T
            b_curr = t * N_PER_T
            for u in range(3):
                idx0 = b_prev + 2 + u
                idx1 = b_curr + 2 + u
                Q[idx0, idx0] += 2.0 * lambda2
                Q[idx1, idx1] += 2.0 * lambda2
                Q[idx0, idx1] -= 2.0 * lambda2
                Q[idx1, idx0] -= 2.0 * lambda2

    return Model(
        c=c, A=A, row_lower=row_lower, row_upper=row_upper,
        lower=lower, upper=upper, integer=integer, Q=Q,
        name=f'MRPL_Refinery_Twin_{v.upper()}',
        names=tuple(var_names)
    )
