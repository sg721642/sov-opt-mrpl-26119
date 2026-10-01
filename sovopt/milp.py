"""Serial best-bound B&B with exact rational conservative bounds.
No cuts, warm starts, or pseudocosts in this reference release.

Mathematical safety guarantees:
- Unsafe root bounds are prevented: unbounded minimizing directions yield -math.inf.
- Exact rational Fraction bounds are preserved throughout tree search and pruning.
- Rounding is applied ONLY to declared integer variables; continuous variables retain float values.
- Feasibility is checked against the original model.
- Objective offsets and maximization sense are consistently mapped to reported values.
"""
from dataclasses import replace
from fractions import Fraction as F
import heapq, math, time
import numpy as np
from .simplex import solve_lp
from .verify import verify, safe_lower_bound, downward_float, upward_float

def exact_objective(model, x):
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

def solve_milp(model, tol=1e-7, max_nodes=1000, time_limit=30., **kwargs):
    start = time.perf_counter()

    # Root lower bound from variable box:
    # For minimization: an objective coefficient whose minimizing direction has an
    # infinite variable bound makes the box lower bound -math.inf. Zero coefficients
    # contribute exactly 0.
    def box_lb(m):
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
            # c_f == 0 contributes strictly 0 regardless of bounds
        return b

    rootlb = box_lb(model)
    lo = model.lower.copy()
    hi = model.upper.copy()
    for j in model.integer:
        if math.isfinite(lo[j]): lo[j] = math.ceil(lo[j])
        if math.isfinite(hi[j]): hi[j] = math.floor(hi[j])

    if np.any(lo > hi):
        return dict(status='INFEASIBLE_CERTIFIED', message='An integer variable has no integer in its box',
                    algorithm='rational-bound branch-and-bound', nodes=0)

    # Heap contains: (bound, serial, lo, hi)
    # bound is either exact Fraction or -math.inf.
    heap = [(rootlb, 0, lo, hi)]
    serial = 0
    nodes = 0
    inc = None
    incval = None
    history = []
    pruned_by_bound = []
    tolerance_closed = []
    failure = None

    while heap and nodes < max_nodes and time.perf_counter() - start < time_limit:
        inherited, _, l_node, u_node = heapq.heappop(heap)
        if incval is not None and inherited != -math.inf and inherited >= incval:
            pruned_by_bound.append(inherited)
            continue

        node = replace(model, lower=l_node, upper=u_node, integer=())
        res = solve_lp(node, tol=tol, **kwargs)
        nodes += 1

        if res['status'] == 'INFEASIBLE_CERTIFIED':
            continue
        if res['status'] != 'OPTIMAL_VERIFIED':
            heapq.heappush(heap, (inherited, serial + 1, l_node, u_node))
            failure = 'Unresolved LP relaxation: ' + res.get('message', res['status'])
            break

        dual_to_use = res.get('dual_exact_fraction', res['dual'])
        slb = safe_lower_bound(node, dual_to_use)
        if slb is not None:
            bound = slb if inherited == -math.inf else max(inherited, slb)
        else:
            bound = inherited

        if incval is not None and bound != -math.inf and bound >= incval:
            pruned_by_bound.append(bound)
            continue

        x = np.array(res['x'])
        fractional = [j for j in model.integer if abs(x[j] - round(x[j])) > tol]

        if not fractional:
            xr = x.copy()
            for j in model.integer:
                xr[j] = round(xr[j])
            vr = verify(model, xr, tol=tol)
            val = exact_objective(model, xr)
            if vr['feasible']:
                if incval is None or val < incval:
                    inc = xr
                    incval = val
                # Node is fathomed by integrality.
                # Conservative lower bound on this branch is the relaxation bound or exact objective.
                leaf_bound = bound if bound != -math.inf else val
                tolerance_closed.append(leaf_bound)
            else:
                heapq.heappush(heap, (bound, serial + 1, l_node, u_node))
                failure = 'Near-integral node could not be closed safely'
                break
        else:
            j = max(fractional, key=lambda j: min(x[j] - math.floor(x[j]), math.ceil(x[j]) - x[j]))
            for left in [True, False]:
                l_branch = l_node.copy()
                u_branch = u_node.copy()
                if left:
                    u_branch[j] = min(u_branch[j], math.floor(x[j]))
                else:
                    l_branch[j] = max(l_branch[j], math.ceil(x[j]))
                if l_branch[j] <= u_branch[j]:
                    serial += 1
                    heapq.heappush(heap, (bound, serial, l_branch, u_branch))

        history.append(dict(nodes=nodes, open_nodes=len(heap),
                            incumbent=None if incval is None else float(incval),
                            node_bound=downward_float(bound) if bound != -math.inf else None))

    # Exhaustive accounting of all tree regions:
    # 1. Open / unresolved leaves in heap
    open_bounds = [t[0] for t in heap]
    # 2. Leaves closed within tolerance
    tolerance_bounds = [b for b in tolerance_closed]

    if incval is not None:
        candidates = open_bounds + tolerance_bounds + [incval]
        if any(c == -math.inf for c in candidates):
            global_lower = -math.inf
        else:
            global_lower = min(candidates)
    else:
        if open_bounds:
            global_lower = -math.inf if any(b == -math.inf for b in open_bounds) else min(open_bounds)
        elif tolerance_bounds:
            global_lower = -math.inf if any(b == -math.inf for b in tolerance_bounds) else min(tolerance_bounds)
        else:
            # Heap is empty and no incumbent exists: every branch was certified infeasible
            global_lower = None

    result = dict(
        algorithm='rational-bound branch-and-bound',
        nodes=nodes,
        history=history,
        bound_kind='exact rational Lagrangian bounds of binary64 input',
        open_nodes=len(heap),
        tolerance_closed_nodes=len(tolerance_closed),
        pruned_nodes=len(pruned_by_bound)
    )

    offset_F = F(float(model.obj_offset)) if model.obj_offset != 0.0 else F(0)

    # Map bounds, objectives, and gaps according to objective sense (min vs max)
    if not model.maximize:
        # Standard minimization
        # Add objective offset in exact rational arithmetic BEFORE downward rounding
        if global_lower is not None and global_lower != -math.inf:
            reported_lower = downward_float(global_lower + offset_F)
        elif global_lower == -math.inf:
            reported_lower = -math.inf
        else:
            reported_lower = None
        result['best_bound'] = reported_lower

        if inc is not None:
            reported_obj = float(incval + offset_F)
            if global_lower is not None and global_lower != -math.inf:
                gap = max(0.0, float(incval - global_lower)) / (1.0 + abs(reported_obj))
            else:
                gap = float('inf')
            vr = verify(model, inc, tol=tol)
            result.update(x=inc.tolist(), objective=reported_obj, verification=vr, relative_gap=gap)
            if not heap and not failure and gap <= tol:
                result['status'] = 'OPTIMAL_VERIFIED'
                # gap == 0.0 is a floating-point equality between incumbent and bound;
                # it is not an exact rational certificate of optimality. Incumbent feasibility
                # is checked numerically (verify()), not by exact rational arithmetic.
                result['verification']['optimality_basis'] = (
                    f'finite B&B tree with exact rational lower bounds; incumbent feasibility verified numerically; '
                    f'relative gap {gap:.2e} <= {tol:.2e} (floating-point; not an exact rational optimality certificate)'
                )
            elif failure:
                result['status'] = 'NUMERICAL_FAILURE'
                result['verification']['optimality_basis'] = 'B&B search halted on unresolved LP node; conservative lower bound preserved from open search tree'
            else:
                result['status'] = 'LIMIT_REACHED'
                result['verification']['optimality_basis'] = 'B&B search halted at limit; conservative lower bound from exhaustive open frontier and terminal leaves'
        else:
            result['status'] = 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if heap else 'INFEASIBLE_CERTIFIED'
    else:
        # Maximization: internal objective is negated (-c @ x - offset)
        # Global lower bound on internal problem becomes UPPER bound on original maximization
        if global_lower is not None and global_lower != -math.inf:
            reported_upper = upward_float(-global_lower + offset_F)
        elif global_lower == -math.inf:
            reported_upper = math.inf
        else:
            reported_upper = None
        result['best_bound'] = reported_upper

        if inc is not None:
            reported_obj = float(-incval + offset_F)
            if global_lower is not None and global_lower != -math.inf:
                gap = max(0.0, float(incval - global_lower)) / (1.0 + abs(reported_obj))
            else:
                gap = float('inf')
            vr = verify(model, inc, tol=tol)
            result.update(x=inc.tolist(), objective=reported_obj, verification=vr, relative_gap=gap)
            if not heap and not failure and gap <= tol:
                result['status'] = 'OPTIMAL_VERIFIED'
                # Same caveat: floating-point gap equality is not an exact rational optimality proof
                result['verification']['optimality_basis'] = (
                    f'finite B&B tree with exact rational bounds; incumbent feasibility verified numerically; '
                    f'relative gap {gap:.2e} <= {tol:.2e} (floating-point; not an exact rational optimality certificate)'
                )
            elif failure:
                result['status'] = 'NUMERICAL_FAILURE'
                result['verification']['optimality_basis'] = 'B&B search halted on unresolved LP node; conservative bound preserved from open search tree'
            else:
                result['status'] = 'LIMIT_REACHED'
                result['verification']['optimality_basis'] = 'B&B search halted at limit; conservative bound from exhaustive open frontier and terminal leaves'
        else:
            result['status'] = 'NUMERICAL_FAILURE' if failure else 'LIMIT_REACHED' if heap else 'INFEASIBLE_CERTIFIED'

    if failure:
        result['message'] = failure
    return result
