"""Branch-and-bound MILP engine with dual simplex basis warm starts,
pseudocost branching, limited strong-branching bootstrap, hybrid
best-bound/depth node selection, verified incumbent propagation,
safe rounding and conservative diving heuristics, and exact rational lower bounds.

Sovereign implementation for SOV-OPT (MRPL Problem Statement 26119).
Zero external solver dependencies.
"""
from collections import defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction as F
import math
import time
from typing import Optional, List, Dict, Any, Tuple, Union

import numpy as np

from .model import Model
from .dual_simplex import solve_dual_simplex, DualBasisState
from .simplex import solve_lp
from .verify import verify, safe_lower_bound, downward_float, upward_float
from .cuts import CutConfig, CutPool, separate_cover_cuts, append_rows_to_matrix


@dataclass
class MILPNode:
    """Represents an active or evaluated node in the branch-and-bound search tree."""
    node_id: int
    parent_id: Optional[int]
    depth: int
    branch_variable: Optional[int]
    branch_direction: Optional[str]  # 'down' or 'up'
    branch_value: Optional[float]
    local_lower_bounds: np.ndarray
    local_upper_bounds: np.ndarray
    certified_lp_bound: Any  # Fraction or -math.inf
    lp_status: Optional[str]
    basis_state: Optional[DualBasisState]
    warm_start_source: Optional[str]  # 'parent', 'strong_branch', None
    creation_order: int
    x_sol: Optional[np.ndarray] = None


def exact_objective(model: Model, x: np.ndarray) -> F:
    """Compute exact objective in internal minimization space.
    Rounds declared integer variables to exact integers, while continuous variables
    are converted losslessly from float to Fraction.
    """
    val = F(0)
    for j, c in enumerate(model.c):
        c_F = F(float(c))
        if j in model.integer:
            x_F = F(int(round(x[j])))
        else:
            x_F = F(float(x[j]))
        val += c_F * x_F
    return val


def solve_milp(model: Model, tol: float = 1e-7, max_nodes: int = 1000,
               time_limit: float = 30.0,
               parallel_workers: int = 1,
               use_warm_starts: bool = True,
               use_pseudocosts: bool = True,
               use_strong_branching: bool = True,
               use_heuristics: bool = True,
               use_cuts: bool = True,
               node_selection: str = 'hybrid',
               cut_config: Optional[CutConfig] = None,
               **kwargs) -> Dict[str, Any]:
    """Solve mixed-integer linear programming (MILP) problem via sovereign B&B.

    Features:
    - Intra-solve parallel multi-process search when parallel_workers > 1.
    - Parent/child LP basis warm starts using DualBasisState.
    - Pseudocost branching with history tracking and dynamic initialization.
    - Limited strong-branching bootstrap on unreliable candidates.
    - Hybrid best-bound / depth node selection policy.
    - Verified incumbent propagation against untouched original model.
    - Safe rounding heuristic with continuous subproblem solve.
    - Conservative diving heuristic from root LP.
    - Sovereign cutting planes (Binary Cover Cuts) at root node.
    - Rigorous Neumaier-Shcherbina exact rational Lagrangian lower bounds.
    - Objective offset handling in exact rational arithmetic.
    - Comprehensive MILP telemetry tracking.
    """
    workers_req = kwargs.get('workers', parallel_workers)
    engine_req = kwargs.get('engine', 'auto')
    if workers_req > 1 or engine_req == 'parallel':
        from .parallel_bnb import solve_milp_parallel
        return solve_milp_parallel(
            model=model, tol=tol, max_nodes=max_nodes, time_limit=time_limit,
            parallel_workers=workers_req,
            use_warm_starts=use_warm_starts,
            use_pseudocosts=use_pseudocosts,
            use_strong_branching=use_strong_branching,
            use_heuristics=use_heuristics,
            use_cuts=use_cuts,
            node_selection=node_selection,
            cut_config=cut_config,
            **kwargs
        )

    start_time = time.perf_counter()
    orig_model = model

    # Root lower bound from variable box:
    def box_lb(m: Model) -> Union[F, float]:
        b = F(0)
        for c, l, u in zip(m.c, m.lower, m.upper):
            c_f = float(c)
            if c_f > 0:
                if not math.isfinite(l):
                    return -math.inf
                b += F(c_f) * F(float(l))
            elif c_f < 0:
                if not math.isfinite(u):
                    return -math.inf
                b += F(c_f) * F(float(u))
        return b

    rootlb = box_lb(model)
    lo = model.lower.copy()
    hi = model.upper.copy()
    for j in model.integer:
        if math.isfinite(lo[j]): lo[j] = math.ceil(lo[j])
        if math.isfinite(hi[j]): hi[j] = math.floor(hi[j])

    offset_F = F(float(model.obj_offset)) if model.obj_offset != 0.0 else F(0)

    if np.any(lo > hi):
        return {
            'status': 'INFEASIBLE_CERTIFIED',
            'message': 'An integer variable has no integer in its box',
            'algorithm': 'rational-bound branch-and-bound',
            'nodes': 0,
        }

    # Handle immediate max_nodes <= 0 constraint honestly
    if max_nodes <= 0:
        if not model.maximize:
            rep_bound = downward_float(rootlb + offset_F) if rootlb != -math.inf else -math.inf
        else:
            rep_bound = upward_float(-rootlb + offset_F) if rootlb != -math.inf else math.inf
        return {
            'status': 'LIMIT_REACHED',
            'algorithm': 'rational-bound branch-and-bound',
            'nodes': 0,
            'best_bound': rep_bound,
            'open_nodes': 1,
            'tolerance_closed_nodes': 0,
            'pruned_nodes': 0,
            'history': [],
            'message': 'Search halted at node limit 0',
        }

    # Telemetry counters
    telemetry = {
        'warm_starts_attempted': 0,
        'warm_starts_accepted': 0,
        'warm_starts_rejected': 0,
        'warm_start_pivots_total': 0,
        'cold_start_pivots_total': 0,
        'strong_branching_evaluations': 0,
        'heuristics_attempted': 0,
        'heuristics_found_incumbent': 0,
        'pruned_by_bound': 0,
        'pruned_by_infeasibility': 0,
        'pruned_by_integrality': 0,
        'root_lp_iterations': 0,
        'root_lp_time': 0.0,
        'root_lp_bound': None,
        'deadline_checks': 0,
        'cuts_enabled': bool(kwargs.get('cuts_enabled', use_cuts)),
        'cut_rounds': 0,
        'cuts_generated': 0,
        'cuts_accepted': 0,
        'cover_cuts_generated': 0,
        'cover_cuts_accepted': 0,
        'gomory_or_gmi_generated': 0,
        'gomory_or_gmi_accepted': 0,
        'root_bound_before_cuts': None,
        'root_bound_after_cuts': None,
        'root_bound_improvement_abs': 0.0,
        'root_bound_improvement_pct': 0.0,
        'cut_time_seconds': 0.0,
    }

    # Pseudocost data structures
    down_count: Dict[int, int] = defaultdict(int)
    down_sum: Dict[int, float] = defaultdict(float)
    up_count: Dict[int, int] = defaultdict(int)
    up_sum: Dict[int, float] = defaultdict(float)

    # LP solver helper with warm start and fallbacks
    deadline = start_time + time_limit

    def check_deadline() -> bool:
        telemetry['deadline_checks'] += 1
        return time.perf_counter() >= deadline

    def solve_node_lp(node_model: Model, basis_state: Optional[DualBasisState],
                      max_iter: Optional[int] = None) -> Dict[str, Any]:
        if check_deadline():
            return {'status': 'LIMIT_REACHED', 'message': 'Time limit reached'}

        n_total = len(node_model.A) + len(node_model.c)
        effective_iter = max_iter if max_iter is not None else min(1500, max(250, 3 * n_total))

        attempted_warm = use_warm_starts and (basis_state is not None)
        if attempted_warm:
            telemetry['warm_starts_attempted'] += 1
            res = solve_dual_simplex(node_model, basis_state=basis_state,
                                     presolve=False, scaling=False, tol=tol,
                                     max_iter=effective_iter, deadline=deadline)
            if res.get('warm_start_accepted', False) and res['status'] in ('OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED'):
                telemetry['warm_starts_accepted'] += 1
                telemetry['warm_start_pivots_total'] += res.get('iterations', 0)
                return res
            if res.get('status') == 'LIMIT_REACHED':
                return res
            telemetry['warm_starts_rejected'] += 1

        if check_deadline():
            return {'status': 'LIMIT_REACHED', 'message': 'Time limit reached'}

        # Cold dual simplex solve
        res = solve_dual_simplex(node_model, basis_state=None,
                                 presolve=False, scaling=False, tol=tol,
                                 max_iter=effective_iter, deadline=deadline)
        if res['status'] in ('OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED', 'LIMIT_REACHED'):
            telemetry['cold_start_pivots_total'] += res.get('iterations', 0)
            return res

        if check_deadline():
            return {'status': 'LIMIT_REACHED', 'message': 'Time limit reached'}

        # Cold primal simplex fallback
        res_primal = solve_lp(node_model, tol=tol, max_iter=effective_iter, deadline=deadline)
        telemetry['cold_start_pivots_total'] += res_primal.get('iterations', 0)
        return res_primal

    # Solve root node
    t0_root = time.perf_counter()
    root_model = replace(model, lower=lo, upper=hi, integer=())
    res_root = solve_node_lp(root_model, basis_state=None)
    nodes = 1
    t_root_elapsed = time.perf_counter() - t0_root
    telemetry['root_lp_iterations'] = res_root.get('iterations', 0)
    telemetry['root_lp_time'] = t_root_elapsed

    if res_root['status'] == 'INFEASIBLE_CERTIFIED':
        return {
            'status': 'INFEASIBLE_CERTIFIED',
            'algorithm': 'rational-bound branch-and-bound',
            'nodes': 1,
            'message': 'Root LP relaxation is infeasible',
            'best_bound': math.inf,
            'configured_time_limit': float(time_limit),
            'measured_runtime': float(time.perf_counter() - start_time),
            'deadline_checks': int(telemetry['deadline_checks']),
            'telemetry': telemetry,
        }

    if res_root['status'] == 'LIMIT_REACHED':
        return {
            'status': 'LIMIT_REACHED',
            'algorithm': 'rational-bound branch-and-bound',
            'nodes': 1,
            'message': 'Time limit reached during root LP relaxation',
            'best_bound': -math.inf,
            'configured_time_limit': float(time_limit),
            'measured_runtime': float(time.perf_counter() - start_time),
            'deadline_checks': int(telemetry['deadline_checks']),
            'telemetry': telemetry,
        }

    if res_root['status'] != 'OPTIMAL_VERIFIED':
        return {
            'status': 'NUMERICAL_FAILURE',
            'algorithm': 'rational-bound branch-and-bound',
            'nodes': 1,
            'message': 'Root LP relaxation could not be solved: ' + res_root.get('message', res_root['status']),
            'best_bound': -math.inf,
            'configured_time_limit': float(time_limit),
            'measured_runtime': float(time.perf_counter() - start_time),
            'deadline_checks': int(telemetry['deadline_checks']),
            'telemetry': telemetry,
        }

    slb_root = safe_lower_bound(root_model, res_root.get('dual_exact_fraction', res_root.get('dual')))
    root_bound = slb_root if slb_root is not None else rootlb
    telemetry['root_lp_bound'] = downward_float(root_bound) if root_bound != -math.inf else -math.inf
    telemetry['root_bound_before_cuts'] = telemetry['root_lp_bound']
    telemetry['root_bound_after_cuts'] = telemetry['root_lp_bound']
    x_root = np.array(res_root['x'])

    # Root Node Cutting Plane Loop
    frac_root = [j for j in model.integer if abs(x_root[j] - round(x_root[j])) > tol]
    if frac_root and telemetry['cuts_enabled']:
        cfg = cut_config or CutConfig()
        cut_pool = CutPool(cfg)
        t0_cuts = time.perf_counter()

        for round_idx in range(cfg.max_cut_rounds_root):
            if check_deadline():
                break
            frac_curr = [j for j in model.integer if abs(x_root[j] - round(x_root[j])) > tol]
            if not frac_curr:
                break

            # Separate cover cuts from current root relaxation
            new_cover_cuts = separate_cover_cuts(root_model, x_root, config=cfg, source_node=1,
                                                 integer_vars=model.integer)
            telemetry['cover_cuts_generated'] += len(new_cover_cuts)
            telemetry['cuts_generated'] += len(new_cover_cuts)

            round_accepted = []
            for c in new_cover_cuts:
                if cut_pool.add(c):
                    round_accepted.append(c)
                    telemetry['cover_cuts_accepted'] += 1
                    telemetry['cuts_accepted'] += 1
                    if len(round_accepted) >= cfg.max_cuts_per_round:
                        break

            if not round_accepted:
                break

            # Augment root model with accepted cuts
            k_cuts = len(round_accepted)
            cut_coeffs = np.array([c.coefficients for c in round_accepted], dtype=np.float64)
            cut_rhs = np.array([c.rhs for c in round_accepted], dtype=np.float64)

            aug_A = append_rows_to_matrix(root_model.A, cut_coeffs)
            aug_rl = np.concatenate([root_model.row_lower, np.full(k_cuts, -np.inf)])
            aug_ru = np.concatenate([root_model.row_upper, cut_rhs])
            aug_model = replace(root_model, A=aug_A, row_lower=aug_rl, row_upper=aug_ru)

            # Re-solve root LP relaxation
            res_aug = solve_node_lp(aug_model, basis_state=None)
            if res_aug.get('status') == 'OPTIMAL_VERIFIED':
                root_model = aug_model
                res_root = res_aug
                x_root = np.array(res_aug['x'])
                telemetry['cut_rounds'] += 1

                # Recompute exact rational safe lower bound
                slb_aug = safe_lower_bound(root_model, res_aug.get('dual_exact_fraction', res_aug.get('dual')))
                if slb_aug is not None:
                    if root_bound == -math.inf or slb_aug > root_bound:
                        root_bound = slb_aug
                        telemetry['root_lp_bound'] = downward_float(root_bound)
                        telemetry['root_bound_after_cuts'] = telemetry['root_lp_bound']
            else:
                break

        telemetry['cut_time_seconds'] = float(time.perf_counter() - t0_cuts)

        # Compute bound improvement
        b_before = telemetry['root_bound_before_cuts']
        b_after = telemetry['root_bound_after_cuts']
        if b_before is not None and b_after is not None and b_before != -math.inf and b_after != -math.inf:
            imp_abs = max(0.0, float(b_after - b_before))
            telemetry['root_bound_improvement_abs'] = imp_abs
            telemetry['root_bound_improvement_pct'] = float((imp_abs / max(1.0, abs(float(b_before)))) * 100.0)

        # Augment active model for child nodes if cuts were added
        if telemetry['cuts_accepted'] > 0:
            model = replace(model, A=root_model.A, row_lower=root_model.row_lower, row_upper=root_model.row_upper)

    root_node = MILPNode(
        node_id=1,
        parent_id=None,
        depth=0,
        branch_variable=None,
        branch_direction=None,
        branch_value=None,
        local_lower_bounds=lo.copy(),
        local_upper_bounds=hi.copy(),
        certified_lp_bound=root_bound,
        lp_status='OPTIMAL_VERIFIED',
        basis_state=res_root.get('basis_state'),
        warm_start_source=None,
        creation_order=1,
        x_sol=x_root,
    )

    inc: Optional[np.ndarray] = None
    incval: Optional[F] = None
    incumbent_history: List[Dict[str, Any]] = []
    tolerance_closed: List[F] = []
    open_nodes: List[MILPNode] = []
    serial = 1

    # Check root integrality
    fractional = [j for j in model.integer if abs(x_root[j] - round(x_root[j])) > tol]
    if not fractional:
        xr = x_root.copy()
        for j in model.integer:
            xr[j] = round(xr[j])
        vr = verify(orig_model, xr, tol=tol)
        val = exact_objective(orig_model, xr)
        if vr['feasible']:
            inc = xr
            incval = val
            tolerance_closed.append(val)
            incumbent_history.append({
                'node_id': 1,
                'objective': float(val),
                'source': 'root_integrality',
                'time': time.perf_counter() - start_time,
            })
        else:
            return {'status': 'NUMERICAL_FAILURE', 'message': 'Root integral node could not be verified'}
    else:
        open_nodes.append(root_node)

        # Heuristics at root node
        if use_heuristics and time.perf_counter() < deadline:
            # Safe Rounding Heuristic
            telemetry['heuristics_attempted'] += 1
            can_round = all(abs(x_root[j] - round(x_root[j])) <= 0.4 for j in model.integer)
            if can_round and time.perf_counter() < deadline:
                x_cand = x_root.copy()
                round_feasible = True
                for j in model.integer:
                    rj = round(x_root[j])
                    if rj < lo[j] - tol or rj > hi[j] + tol:
                        round_feasible = False
                        break
                    x_cand[j] = rj
                if round_feasible and time.perf_counter() < deadline:
                    lo_fix = lo.copy()
                    hi_fix = hi.copy()
                    for j in model.integer:
                        lo_fix[j] = x_cand[j]
                        hi_fix[j] = x_cand[j]
                    m_sub = replace(model, lower=lo_fix, upper=hi_fix, integer=())
                    res_sub = solve_node_lp(m_sub, basis_state=res_root.get('basis_state'), max_iter=100)
                    if res_sub['status'] == 'OPTIMAL_VERIFIED':
                        x_sub = np.array(res_sub['x'])
                        v_sub = verify(model, x_sub, tol=tol)
                        if v_sub['feasible']:
                            val_sub = exact_objective(model, x_sub)
                            if incval is None or val_sub < incval:
                                inc = x_sub
                                incval = val_sub
                                telemetry['heuristics_found_incumbent'] += 1
                                incumbent_history.append({
                                    'node_id': 1,
                                    'objective': float(val_sub),
                                    'source': 'safe_rounding',
                                    'time': time.perf_counter() - start_time,
                                })

            # Conservative Diving Heuristic from root
            if time.perf_counter() < deadline:
                telemetry['heuristics_attempted'] += 1
                try:
                    dive_lo = lo.copy()
                    dive_hi = hi.copy()
                    dive_basis = res_root.get('basis_state')
                    dive_x = x_root.copy()
                    dive_success = False
                    for step in range(8):
                        if time.perf_counter() >= deadline:
                            break
                        frac_dive = [j for j in model.integer if abs(dive_x[j] - round(dive_x[j])) > tol]
                        if not frac_dive:
                            dive_success = True
                            break
                        j_dive = min(frac_dive, key=lambda j: abs(dive_x[j] - round(dive_x[j])))
                        r_val = round(dive_x[j_dive])
                        if r_val < dive_lo[j_dive] or r_val > dive_hi[j_dive]:
                            break
                        dive_lo[j_dive] = r_val
                        dive_hi[j_dive] = r_val
                        m_dive = replace(model, lower=dive_lo, upper=dive_hi, integer=())
                        res_dive = solve_dual_simplex(m_dive, basis_state=dive_basis, presolve=False,
                                                      scaling=False, tol=tol, max_iter=50, deadline=deadline)
                        if res_dive['status'] != 'OPTIMAL_VERIFIED':
                            break
                        dive_x = np.array(res_dive['x'])
                        dive_basis = res_dive.get('basis_state')

                    if dive_success:
                        xr_dive = dive_x.copy()
                        for j in model.integer:
                            xr_dive[j] = round(xr_dive[j])
                        vr_dive = verify(model, xr_dive, tol=tol)
                        if vr_dive['feasible']:
                            val_dive = exact_objective(model, xr_dive)
                            if incval is None or val_dive < incval:
                                inc = xr_dive
                                incval = val_dive
                                telemetry['heuristics_found_incumbent'] += 1
                                incumbent_history.append({
                                    'node_id': 1,
                                    'objective': float(val_dive),
                                    'source': 'conservative_diving',
                                    'time': time.perf_counter() - start_time,
                                })
                except Exception:
                    pass

    history: List[Dict[str, Any]] = []
    failure: Optional[str] = None

    # Step 7: Node Selection Helper
    def select_next_node() -> Optional[int]:
        if not open_nodes:
            return None
        if node_selection == 'best_bound' or incval is None:
            # Pure best bound
            best_idx = 0
            best_bound = open_nodes[0].certified_lp_bound
            for i in range(1, len(open_nodes)):
                b = open_nodes[i].certified_lp_bound
                if best_bound != -math.inf and (b == -math.inf or b < best_bound):
                    best_bound = b
                    best_idx = i
                elif b == best_bound:
                    if open_nodes[i].depth > open_nodes[best_idx].depth or (
                        open_nodes[i].depth == open_nodes[best_idx].depth and open_nodes[i].creation_order < open_nodes[best_idx].creation_order
                    ):
                        best_idx = i
            return best_idx
        else:
            # Hybrid Best-Bound / Depth
            min_bound = None
            for n in open_nodes:
                b = n.certified_lp_bound
                if b == -math.inf:
                    min_bound = -math.inf
                    break
                if min_bound is None or b < min_bound:
                    min_bound = b

            if min_bound == -math.inf:
                for i, n in enumerate(open_nodes):
                    if n.certified_lp_bound == -math.inf:
                        return i

            thresh = float(min_bound) + 0.15 * max(1.0, abs(float(min_bound)))
            best_idx = -1
            best_key = None
            for i, n in enumerate(open_nodes):
                if float(n.certified_lp_bound) <= thresh + 1e-9:
                    cand_key = (-n.depth, n.certified_lp_bound, n.creation_order)
                    if best_key is None or cand_key < best_key:
                        best_key = cand_key
                        best_idx = i
            return best_idx if best_idx != -1 else 0

    # Step 4 & 5: Strong Branching Bootstrap & Branch Variable Selection
    def select_branching_variable(parent_node: MILPNode, fractional_vars: List[int]) -> int:
        if not use_pseudocosts:
            # Classic most-fractional variable selection
            return max(fractional_vars, key=lambda j: min(parent_node.x_sol[j] - math.floor(parent_node.x_sol[j]),
                                                          math.ceil(parent_node.x_sol[j]) - parent_node.x_sol[j]))

        avg_down = (sum(down_sum.values()) / max(1, sum(down_count.values()))) if sum(down_count.values()) > 0 else 1.0
        avg_up = (sum(up_sum.values()) / max(1, sum(up_count.values()))) if sum(up_count.values()) > 0 else 1.0
        if avg_down <= 0.0: avg_down = 1.0
        if avg_up <= 0.0: avg_up = 1.0

        # Strong branching bootstrap on unreliable candidates
        if use_strong_branching and parent_node.basis_state is not None and time.perf_counter() < deadline:
            K_reliable = 2
            unreliable = [j for j in fractional_vars if min(down_count[j], up_count[j]) < K_reliable]
            if unreliable:
                unreliable.sort(key=lambda j: abs(parent_node.x_sol[j] - round(parent_node.x_sol[j]) - 0.5))
                eval_candidates = unreliable[:4]

                for cand_j in eval_candidates:
                    if time.perf_counter() >= deadline:
                        break
                    xj = parent_node.x_sol[cand_j]
                    f_down = xj - math.floor(xj)
                    f_up = math.ceil(xj) - xj
                    telemetry['strong_branching_evaluations'] += 1

                    # Evaluate down
                    lo_d = parent_node.local_lower_bounds.copy()
                    hi_d = parent_node.local_upper_bounds.copy()
                    hi_d[cand_j] = min(hi_d[cand_j], math.floor(xj))
                    if lo_d[cand_j] <= hi_d[cand_j]:
                        m_d = replace(model, lower=lo_d, upper=hi_d, integer=())
                        res_d = solve_dual_simplex(m_d, basis_state=parent_node.basis_state,
                                                   presolve=False, scaling=False, tol=tol, max_iter=50,
                                                   deadline=deadline)
                        if res_d['status'] == 'OPTIMAL_VERIFIED':
                            dz = max(0.0, res_d['objective'] - float(parent_node.certified_lp_bound if parent_node.certified_lp_bound != -math.inf else res_d['objective']))
                            down_count[cand_j] += 1
                            down_sum[cand_j] += dz / max(f_down, 1e-4)

                    if time.perf_counter() >= deadline:
                        break

                    # Evaluate up
                    lo_u = parent_node.local_lower_bounds.copy()
                    hi_u = parent_node.local_upper_bounds.copy()
                    lo_u[cand_j] = max(lo_u[cand_j], math.ceil(xj))
                    if lo_u[cand_j] <= hi_u[cand_j]:
                        m_u = replace(model, lower=lo_u, upper=hi_u, integer=())
                        res_u = solve_dual_simplex(m_u, basis_state=parent_node.basis_state,
                                                   presolve=False, scaling=False, tol=tol, max_iter=50,
                                                   deadline=deadline)
                        if res_u['status'] == 'OPTIMAL_VERIFIED':
                            dz = max(0.0, res_u['objective'] - float(parent_node.certified_lp_bound if parent_node.certified_lp_bound != -math.inf else res_u['objective']))
                            up_count[cand_j] += 1
                            up_sum[cand_j] += dz / max(f_up, 1e-4)

        # Score all fractional candidates
        best_j = fractional_vars[0]
        best_score = -1.0
        for j in fractional_vars:
            xj = parent_node.x_sol[j]
            f_down = xj - math.floor(xj)
            f_up = math.ceil(xj) - xj

            psi_down = (down_sum[j] / down_count[j]) if down_count[j] > 0 else avg_down
            psi_up = (up_sum[j] / up_count[j]) if up_count[j] > 0 else avg_up

            q_down = max(psi_down * f_down, 1e-6)
            q_up = max(psi_up * f_up, 1e-6)
            score = q_down * q_up

            if score > best_score:
                best_score = score
                best_j = j
            elif score == best_score and j < best_j:
                best_j = j
        return best_j

    # Main Branch & Bound Search Loop
    while open_nodes and nodes < max_nodes and (time.perf_counter() - start_time < time_limit):
        idx = select_next_node()
        current_node = open_nodes.pop(idx)

        # Prune if bound exceeds incumbent
        if incval is not None and current_node.certified_lp_bound != -math.inf and current_node.certified_lp_bound >= incval:
            telemetry['pruned_by_bound'] += 1
            continue

        x_curr = current_node.x_sol
        frac_vars = [j for j in model.integer if abs(x_curr[j] - round(x_curr[j])) > tol]
        if not frac_vars:
            xr = x_curr.copy()
            for j in model.integer:
                xr[j] = round(xr[j])
            vr = verify(model, xr, tol=tol)
            val = exact_objective(model, xr)
            if vr['feasible']:
                if incval is None or val < incval:
                    inc = xr
                    incval = val
                    incumbent_history.append({
                        'node_id': current_node.node_id,
                        'objective': float(val),
                        'source': 'integrality',
                        'time': time.perf_counter() - start_time,
                    })
                tolerance_closed.append(val)
                telemetry['pruned_by_integrality'] += 1
            continue

        # Select branching variable
        branch_var = select_branching_variable(current_node, frac_vars)
        xj = current_node.x_sol[branch_var]
        f_down = xj - math.floor(xj)
        f_up = math.ceil(xj) - xj

        branches = [
            ('down', math.floor(xj), True),
            ('up', math.ceil(xj), False),
        ]

        for dir_name, b_val, is_down in branches:
            l_b = current_node.local_lower_bounds.copy()
            u_b = current_node.local_upper_bounds.copy()
            if is_down:
                u_b[branch_var] = min(u_b[branch_var], b_val)
            else:
                l_b[branch_var] = max(l_b[branch_var], b_val)

            # Bound conflict pruning
            if l_b[branch_var] > u_b[branch_var]:
                telemetry['pruned_by_infeasibility'] += 1
                continue

            serial += 1
            # Check limits before solving child LP
            if nodes >= max_nodes or (time.perf_counter() - start_time >= time_limit):
                unsolved_node = MILPNode(
                    node_id=serial,
                    parent_id=current_node.node_id,
                    depth=current_node.depth + 1,
                    branch_variable=branch_var,
                    branch_direction=dir_name,
                    branch_value=b_val,
                    local_lower_bounds=l_b,
                    local_upper_bounds=u_b,
                    certified_lp_bound=current_node.certified_lp_bound,
                    lp_status='UNRESOLVED',
                    basis_state=current_node.basis_state,
                    warm_start_source='parent',
                    creation_order=serial,
                    x_sol=current_node.x_sol,
                )
                open_nodes.append(unsolved_node)
                continue

            # Solve child LP
            child_model = replace(model, lower=l_b, upper=u_b, integer=())
            res_child = solve_node_lp(child_model, basis_state=current_node.basis_state)
            nodes += 1

            if res_child['status'] == 'INFEASIBLE_CERTIFIED':
                telemetry['pruned_by_infeasibility'] += 1
                continue

            if res_child['status'] != 'OPTIMAL_VERIFIED':
                failure = 'Unresolved child LP relaxation: ' + res_child.get('message', res_child['status'])
                unsolved_node = MILPNode(
                    node_id=serial,
                    parent_id=current_node.node_id,
                    depth=current_node.depth + 1,
                    branch_variable=branch_var,
                    branch_direction=dir_name,
                    branch_value=b_val,
                    local_lower_bounds=l_b,
                    local_upper_bounds=u_b,
                    certified_lp_bound=current_node.certified_lp_bound,
                    lp_status=res_child['status'],
                    basis_state=None,
                    warm_start_source='parent',
                    creation_order=serial,
                    x_sol=current_node.x_sol,
                )
                open_nodes.append(unsolved_node)
                break

            # Certified rational lower bound
            slb_child = safe_lower_bound(child_model, res_child.get('dual_exact_fraction', res_child.get('dual')))
            if slb_child is not None:
                child_bound = slb_child if current_node.certified_lp_bound == -math.inf else max(current_node.certified_lp_bound, slb_child)
            else:
                child_bound = current_node.certified_lp_bound

            # Update pseudocosts
            child_obj = float(res_child['objective'])
            parent_obj = float(current_node.certified_lp_bound if current_node.certified_lp_bound != -math.inf else child_obj)
            dz = max(0.0, child_obj - parent_obj)
            if is_down:
                down_count[branch_var] += 1
                down_sum[branch_var] += dz / max(f_down, 1e-4)
            else:
                up_count[branch_var] += 1
                up_sum[branch_var] += dz / max(f_up, 1e-4)

            # Bound cutoff check
            if incval is not None and child_bound != -math.inf and child_bound >= incval:
                telemetry['pruned_by_bound'] += 1
                continue

            x_child = np.array(res_child['x'])
            child_frac = [j for j in model.integer if abs(x_child[j] - round(x_child[j])) > tol]
            if not child_frac:
                xr = x_child.copy()
                for j in model.integer:
                    xr[j] = round(xr[j])
                vr = verify(model, xr, tol=tol)
                val = exact_objective(model, xr)
                if vr['feasible']:
                    if incval is None or val < incval:
                        inc = xr
                        incval = val
                        incumbent_history.append({
                            'node_id': serial,
                            'objective': float(val),
                            'source': 'integrality',
                            'time': time.perf_counter() - start_time,
                        })
                    tolerance_closed.append(val if child_bound == -math.inf else max(child_bound, val))
                    telemetry['pruned_by_integrality'] += 1
                else:
                    child_node = MILPNode(
                        node_id=serial,
                        parent_id=current_node.node_id,
                        depth=current_node.depth + 1,
                        branch_variable=branch_var,
                        branch_direction=dir_name,
                        branch_value=b_val,
                        local_lower_bounds=l_b,
                        local_upper_bounds=u_b,
                        certified_lp_bound=child_bound,
                        lp_status='OPTIMAL_VERIFIED',
                        basis_state=res_child.get('basis_state'),
                        warm_start_source='parent',
                        creation_order=serial,
                        x_sol=x_child,
                    )
                    open_nodes.append(child_node)
            else:
                child_node = MILPNode(
                    node_id=serial,
                    parent_id=current_node.node_id,
                    depth=current_node.depth + 1,
                    branch_variable=branch_var,
                    branch_direction=dir_name,
                    branch_value=b_val,
                    local_lower_bounds=l_b,
                    local_upper_bounds=u_b,
                    certified_lp_bound=child_bound,
                    lp_status='OPTIMAL_VERIFIED',
                    basis_state=res_child.get('basis_state'),
                    warm_start_source='parent',
                    creation_order=serial,
                    x_sol=x_child,
                )
                open_nodes.append(child_node)

        history.append({
            'nodes': nodes,
            'open_nodes': len(open_nodes),
            'incumbent': None if incval is None else float(incval),
            'node_bound': downward_float(current_node.certified_lp_bound) if current_node.certified_lp_bound != -math.inf else None,
        })

    # Exhaustive accounting of all tree regions:
    open_bounds = [n.certified_lp_bound for n in open_nodes]
    tolerance_bounds = list(tolerance_closed)

    if incval is not None:
        candidates = open_bounds + tolerance_bounds + [incval]
        global_lower = -math.inf if any(c == -math.inf for c in candidates) else min(candidates)
    else:
        if open_bounds:
            global_lower = -math.inf if any(b == -math.inf for b in open_bounds) else min(open_bounds)
        elif tolerance_bounds:
            global_lower = -math.inf if any(b == -math.inf for b in tolerance_bounds) else min(tolerance_bounds)
        else:
            global_lower = None

    result = {
        'algorithm': 'rational-bound branch-and-bound',
        'nodes': nodes,
        'history': history,
        'bound_kind': 'exact rational Lagrangian bounds of binary64 input',
        'open_nodes': len(open_nodes),
        'tolerance_closed_nodes': len(tolerance_closed),
        'pruned_nodes': telemetry['pruned_by_bound'] + telemetry['pruned_by_infeasibility'] + telemetry['pruned_by_integrality'],
        'incumbent_history': incumbent_history,
        'selection_strategy': 'hybrid best-bound/depth' if node_selection == 'hybrid' else 'best-bound',
        'branching_strategy': 'pseudocost with strong branching bootstrap' if use_pseudocosts else 'most-fractional',
        'configured_time_limit': float(time_limit),
        'measured_runtime': float(time.perf_counter() - start_time),
        'deadline_checks': int(telemetry['deadline_checks']),
    }
    result.update(telemetry)

    # Sense mapping (minimization vs maximization)
    if not model.maximize:
        if global_lower is not None and global_lower != -math.inf:
            reported_lower = downward_float(global_lower + offset_F)
        elif global_lower == -math.inf:
            reported_lower = -math.inf
        else:
            reported_lower = None
        result['best_bound'] = reported_lower

        if inc is not None:
            reported_obj = float(incval + offset_F)
            gap = max(0.0, float(incval - global_lower)) / (1.0 + abs(reported_obj)) if global_lower not in (None, -math.inf) else float('inf')
            vr = verify(orig_model, inc, tol=tol)
            result.update(x=inc.tolist(), objective=reported_obj, verification=vr, relative_gap=gap)
            if not open_nodes and not failure and gap <= tol:
                result['status'] = 'OPTIMAL_VERIFIED'
                result['verification']['optimality_basis'] = (
                    f'finite B&B tree with exact rational lower bounds; incumbent feasibility verified numerically; '
                    f'relative gap {gap:.2e} <= {tol:.2e}'
                )
            elif failure:
                result['status'] = 'NUMERICAL_FAILURE'
                result['verification']['optimality_basis'] = 'B&B search halted on unresolved LP node; conservative lower bound preserved'
            else:
                result['status'] = 'LIMIT_REACHED'
                result['verification']['optimality_basis'] = 'B&B search halted at limit; conservative lower bound from exhaustive open frontier and terminal leaves'
        else:
            result['status'] = 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if open_nodes else 'INFEASIBLE_CERTIFIED'
    else:
        if global_lower is not None and global_lower != -math.inf:
            reported_upper = upward_float(-global_lower + offset_F)
        elif global_lower == -math.inf:
            reported_upper = math.inf
        else:
            reported_upper = None
        result['best_bound'] = reported_upper

        if inc is not None:
            reported_obj = float(-incval + offset_F)
            gap = max(0.0, float(incval - global_lower)) / (1.0 + abs(reported_obj)) if global_lower not in (None, -math.inf) else float('inf')
            vr = verify(orig_model, inc, tol=tol)
            result.update(x=inc.tolist(), objective=reported_obj, verification=vr, relative_gap=gap)
            if not open_nodes and not failure and gap <= tol:
                result['status'] = 'OPTIMAL_VERIFIED'
                result['verification']['optimality_basis'] = (
                    f'finite B&B tree with exact rational lower bounds; incumbent feasibility verified numerically; '
                    f'relative gap {gap:.2e} <= {tol:.2e}'
                )
            elif failure:
                result['status'] = 'NUMERICAL_FAILURE'
            else:
                result['status'] = 'LIMIT_REACHED'
        else:
            result['status'] = 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if open_nodes else 'INFEASIBLE_CERTIFIED'

    # Update summary telemetry
    telemetry['nodes_explored'] = nodes
    telemetry['nodes_pruned'] = telemetry['pruned_by_bound'] + telemetry['pruned_by_infeasibility'] + telemetry['pruned_by_integrality']
    telemetry['incumbent'] = result.get('objective')
    telemetry['best_bound'] = result.get('best_bound')
    telemetry['final_gap'] = result.get('relative_gap', float('inf'))
    result.update(telemetry)

    if failure:
        result['message'] = failure
    return result

