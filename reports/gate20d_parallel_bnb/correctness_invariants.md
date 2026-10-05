# Gate 20D: Parallel Branch-and-Bound Correctness Invariants

**Repository:** `sov-opt-mrpl-26119`
**Problem Statement:** MRPL SIH 2026 PS 26119
**Date:** 2026-10-05

---

## 1. Mathematical & Structural Invariants

To guarantee that intra-solve parallel branch-and-bound produces mathematically identical, verified solutions to serial search, the parallel implementation must adhere to eleven invariant principles without exception.

### Invariant 1: Immutable Unique Node Identification
Every node generated in the B&B tree is assigned a strictly unique, monotonically increasing integer `node_id`. Once assigned, `node_id` is immutable.

### Invariant 2: Mutually Exclusive Node States
At every point in time during the solve, every node in the search tree exists in exactly one of the following six states:
- `QUEUED`: Stored in the coordinator's open node priority pool awaiting evaluation.
- `IN_FLIGHT`: Dispatched to a worker process; currently being solved.
- `SOLVED`: Relaxation completed; returned to coordinator for branching or pruning.
- `PRUNED`: Eliminated by bound cutoff, infeasibility, or integer optimality.
- `INFEASIBLE`: Provably infeasible local bounds or certified infeasible LP relaxation.
- `FAILED`: Numerical failure during relaxation; retained for diagnostic accounting.

### Invariant 3: Single-Evaluation Guarantee
A node can never be dispatched or evaluated more than once, except during explicit crash recovery where an uncompleted in-flight node is safely requeued.

### Invariant 4: Monotonic Global Incumbent
For minimization problems, the global incumbent objective sequence $z_k$ is strictly non-increasing:
$$z_{k+1} \le z_k \quad \forall k$$
No race condition or asynchronous message arrival may weaken or overwrite an established incumbent with an inferior value.

### Invariant 5: Independent Verification of Proposed Incumbents
Workers do not possess the authority to declare a new global incumbent. When a worker discovers an integer-feasible point $x^*$, it returns the candidate to the coordinator. The coordinator independently verifies feasibility against the original un-cut model (`verify(orig_model, x*)`) and computes the exact rational objective (`exact_objective(orig_model, x*)`) before updating canonical state.

### Invariant 6: Strict Pruning Safety
A node or subtree with lower bound $b_{\text{node}}$ may be pruned if and only if:
$$b_{\text{node}} \ge z_{\text{incumbent}}$$
using certified rational bounds or conservative floating-point directed rounding. Subtrees may never be pruned against speculative or unverified bounds.

### Invariant 7: Authoritative Exact Rational Bound Accounting
The Neumaier-Shcherbina safe lower bound and Fraction-based objective tracking remain the authoritative ground truth. Floating-point conversions are permitted only for heuristic guidance and user display.

### Invariant 8: Closed-World Optimality Verification
`OPTIMAL_VERIFIED` may be declared if and only if ALL of the following criteria hold simultaneously:
1. `len(open_nodes) == 0` (queue is completely empty).
2. `len(in_flight) == 0` (zero nodes are currently being evaluated by workers).
3. Zero worker results or messages are pending.
4. An incumbent solution has been discovered, verified, and certified feasible.
5. The global lower bound satisfies:
   $$\text{gap} = \frac{z_{\text{incumbent}} - \text{global\_lower}}{1.0 + |z_{\text{incumbent}}|} \le \text{tol}$$
6. The incumbent passes final end-to-end KKT/integer verification.

### Invariant 9: Fail-Safe Subtree Preservation
If a worker process terminates abnormally, crashes, or raises an unhandled exception while evaluating a node, that node must NOT be silently dropped. The coordinator must either:
- Requeue the node back into `open_nodes` for retry, OR
- Terminate the solve honestly with `NUMERICAL_FAILURE` or `LIMIT_REACHED`.

### Invariant 10: Honest Timeout Accounting
If the global time limit expires while nodes remain in the queue or in flight:
- The coordinator must immediately halt worker dispatch, safely shut down workers, and return `LIMIT_REACHED`.
- It is strictly forbidden to declare `OPTIMAL_VERIFIED` if any unexplored subtree remains unresolved.

### Invariant 11: Fail-Closed Numerical Integrity
If any node encounters basis singularity or numerical breakdown in its dual simplex relaxation that cannot be recovered, the coordinator must record the diagnostic honestly as `NUMERICAL_FAILURE` rather than pretending the node was infeasible.

### Invariant 12: Canonical Pseudocost Ownership
Workers return local bound delta observations `(branch_var, is_down, dz, f_val)` with completed tasks. The coordinator process exclusively owns, aggregates, and updates the canonical global pseudocost structures (`down_count`, `down_sum`, `up_count`, `up_sum`). Workers never mutate shared pseudocost state.
