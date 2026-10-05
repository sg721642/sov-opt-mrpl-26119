# Gate 20D: Serial Branch-and-Bound Architecture Audit

**Repository:** `sov-opt-mrpl-26119`
**Problem Statement:** MRPL SIH 2026 PS 26119
**Date:** 2026-10-05
**Authoritative Base Commit:** `fb2dbc5f82b9d488c8d56bab15e29c44a8575fe5`

---

## 1. Executive Overview

This document audits the sovereign branch-and-bound (B&B) solver in `sovopt/milp.py` prior to the integration of intra-solve parallel branch-and-bound.

The core algorithm is a single-process, deterministic B&B search with:
- Exact rational objective calculation (`exact_objective`) using Python `Fraction`
- Exact rational safe lower bounding (`safe_lower_bound`)
- Conservative integer feasibility verification (`verify`) against the untouched original model (`orig_model`)
- Root-level cutting-plane loop (`sovopt/cuts.py`)
- Warm-started dual simplex LP relaxations (`DualBasisState`)
- Hybrid best-bound / depth node selection policy
- Pseudocost branching with limited strong-branching bootstrap

---

## 2. Component Inventory & Code Map

### A. Data Structures (`MILPNode`)
- **Location:** `sovopt/milp.py:25-42`
- **Fields:**
  - `node_id: int` (monotonically increasing integer ID)
  - `parent_id: Optional[int]`
  - `depth: int`
  - `branch_variable: Optional[int]`
  - `branch_direction: Optional[str]` ('down' or 'up')
  - `branch_value: Optional[float]`
  - `local_lower_bounds: np.ndarray` (per-variable box lower bound)
  - `local_upper_bounds: np.ndarray` (per-variable box upper bound)
  - `certified_lp_bound: Any` (`Fraction` or `-math.inf`)
  - `lp_status: Optional[str]` (`OPTIMAL_VERIFIED`, `INFEASIBLE_CERTIFIED`, etc.)
  - `basis_state: Optional[DualBasisState]` (basis factorization cache for warm start)
  - `warm_start_source: Optional[str]`
  - `creation_order: int`
  - `x_sol: Optional[np.ndarray]` (relaxed LP solution vector)

### B. Node Selection
- **Location:** `sovopt/milp.py:490-536`
- **Policies:**
  - `best-bound`: Selects node with minimal `certified_lp_bound`; ties broken by deeper depth and lower creation order.
  - `hybrid`: Computes threshold $T = \min(b) + 0.15 \max(1.0, |\min(b)|)$ and selects the deepest node whose bound is $\le T$.

### C. Branch Variable Selection
- **Location:** `sovopt/milp.py:538-616`
- **Strategy:**
  - Pseudocost branching ($q_{\text{down}} \times q_{\text{up}}$ score).
  - Strong branching bootstrap on unreliable candidates ($\min(\text{count}_{\text{down}}, \text{count}_{\text{up}}) < 2$) evaluating up to 4 candidates with 50-iteration dual simplex limits.
  - Fallback to most-fractional variable selection when pseudocosts are disabled.

### D. Incumbent & Pruning Logic
- **Location:** `sovopt/milp.py:623-648, 744-770`
- **Incumbent:** Evaluated in exact rational arithmetic via `exact_objective(orig_model, xr)` and verified by `verify(orig_model, xr)`.
- **Pruning by Bound:** If $b_{\text{node}} \ge \text{incval}$ (in exact rational comparison), the node is pruned immediately without branching.
- **Pruning by Infeasibility:** If local bounds conflict ($l_j > u_j$) or the LP relaxation returns `INFEASIBLE_CERTIFIED`, the node is pruned.
- **Pruning by Integrality:** If all integer variables satisfy integrality tolerance ($|x_j - \text{round}(x_j)| \le \text{tol}$), the node is verified, may update incumbent, and is closed (`pruned_by_integrality`).

### E. Child Node Generation & LP Relaxation
- **Location:** `sovopt/milp.py:651-732`
- For each branch direction ('down' and 'up'):
  1. Restrict local bounds $u_j \gets \lfloor x_j \rfloor$ or $l_j \gets \lceil x_j \rceil$.
  2. Solve child LP via `solve_node_lp(child_model, basis_state=parent.basis_state)`.
  3. Extract certified rational lower bound `safe_lower_bound(child_model, dual_exact)`.
  4. Update pseudocost tracking stats.
  5. Check incumbent cutoff; if not cut off, add to `open_nodes`.

### F. Global Lower Bound & Optimality Gap
- **Location:** `sovopt/milp.py:813-827`
- Candidates: all bounds in `open_nodes` + bounds from `tolerance_closed` nodes + `incval`.
- Global lower bound is $\min(\text{candidates})$.
- Relative gap: $\frac{\text{incval} - \text{global\_lower}}{1.0 + |\text{incval}|}$.
- Optimality verified when `open_nodes == []` and `gap <= tol`.

---

## 3. Bottlenecks & Parallelization Opportunities

1. **Child LP Relaxation:** Each node requires solving a dual simplex linear program (typically 1 to 50 iterations with warm start, or hundreds for harder MIPs). In serial execution, node relaxations are strictly sequential.
2. **Subtree Independence:** Once a node's bounds are established, its LP relaxation and subsequent branching are mathematically independent of other open nodes.
3. **Information Sharing:** Only two pieces of information need to flow between tree branches:
   - **Incumbent value**: Tightening incumbent allows other subtrees to prune earlier.
   - **Global best bound**: Requires knowing the lower bounds of all unresolved subtrees.
