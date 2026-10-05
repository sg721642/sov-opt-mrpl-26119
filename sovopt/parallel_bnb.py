"""Intra-solve parallel branch-and-bound engine for SOV-OPT.

Provides multi-process tree search with:
- Authoritative coordinator process managing queue, global bounds, and incumbent.
- Multi-process worker pool solving node LP relaxations concurrently.
- Shared incumbent propagation with conservative coordinator-side verification.
- Safe exact-rational global lower-bound accounting including in-flight nodes.
- Full compatibility with Gate 20C root cover cuts.
- Robust worker-failure recovery and deterministic fallback.

Sovereign implementation for SOV-OPT (MRPL Problem Statement 26119).
Dependencies: Python standard library and NumPy only.
"""
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import replace
from fractions import Fraction as F
import math
import os
import time
from typing import Optional, List, Dict, Any, Tuple, Union

import numpy as np

from .model import Model
from .dual_simplex import solve_dual_simplex, DualBasisState
from .simplex import solve_lp
from .verify import verify, safe_lower_bound, downward_float, upward_float
from .cuts import CutConfig, CutPool, separate_cover_cuts, append_rows_to_matrix
from .milp import MILPNode, exact_objective


# Global worker state (initialized once per worker process)
_WORKER_BASE_MODEL: Optional[Model] = None
_WORKER_ORIG_MODEL: Optional[Model] = None


def _worker_init(base_model: Model, orig_model: Model) -> None:
    """Initialize worker process with pinned single-thread BLAS and base models."""
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"

    global _WORKER_BASE_MODEL, _WORKER_ORIG_MODEL
    _WORKER_BASE_MODEL = base_model
    _WORKER_ORIG_MODEL = orig_model


def _worker_solve_node_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single child node LP relaxation in a worker process.

    Returns structured evaluation metadata without mutating global state.
    """
    t0 = time.perf_counter()
    node_id = task['node_id']
    l_b = task['l_b']
    u_b = task['u_b']
    basis_state = task.get('basis_state')
    parent_bound = task.get('parent_bound', -math.inf)
    current_incval = task.get('current_incval')  # float or None
    tol = task.get('tol', 1e-7)
    max_iter = task.get('max_iter')
    deadline = task.get('deadline', time.perf_counter() + 3600.0)
    branch_var = task.get('branch_var')
    is_down = task.get('is_down', True)
    f_down = task.get('f_down', 0.5)
    f_up = task.get('f_up', 0.5)

    global _WORKER_BASE_MODEL, _WORKER_ORIG_MODEL
    base_model = _WORKER_BASE_MODEL
    orig_model = _WORKER_ORIG_MODEL

    # Early cutoff check before solving
    if current_incval is not None and parent_bound != -math.inf and float(parent_bound) >= current_incval:
        return {
            'node_id': node_id,
            'status': 'PRUNED_BY_BOUND',
            'pruned_early': True,
            'lp_time': time.perf_counter() - t0,
            'worker_pid': os.getpid(),
        }

    if time.perf_counter() >= deadline:
        return {
            'node_id': node_id,
            'status': 'LIMIT_REACHED',
            'message': 'Time limit reached before node LP solve',
            'lp_time': time.perf_counter() - t0,
            'worker_pid': os.getpid(),
        }

    # Construct child LP model
    child_model = replace(base_model, lower=l_b, upper=u_b, integer=())
    n_total = len(child_model.A) + len(child_model.c)
    effective_iter = max_iter if max_iter is not None else min(1500, max(250, 3 * n_total))

    # Dual simplex with warm start
    res_child = None
    warm_accepted = False
    if basis_state is not None:
        res = solve_dual_simplex(child_model, basis_state=basis_state,
                                 presolve=False, scaling=False, tol=tol,
                                 max_iter=effective_iter, deadline=deadline)
        if res.get('warm_start_accepted', False) and res['status'] in ('OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED'):
            res_child = res
            warm_accepted = True

    if res_child is None:
        if time.perf_counter() >= deadline:
            return {
                'node_id': node_id,
                'status': 'LIMIT_REACHED',
                'message': 'Time limit reached',
                'lp_time': time.perf_counter() - t0,
                'worker_pid': os.getpid(),
            }
        # Cold dual simplex
        res = solve_dual_simplex(child_model, basis_state=None,
                                 presolve=False, scaling=False, tol=tol,
                                 max_iter=effective_iter, deadline=deadline)
        if res['status'] in ('OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED', 'LIMIT_REACHED'):
            res_child = res
        else:
            # Cold primal simplex fallback
            res_child = solve_lp(child_model, tol=tol, max_iter=effective_iter, deadline=deadline)

    lp_time = time.perf_counter() - t0
    status = res_child['status']

    if status == 'INFEASIBLE_CERTIFIED':
        return {
            'node_id': node_id,
            'status': 'INFEASIBLE_CERTIFIED',
            'lp_time': lp_time,
            'iterations': res_child.get('iterations', 0),
            'warm_accepted': warm_accepted,
            'worker_pid': os.getpid(),
        }

    if status != 'OPTIMAL_VERIFIED':
        return {
            'node_id': node_id,
            'status': status,
            'message': res_child.get('message', status),
            'lp_time': lp_time,
            'iterations': res_child.get('iterations', 0),
            'warm_accepted': warm_accepted,
            'worker_pid': os.getpid(),
        }

    # Certified rational lower bound
    slb_child = safe_lower_bound(child_model, res_child.get('dual_exact_fraction', res_child.get('dual')))
    if slb_child is not None:
        child_bound = slb_child if parent_bound == -math.inf else max(parent_bound, slb_child)
    else:
        child_bound = parent_bound

    # Pseudocost delta observation
    child_obj = float(res_child['objective'])
    parent_obj_float = float(parent_bound) if parent_bound != -math.inf else child_obj
    dz = max(0.0, child_obj - parent_obj_float)
    f_val = f_down if is_down else f_up
    pseudocost_obs = (branch_var, is_down, dz, f_val) if branch_var is not None else None

    # Check integrality
    x_child = np.array(res_child['x'], dtype=np.float64)
    child_frac = [j for j in base_model.integer if abs(x_child[j] - round(x_child[j])) > tol]

    is_integral = len(child_frac) == 0
    integral_val = None
    integral_feasible = False
    xr = None

    if is_integral:
        xr = x_child.copy()
        for j in base_model.integer:
            xr[j] = round(xr[j])
        vr = verify(orig_model, xr, tol=tol)
        integral_feasible = vr['feasible']
        if integral_feasible:
            integral_val = exact_objective(orig_model, xr)

    return {
        'node_id': node_id,
        'status': 'OPTIMAL_VERIFIED',
        'objective': child_obj,
        'child_bound': child_bound,
        'basis_state': res_child.get('basis_state'),
        'x_sol': x_child,
        'is_integral': is_integral,
        'integral_feasible': integral_feasible,
        'integral_val': integral_val,
        'xr': xr,
        'pseudocost_obs': pseudocost_obs,
        'lp_time': lp_time,
        'iterations': res_child.get('iterations', 0),
        'warm_accepted': warm_accepted,
        'worker_pid': os.getpid(),
    }


def solve_milp_parallel(model: Model, tol: float = 1e-7, max_nodes: int = 1000,
                        time_limit: float = 30.0,
                        parallel_workers: int = 4,
                        use_warm_starts: bool = True,
                        use_pseudocosts: bool = True,
                        use_strong_branching: bool = True,
                        use_heuristics: bool = True,
                        use_cuts: bool = True,
                        node_selection: str = 'hybrid',
                        cut_config: Optional[CutConfig] = None,
                        **kwargs) -> Dict[str, Any]:
    """Sovereign intra-solve parallel branch-and-bound MILP solver."""
    start_time = time.perf_counter()
    orig_model = model
    deadline = start_time + time_limit

    # Initial variable box check
    def box_lb(m: Model) -> Union[F, float]:
        b = F(0)
        for c, l, u in zip(m.c, m.lower, m.upper):
            c_f = float(c)
            if c_f > 0:
                if not math.isfinite(l): return -math.inf
                b += F(c_f) * F(float(l))
            elif c_f < 0:
                if not math.isfinite(u): return -math.inf
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
            'algorithm': 'intra-solve parallel branch-and-bound',
            'nodes': 0,
            'parallel_enabled': True,
            'parallel_workers_used': parallel_workers,
        }

    if max_nodes <= 0:
        rep_bound = downward_float(rootlb + offset_F) if rootlb != -math.inf else -math.inf
        return {
            'status': 'LIMIT_REACHED',
            'algorithm': 'intra-solve parallel branch-and-bound',
            'nodes': 0,
            'best_bound': rep_bound,
            'open_nodes': 1,
            'parallel_enabled': True,
            'parallel_workers_used': parallel_workers,
        }

    # Parallel & MILP Telemetry
    telemetry = {
        'parallel_enabled': True,
        'parallel_workers_requested': parallel_workers,
        'parallel_workers_used': parallel_workers,
        'worker_process_ids': [],
        'nodes_dispatched': 0,
        'nodes_completed': 0,
        'max_nodes_in_flight': 0,
        'worker_busy_seconds': 0.0,
        'coordinator_seconds': 0.0,
        'parallel_wall_seconds': 0.0,
        'incumbent_updates_proposed': 0,
        'incumbent_updates_accepted': 0,
        'incumbent_updates_rejected': 0,
        'worker_failures': 0,
        'requeued_nodes': 0,
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
        'cut_time_seconds': 0.0,
        'root_bound_before_cuts': None,
        'root_bound_after_cuts': None,
        'root_bound_improvement_abs': 0.0,
        'root_bound_improvement_pct': 0.0,
    }

    down_count: Dict[int, int] = defaultdict(int)
    down_sum: Dict[int, float] = defaultdict(float)
    up_count: Dict[int, int] = defaultdict(int)
    up_sum: Dict[int, float] = defaultdict(float)

    # 1. Coordinator solves root node LP relaxation
    t0_root = time.perf_counter()
    root_model = replace(model, lower=lo, upper=hi, integer=())
    res_root = solve_dual_simplex(root_model, basis_state=None, presolve=False, scaling=False, tol=tol, deadline=deadline)
    if res_root['status'] not in ('OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED'):
        res_root = solve_lp(root_model, tol=tol, deadline=deadline)

    telemetry['root_lp_time'] = time.perf_counter() - t0_root
    telemetry['root_lp_iterations'] = res_root.get('iterations', 0)
    nodes = 1

    if res_root['status'] == 'INFEASIBLE_CERTIFIED':
        return {
            'status': 'INFEASIBLE_CERTIFIED',
            'algorithm': 'intra-solve parallel branch-and-bound',
            'nodes': 1,
            'message': 'Root LP relaxation is infeasible',
            'best_bound': math.inf,
            'parallel_enabled': True,
            'parallel_workers_used': parallel_workers,
            'telemetry': telemetry,
        }

    if res_root['status'] != 'OPTIMAL_VERIFIED':
        return {
            'status': res_root['status'],
            'algorithm': 'intra-solve parallel branch-and-bound',
            'nodes': 1,
            'message': 'Root LP relaxation failed',
            'best_bound': -math.inf,
            'parallel_enabled': True,
            'parallel_workers_used': parallel_workers,
            'telemetry': telemetry,
        }

    slb_root = safe_lower_bound(root_model, res_root.get('dual_exact_fraction', res_root.get('dual')))
    root_bound = slb_root if slb_root is not None else rootlb
    telemetry['root_lp_bound'] = downward_float(root_bound) if root_bound != -math.inf else -math.inf
    telemetry['root_bound_before_cuts'] = telemetry['root_lp_bound']
    telemetry['root_bound_after_cuts'] = telemetry['root_lp_bound']
    x_root = np.array(res_root['x'])

    # 2. Coordinator Root Cut Loop (Gate 20C cover cuts)
    frac_root = [j for j in model.integer if abs(x_root[j] - round(x_root[j])) > tol]
    if telemetry['cuts_enabled'] and len(frac_root) > 0:
        cfg = cut_config or CutConfig()
        cut_pool = CutPool(cfg)
        t0_cuts = time.perf_counter()

        for round_idx in range(cfg.max_cut_rounds_root):
            if time.perf_counter() >= deadline:
                break
            new_cover_cuts = separate_cover_cuts(root_model, x_root, config=cfg, source_node=1,
                                                 integer_vars=model.integer)
            telemetry['cover_cuts_generated'] += len(new_cover_cuts)
            telemetry['cuts_generated'] += len(new_cover_cuts)
            if not new_cover_cuts:
                break

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

            k_cuts = len(round_accepted)
            cut_coeffs = np.array([c.coefficients for c in round_accepted], dtype=np.float64)
            cut_rhs = np.array([c.rhs for c in round_accepted], dtype=np.float64)
            aug_A = append_rows_to_matrix(root_model.A, cut_coeffs)
            aug_rl = np.concatenate([root_model.row_lower, np.full(k_cuts, -np.inf)])
            aug_ru = np.concatenate([root_model.row_upper, cut_rhs])
            aug_model = replace(root_model, A=aug_A, row_lower=aug_rl, row_upper=aug_ru)

            res_aug = solve_dual_simplex(aug_model, basis_state=None, presolve=False, scaling=False, tol=tol, deadline=deadline)
            if res_aug.get('status') == 'OPTIMAL_VERIFIED':
                root_model = aug_model
                res_root = res_aug
                x_root = np.array(res_aug['x'])
                telemetry['cut_rounds'] += 1
                slb_aug = safe_lower_bound(root_model, res_aug.get('dual_exact_fraction', res_aug.get('dual')))
                if slb_aug is not None and (root_bound == -math.inf or slb_aug > root_bound):
                    root_bound = slb_aug
                    telemetry['root_lp_bound'] = downward_float(root_bound)
                    telemetry['root_bound_after_cuts'] = telemetry['root_lp_bound']
            else:
                break

        telemetry['cut_time_seconds'] = float(time.perf_counter() - t0_cuts)
        b_before = telemetry['root_bound_before_cuts']
        b_after = telemetry['root_bound_after_cuts']
        if b_before is not None and b_after is not None and b_before != -math.inf and b_after != -math.inf:
            imp_abs = max(0.0, float(b_after - b_before))
            telemetry['root_bound_improvement_abs'] = imp_abs
            telemetry['root_bound_improvement_pct'] = float((imp_abs / max(1.0, abs(float(b_before)))) * 100.0)

        if telemetry['cuts_accepted'] > 0:
            model = replace(model, A=root_model.A, row_lower=root_model.row_lower, row_upper=root_model.row_upper)

    # 3. Check root integrality
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

    fractional = [j for j in model.integer if abs(x_root[j] - round(x_root[j])) > tol]
    if not fractional:
        xr = x_root.copy()
        for j in model.integer: xr[j] = round(xr[j])
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

    # If root solved to optimality or infeasibility, finish immediately
    if not open_nodes:
        result = _finalize_result(model, orig_model, nodes, open_nodes, [], tolerance_closed,
                                  inc, incval, offset_F, start_time, time_limit, telemetry, tol,
                                  incumbent_history, node_selection, use_pseudocosts)
        return result

    # 4. Intra-Solve Parallel Search Coordinator
    # Shared base model across all workers is `model` (including root cuts)
    worker_pids = set()

    def select_next_node_idx() -> int:
        """Select best node from open_nodes using hybrid or best-bound strategy."""
        if not open_nodes:
            return -1
        if node_selection == 'best-bound':
            best_idx = 0
            best_bound = open_nodes[0].certified_lp_bound
            for i in range(1, len(open_nodes)):
                b = open_nodes[i].certified_lp_bound
                if best_bound != -math.inf and (b == -math.inf or b < best_bound):
                    best_bound = b
                    best_idx = i
                elif b == best_bound and open_nodes[i].depth > open_nodes[best_idx].depth:
                    best_idx = i
            return best_idx
        else:
            # Hybrid
            min_bound = None
            for n in open_nodes:
                b = n.certified_lp_bound
                if b == -math.inf:
                    min_bound = -math.inf; break
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

    def select_branching_var(parent_node: MILPNode, frac_vars: List[int]) -> int:
        if not use_pseudocosts:
            return max(frac_vars, key=lambda j: min(parent_node.x_sol[j] - math.floor(parent_node.x_sol[j]),
                                                    math.ceil(parent_node.x_sol[j]) - parent_node.x_sol[j]))
        avg_down = (sum(down_sum.values()) / max(1, sum(down_count.values()))) if sum(down_count.values()) > 0 else 1.0
        avg_up = (sum(up_sum.values()) / max(1, sum(up_count.values()))) if sum(up_count.values()) > 0 else 1.0
        best_j = frac_vars[0]
        best_score = -1.0
        for j in frac_vars:
            xj = parent_node.x_sol[j]
            f_down = xj - math.floor(xj)
            f_up = math.ceil(xj) - xj
            psi_down = (down_sum[j] / down_count[j]) if down_count[j] > 0 else avg_down
            psi_up = (up_sum[j] / up_count[j]) if up_count[j] > 0 else avg_up
            score = max(psi_down * f_down, 1e-6) * max(psi_up * f_up, 1e-6)
            if score > best_score:
                best_score = score
                best_j = j
            elif score == best_score and j < best_j:
                best_j = j
        return best_j

    in_flight: Dict[int, MILPNode] = {}
    futures_map: Dict[Any, int] = {}
    unsolved_tasks: List[Tuple[MILPNode, Dict[str, Any]]] = []
    failure: Optional[str] = None

    # Spawn ProcessPoolExecutor
    num_workers = max(1, min(parallel_workers, 16))
    with ProcessPoolExecutor(max_workers=num_workers,
                             initializer=_worker_init,
                             initargs=(model, orig_model)) as executor:

        while (open_nodes or unsolved_tasks or in_flight) and nodes < max_nodes and time.perf_counter() < deadline:
            # 1. Dispatch Phase: Fill worker capacity
            while len(in_flight) < num_workers and (unsolved_tasks or open_nodes):
                if nodes >= max_nodes or time.perf_counter() >= deadline:
                    break

                if unsolved_tasks:
                    node_to_eval, task_spec = unsolved_tasks.pop(0)
                    task_spec['current_incval'] = float(incval) if incval is not None else None
                    fut = executor.submit(_worker_solve_node_task, task_spec)
                    in_flight[node_to_eval.node_id] = node_to_eval
                    futures_map[fut] = node_to_eval.node_id
                    telemetry['nodes_dispatched'] += 1
                elif open_nodes:
                    idx = select_next_node_idx()
                    curr = open_nodes.pop(idx)

                    # Prune by incumbent
                    if incval is not None and curr.certified_lp_bound != -math.inf and curr.certified_lp_bound >= incval:
                        telemetry['pruned_by_bound'] += 1
                        continue

                    # Check integrality
                    frac_vars = [j for j in model.integer if abs(curr.x_sol[j] - round(curr.x_sol[j])) > tol]
                    if not frac_vars:
                        xr = curr.x_sol.copy()
                        for j in model.integer: xr[j] = round(xr[j])
                        vr = verify(orig_model, xr, tol=tol)
                        val = exact_objective(orig_model, xr)
                        if vr['feasible']:
                            telemetry['incumbent_updates_proposed'] += 1
                            if incval is None or val < incval:
                                inc = xr
                                incval = val
                                telemetry['incumbent_updates_accepted'] += 1
                                incumbent_history.append({
                                    'node_id': curr.node_id,
                                    'objective': float(val),
                                    'source': 'integrality',
                                    'time': time.perf_counter() - start_time,
                                })
                            else:
                                telemetry['incumbent_updates_rejected'] += 1
                            tolerance_closed.append(val)
                            telemetry['pruned_by_integrality'] += 1
                        continue

                    # Branch node
                    b_var = select_branching_var(curr, frac_vars)
                    xj = curr.x_sol[b_var]
                    f_d = xj - math.floor(xj)
                    f_u = math.ceil(xj) - xj

                    branches = [
                        ('down', math.floor(xj), True),
                        ('up', math.ceil(xj), False),
                    ]

                    for dir_name, b_val, is_down in branches:
                        l_b = curr.local_lower_bounds.copy()
                        u_b = curr.local_upper_bounds.copy()
                        if is_down:
                            u_b[b_var] = min(u_b[b_var], b_val)
                        else:
                            l_b[b_var] = max(l_b[b_var], b_val)

                        if l_b[b_var] > u_b[b_var]:
                            telemetry['pruned_by_infeasibility'] += 1
                            continue

                        serial += 1
                        child_node = MILPNode(
                            node_id=serial,
                            parent_id=curr.node_id,
                            depth=curr.depth + 1,
                            branch_variable=b_var,
                            branch_direction=dir_name,
                            branch_value=b_val,
                            local_lower_bounds=l_b,
                            local_upper_bounds=u_b,
                            certified_lp_bound=curr.certified_lp_bound,
                            lp_status='IN_FLIGHT',
                            basis_state=curr.basis_state,
                            warm_start_source='parent',
                            creation_order=serial,
                            x_sol=curr.x_sol,
                        )

                        task_spec = {
                            'node_id': serial,
                            'l_b': l_b,
                            'u_b': u_b,
                            'basis_state': curr.basis_state,
                            'parent_bound': curr.certified_lp_bound,
                            'current_incval': float(incval) if incval is not None else None,
                            'tol': tol,
                            'deadline': deadline,
                            'branch_var': b_var,
                            'is_down': is_down,
                            'f_down': f_d,
                            'f_up': f_u,
                        }
                        unsolved_tasks.append((child_node, task_spec))

            telemetry['max_nodes_in_flight'] = max(telemetry['max_nodes_in_flight'], len(in_flight))

            # 2. Collect Phase: Wait for at least one worker to finish
            if in_flight:
                done, _ = wait(futures_map.keys(), timeout=0.05, return_when=FIRST_COMPLETED)
                for fut in done:
                    n_id = futures_map.pop(fut)
                    completed_node = in_flight.pop(n_id)

                    try:
                        res_task = fut.result()
                    except Exception as exc:
                        # Worker failure recovery: requeue or fail honestly
                        telemetry['worker_failures'] += 1
                        telemetry['requeued_nodes'] += 1
                        failure = f"Worker process exception on node {n_id}: {str(exc)}"
                        # Requeue node as unresolved
                        open_nodes.append(completed_node)
                        continue

                    nodes += 1
                    telemetry['nodes_completed'] += 1
                    telemetry['worker_busy_seconds'] += res_task.get('lp_time', 0.0)
                    if 'worker_pid' in res_task:
                        worker_pids.add(res_task['worker_pid'])

                    if res_task.get('warm_accepted'):
                        telemetry['warm_starts_accepted'] += 1
                    elif completed_node.basis_state is not None:
                        telemetry['warm_starts_rejected'] += 1

                    # Update pseudocosts from worker observation
                    p_obs = res_task.get('pseudocost_obs')
                    if p_obs:
                        p_var, p_is_down, p_dz, p_f = p_obs
                        if p_is_down:
                            down_count[p_var] += 1
                            down_sum[p_var] += p_dz / max(p_f, 1e-4)
                        else:
                            up_count[p_var] += 1
                            up_sum[p_var] += p_dz / max(p_f, 1e-4)

                    st = res_task['status']
                    if st == 'PRUNED_BY_BOUND':
                        telemetry['pruned_by_bound'] += 1
                        continue

                    if st == 'INFEASIBLE_CERTIFIED':
                        telemetry['pruned_by_infeasibility'] += 1
                        continue

                    if st != 'OPTIMAL_VERIFIED':
                        failure = f"Child LP relaxation on node {n_id} returned {st}: {res_task.get('message', '')}"
                        completed_node.lp_status = st
                        open_nodes.append(completed_node)
                        break

                    # Resolved node
                    c_bound = res_task['child_bound']
                    completed_node.certified_lp_bound = c_bound
                    completed_node.basis_state = res_task.get('basis_state')
                    completed_node.x_sol = res_task['x_sol']
                    completed_node.lp_status = 'OPTIMAL_VERIFIED'

                    # Check bound cutoff
                    if incval is not None and c_bound != -math.inf and c_bound >= incval:
                        telemetry['pruned_by_bound'] += 1
                        continue

                    if res_task['is_integral'] and res_task.get('xr') is not None:
                        cand_xr = res_task['xr']
                        # Authoritative coordinator-side verification before acceptance
                        vr_coord = verify(orig_model, cand_xr, tol=tol)
                        int_viol = max([abs(cand_xr[j] - round(cand_xr[j])) for j in orig_model.integer], default=0.0)
                        if vr_coord['feasible'] and int_viol <= tol:
                            telemetry['incumbent_updates_proposed'] += 1
                            i_val = exact_objective(orig_model, cand_xr)
                            if incval is None or i_val < incval:
                                inc = cand_xr
                                incval = i_val
                                telemetry['incumbent_updates_accepted'] += 1
                                incumbent_history.append({
                                    'node_id': n_id,
                                    'objective': float(i_val),
                                    'source': 'integrality',
                                    'time': time.perf_counter() - start_time,
                                })
                            else:
                                telemetry['incumbent_updates_rejected'] += 1
                            tolerance_closed.append(i_val if c_bound == -math.inf else max(c_bound, i_val))
                            telemetry['pruned_by_integrality'] += 1
                        else:
                            open_nodes.append(completed_node)
                    else:
                        open_nodes.append(completed_node)

        # Cancel any lingering futures on exit
        for fut in list(futures_map.keys()):
            fut.cancel()

    # Reconstitute open nodes with remaining in_flight or unsolved nodes
    for n in in_flight.values():
        open_nodes.append(n)
    for n, _ in unsolved_tasks:
        open_nodes.append(n)

    telemetry['worker_process_ids'] = sorted(list(worker_pids))
    telemetry['parallel_wall_seconds'] = float(time.perf_counter() - start_time)

    return _finalize_result(model, orig_model, nodes, open_nodes, in_flight, tolerance_closed,
                            inc, incval, offset_F, start_time, time_limit, telemetry, tol,
                            incumbent_history, node_selection, use_pseudocosts, failure=failure)


def _finalize_result(model: Model, orig_model: Model, nodes: int,
                     open_nodes: List[MILPNode], in_flight: Any,
                     tolerance_closed: List[F], inc: Optional[np.ndarray],
                     incval: Optional[F], offset_F: F, start_time: float,
                     time_limit: float, telemetry: Dict[str, Any], tol: float,
                     incumbent_history: List[Dict[str, Any]],
                     node_selection: str, use_pseudocosts: bool,
                     failure: Optional[str] = None) -> Dict[str, Any]:
    """Assemble authoritative verified MILP result dictionary."""
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
        'algorithm': 'intra-solve parallel branch-and-bound',
        'nodes': nodes,
        'bound_kind': 'exact rational Lagrangian bounds of binary64 input',
        'open_nodes': len(open_nodes),
        'tolerance_closed_nodes': len(tolerance_closed),
        'pruned_nodes': telemetry['pruned_by_bound'] + telemetry['pruned_by_infeasibility'] + telemetry['pruned_by_integrality'],
        'incumbent_history': incumbent_history,
        'selection_strategy': 'hybrid best-bound/depth' if node_selection == 'hybrid' else 'best-bound',
        'branching_strategy': 'pseudocost with strong branching bootstrap' if use_pseudocosts else 'most-fractional',
        'configured_time_limit': float(time_limit),
        'measured_runtime': float(time.perf_counter() - start_time),
        'deadline_checks': int(telemetry.get('deadline_checks', 0)),
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
            elif failure:
                result['status'] = 'NUMERICAL_FAILURE'
            else:
                result['status'] = 'LIMIT_REACHED'
        else:
            result['status'] = 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if open_nodes else 'INFEASIBLE_CERTIFIED'
    else:
        # Maximization
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
            elif failure:
                result['status'] = 'NUMERICAL_FAILURE'
            else:
                result['status'] = 'LIMIT_REACHED'
        else:
            result['status'] = 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if open_nodes else 'INFEASIBLE_CERTIFIED'

    telemetry['nodes_explored'] = nodes
    telemetry['nodes_pruned'] = telemetry['pruned_by_bound'] + telemetry['pruned_by_infeasibility'] + telemetry['pruned_by_integrality']
    telemetry['incumbent'] = result.get('objective')
    telemetry['best_bound'] = result.get('best_bound')
    telemetry['final_gap'] = result.get('relative_gap', float('inf'))
    result.update(telemetry)

    if failure:
        result['message'] = failure
    return result
