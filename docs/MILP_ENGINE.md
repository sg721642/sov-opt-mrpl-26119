# Sovereign MILP Branch-and-Bound Engine Specification

This document details the mathematical architecture, node search mechanics, warm-start reoptimization dynamics, branching heuristics, and safety guarantees of the sovereign Branch-and-Bound Mixed-Integer Linear Programming solver in SOV-OPT (`sovopt/milp.py`).

---

## 1. Architectural Audit of Baseline B&B (Pre-Gate 6)

A rigorous trace of `sovopt/milp.py` establishes the baseline characteristics prior to Gate 6:

1. **Child LP Cold Starts:** Every LP relaxation is solved from scratch via `solve_lp(node, ...)` with Phase-I initialization. No basis state is passed from parent to child.
2. **Branching Strategy:** Most-fractional variable selection ($\arg\max_j \min(x_j - \lfloor x_j \rfloor, \lceil x_j \rceil - x_j)$) with index-based tie-breaking.
3. **Pseudocosts:** Completely absent.
4. **Strong Branching:** Completely absent.
5. **Primal Heuristics:** Completely absent. Integer solutions are discovered only when an LP relaxation happens to be naturally integral.
6. **Node Selection:** Pure best-bound priority queue (`heapq` sorted by Lagrangian bound) with creation-serial tie breaking. No depth exploration or hybrid selection policy.
7. **Safe Bound Invariant:** Exact rational Lagrangian lower bounds (`safe_lower_bound` in `sovopt/verify.py`) computed from exact rational basis dual multipliers (`dual_exact_fraction`), preserving conservative bounds through the search tree.

---

## 2. Gate 6 Upgraded Architecture

Gate 6 transforms the baseline into a high-performance, deterministic branch-and-bound engine:

```
                          ┌────────────────────────┐
                          │     Root LP Solve      │
                          │   (Presolve/Scaling    │
                          │   + Dual Simplex)      │
                          └───────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   Heuristic Bootstrap   │
                         │   (Rounding & Diving)   │
                         └────────────┬────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │                                                   │
┌───────────▼───────────┐                           ┌───────────▼───────────┐
│     Node Selection    │                           │   Branch Selection    │
│  (Best-Bound / Depth  │                           │   (Pseudocosts with   │
│     Hybrid Queue)     │                           │   Strong Branching)   │
└───────────┬───────────┘                           └───────────┬───────────┘
            │                                                   │
            └─────────────────────────┬─────────────────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │   Dual Basis Warm-     │
                          │   Start Child Solve    │
                          └───────────┬────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │ Conservative Pruning & │
                          │ Safe Bound Accounting  │
                          └────────────────────────┘
```

---

## 3. Node Data Structure & Queue Policy

### 3.1 Node Representation
Each branch-and-bound node is represented by a structured `MILPNode`:
- `node_id: int`: Deterministic unique identifier (root is 0).
- `parent_id: Optional[int]`: Identifier of parent node.
- `depth: int`: Depth in the search tree (root is 0).
- `branch_var: Optional[int]`: Variable branched on to create this node.
- `branch_dir: Optional[str]`: `'down'` ($x_j \le \lfloor x_j^* \rfloor$) or `'up'` ($x_j \ge \lceil x_j^* \rceil$).
- `branch_val: Optional[float]`: Threshold value of the branch.
- `lower: np.ndarray`: Active lower bounds for this node.
- `upper: np.ndarray`: Active upper bounds for this node.
- `bound: Union[Fraction, float]`: Certified conservative Lagrangian lower bound.
- `basis_state: Optional[DualBasisState]`: Parent dual simplex basis state for warm start.
- `creation_order: int`: Deterministic monotonic counter.

### 3.2 Hybrid Node Selection Policy
The active node frontier is managed as a hybrid best-bound / depth queue:
- **No Incumbent Found:** Pure best-bound selection (minimizes global lower bound gap and maximizes bound progression).
- **Incumbent Exists:** Depth-biased best-bound selection. Among open nodes within a small bound neighborhood ($\le 15\%$ above best open bound), the node with greatest depth is prioritized to expedite finding better integer solutions and facilitate tree fathoming.
- **Tie-Breaking:** Deterministic tie-breaking on `(bound, -depth, creation_order)`.

---

## 4. Dual-Simplex Basis Warm Starts

### 4.1 Reoptimization Mechanics
When branching on integer variable $x_j$ at fractional value $x_j^*$:
- **Down Child:** New upper bound $u_j^{\text{new}} = \lfloor x_j^* \rfloor$.
- **Up Child:** New lower bound $l_j^{\text{new}} = \lceil x_j^* \rceil$.

Since the parent basis was dual feasible ($c_k - y^T A_k \ge 0$ for nonbasics at lower, $\le 0$ at upper), tightening variable bounds changes only the primal RHS ($b - \sum_{k \in N} A_k x_k$). Dual feasibility is preserved:
$$
B^T y = c_B \implies d = c - A^T y \quad \text{unchanged}
$$
The child problem is dual feasible and primal infeasible. This is the canonical use case for **revised dual simplex**.

### 4.2 Warm-Start Validation & Fallback
1. The parent's `DualBasisState` (basis indices, nonbasic states, nonbasic values) is attached to the child node.
2. The child LP calls `solve_dual_simplex(node, basis_state=parent_state)`.
3. If the warm basis is rejected (e.g., basis singularity under modified bounds), the solver falls back cleanly to a cold start, logging `warm_start_rejected`.
4. Telemetry records:
   - `lp_solves`, `cold_lp_solves`, `warm_start_attempts`, `warm_start_accepted`, `warm_start_rejected`, `warm_start_success_rate`.

---

## 5. Branch Variable Selection: Pseudocosts & Strong Branching

### 5.1 Pseudocost Formulation
For integer variable $j$, let $x_j^*$ be its fractional value in the parent LP with relaxation objective $z_{\text{parent}}$.
- When branched downwards ($x_j \le \lfloor x_j^* \rfloor$), the child relaxation objective is $z_{\text{down}} \ge z_{\text{parent}}$.
  The down-movement is $f_j^- = x_j^* - \lfloor x_j^* \rfloor > 0$.
  The down unit degradation is:
  $$
  \Delta_j^- = \frac{z_{\text{down}} - z_{\text{parent}}}{f_j^-} \ge 0
  $$
- When branched upwards ($x_j \ge \lceil x_j^* \rceil$), the up-movement is $f_j^+ = \lceil x_j^* \rceil - x_j^* > 0$.
  The up unit degradation is:
  $$
  \Delta_j^+ = \frac{z_{\text{up}} - z_{\text{parent}}}{f_j^+} \ge 0
  $$
- Accumulated statistics for each variable $j$:
  - Down pseudocost: $\psi_j^- = \text{down\_sum}_j / \text{down\_count}_j$
  - Up pseudocost: $\psi_j^+ = \text{up\_sum}_j / \text{up\_count}_j$
- Reliability threshold: A variable's pseudocost is considered reliable if $\min(\text{down\_count}_j, \text{up\_count}_j) \ge K_{\text{reliable}}$ (default $K_{\text{reliable}} = 2$).

### 5.2 Deterministic Pseudocost Scoring
For fractional candidate $j$, the combined score is computed via standard product scoring:
$$
\text{score}_j = \max(\psi_j^- f_j^-, 10^{-6}) \times \max(\psi_j^+ f_j^+, 10^{-6})
$$
Ties are broken deterministically by smaller variable index $j$.

### 5.3 Limited Strong-Branching Bootstrap
For candidate integer variables with unreliable pseudocosts ($\min(\text{down\_count}_j, \text{up\_count}_j) < K_{\text{reliable}}$):
- A limited number of candidates (up to $C_{\text{max}} = 5$) with greatest fractionality $\min(f_j^-, f_j^+)$ are evaluated with trial dual-simplex solves capped at $I_{\text{max}} = 50$ iterations.
- If a trial solve establishes primal infeasibility, the opposite branch can be pruned or forced immediately.
- The observed degradations initialize the pseudocost accumulators $\psi_j^-$ and $\psi_j^+$.
- Parent basis state, node queue, and incumbent are strictly protected from mutation during trial solves.

---

## 6. Primal Heuristics

### 6.1 Safe Rounding Heuristic
Executed at promising nodes where integer fractionality is low ($\sum_j \min(f_j^-, f_j^+) \le 1.5$):
1. Integer variables with $|x_j^* - \text{round}(x_j^*)| \le 0.4$ are rounded to nearest integers.
2. Continuous variables are re-optimized by fixing integer variables to rounded values and solving the resulting continuous LP subproblem.
3. The candidate is independently verified via `verify(original_model, x_cand)`.
4. Only candidates passing feasibility, bound satisfaction, and integrality are accepted as incumbents.

### 6.2 Conservative Diving / Repair Heuristic
Executed at selected search depths with strict iteration and depth limits:
1. Select the fractional integer variable with greatest pseudocost score.
2. Fix the variable to its roundable direction and resolve the LP relaxation using dual-simplex warm start.
3. Repeat up to max dive depth (default 8).
4. If an integer feasible solution is produced, verify against the pristine original model.
5. Heuristics update only the incumbent (upper bound for minimization); they never alter conservative lower bounds or search tree proofs.

---

## 7. Mathematical Invariants & Safe Pruning

### 7.1 Pruning Invariants
A search node is pruned if and only if:
1. **Infeasible:** The relaxation is certified `INFEASIBLE_CERTIFIED` via exact Farkas ray.
2. **Bound Dominated:** The certified rational Lagrangian lower bound satisfies:
   $$
   B_{\text{node}} \ge U_{\text{incumbent}} - \epsilon_{\text{tol}}
   $$
3. **Integral:** The relaxation solution satisfies all integer constraints within integrality tolerance, fathoming the node.
4. **Contradictory:** Local bounds satisfy $l_j > u_j$.

### 7.2 Global Lower Bound Accounting
The global lower bound is the minimum certified lower bound across all open frontier nodes and tolerance-closed leaves:
$$
B_{\text{global}} = \min_{n \in \text{open} \cup \text{closed}} B_n
$$
For minimization with objective offset $c_0$, the reported bound is:
$$
B_{\text{reported}} = \text{downward\_float}(B_{\text{global}} + c_0)
$$
This guarantees $B_{\text{reported}} \le z^*$ unconditionally.
