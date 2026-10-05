# Sovereign MILP Architecture Audit — Gate 20C

**Repository:** `sov-opt-mrpl-26119`
**Problem Statement:** MRPL SIH 2026 PS 26119
**Date:** 2026-10-05
**Authoritative Base:** `d165b9e437644c276f817e2a4325d14fa89aeb32`

---

## 1. Executive Summary

This document audits the sovereign Mixed-Integer Linear Programming (MILP) subsystem within `sovopt/` to establish safe, mathematically rigorous integration boundaries for cutting planes (specifically Binary Cover Cuts and Gomory/GMI cuts).

---

## 2. Component Inventory & Implementation Locations

| MILP Component | Source File | Key Functions / Classes | Notes |
| :--- | :--- | :--- | :--- |
| **Branch-and-Bound Engine** | `sovopt/milp.py` | `solve_milp()` (lines 59–810) | Sovereign B&B coordinating tree search, node pruning, bounds, and heuristics. |
| **Node Structure** | `sovopt/milp.py` | `MILPNode` dataclass (lines 25–41) | Stores bounds, certified LP bound, basis state, parent ID, branch metadata. |
| **LP Relaxation Solver** | `sovopt/milp.py` | `solve_node_lp()` (lines 165–205) | Dispatches to `solve_dual_simplex` with warm start, cold dual simplex, then primal fallback. |
| **Simplex & Basis Engine** | `sovopt/dual_simplex.py` | `solve_dual_simplex()`, `DualBasisState` | Bounded-variable revised dual simplex with Devex pricing and sparse basis engine. |
| **Primal Simplex Fallback** | `sovopt/simplex.py` | `solve_lp()` | Two-phase primal simplex with Bland's rule and exact rational dual computation. |
| **Canonical Model** | `sovopt/model.py` | `Model` dataclass | Stores `c`, `A` (dense or CSR), `row_lower`, `row_upper`, `lower`, `upper`, `integer`. |
| **Variable Metadata** | `sovopt/model.py` | `model.integer`, `model.lower`, `model.upper` | Identifies 0-based integer/binary variables and finite variable boxes. |
| **Incumbent & Objective** | `sovopt/milp.py` | `exact_objective()`, `inc`, `incval` | Evaluates integer variables with exact integer rounding and exact `Fraction` arithmetic. |
| **Best Bound & Rational Cert.** | `sovopt/verify.py` | `safe_lower_bound()`, `downward_float` | Neumaier-Shcherbina exact rational Lagrangian dual bound certification. |
| **Pseudocost Branching** | `sovopt/milp.py` | `select_branching_variable()` (lines 444–522) | Directional score `q_down * q_up` with dynamic history tracking. |
| **Strong Branching Bootstrap**| `sovopt/milp.py` | `select_branching_variable()` (lines 456–501) | Evaluates up to 4 unreliable candidates with 50-iteration dual simplex probes. |
| **Primal Heuristics** | `sovopt/milp.py` | Safe Rounding (310–343), Diving (345–393) | Continuous subproblem solve and dual-simplex diving from root LP solution. |
| **Presolve Subsystem** | `sovopt/presolve.py`| `presolve_lp()` | Bound tightening, singleton elimination, and redundant row pruning. |
| **Node Selection Policy** | `sovopt/milp.py` | `select_next_node()` (lines 398–442) | Configurable: 'hybrid' (best-bound within 15% window, then deepest) or 'best_bound'. |
| **Node Pruning** | `sovopt/milp.py` | Lines 530, 577, 608, 651 | Prunes by bound (`bound >= incval`), bound conflict (`lo > hi`), LP infeasibility, or integrality. |
| **Optimality & Gap** | `sovopt/milp.py` | Lines 763–771, 791–799 | Relative gap $\frac{|incval - global\_lower|}{1 + |incval|}$; requires $\le tol$ for `OPTIMAL_VERIFIED`. |

---

## 3. Analysis of Cutting Plane Integration Boundaries

### 3.1 Where Cuts Can Safely Be Injected

1. **Root Node Cut Loop (Primary Injection Site)**
   - Located in `sovopt/milp.py` immediately after `solve_node_lp(root_model, basis_state=None)` returns `OPTIMAL_VERIFIED` with fractional integer variables, and *before* branching or root heuristics.
   - **Procedure:**
     1. Check if root LP solution $x^*$ has fractional integer variables $j \in \text{model.integer}$.
     2. Call cut separators (Cover Cuts, etc.) on the current model and fractional solution $x^*$.
     3. Filter and validate candidates (violation $\ge \text{tol}$, efficacy, finite coefficients, duplicate checks).
     4. If valid cuts exist, augment the model with the new cut rows ($A \leftarrow [A; A_{\text{cuts}}]$).
     5. Resolve the augmented LP relaxation via `solve_node_lp`.
     6. Update root certified lower bound (`safe_lower_bound`), root objective, and telemetry.
     7. Repeat for a bounded number of cut rounds (e.g. 1 to 5 rounds).
   - **Safety Guarantee:** Cuts generated at the root are **globally valid** across the entire branch-and-bound tree. They strengthen the initial relaxation bound without requiring complex tree-ancestry tracking.

2. **Branch Node Cuts (Secondary Injection Site)**
   - Can optionally be invoked at depth $> 0$, but adding local cuts requires strict local validity isolation. To eliminate risk of invalid cut leakage across parallel tree branches, **Gate 20C focuses strictly on globally valid cuts**.

### 3.2 LP Relaxation Representation & Augmentation

- The model's constraint system is defined by:
  - Matrix $A \in \mathbb{R}^{m \times n}$ (stored as `np.ndarray` or `CSRMatrix`).
  - Row bounds $\text{row\_lower} \in \mathbb{R}^m$, $\text{row\_upper} \in \mathbb{R}^m$.
- Adding $k$ cut inequalities of the form $\sum_{j} \alpha_{i,j} x_j \le \beta_i$:
  - $A_{\text{new}} = \begin{bmatrix} A \\ \alpha \end{bmatrix}$.
  - $\text{row\_lower}_{\text{new}} = [\text{row\_lower}; -\infty \cdot \mathbf{1}_k]$.
  - $\text{row\_upper}_{\text{new}} = [\text{row\_upper}; \beta]$.
- Both dense `np.vstack` and sparse `CSRMatrix` row stacking are fully supported in sovereign `sovopt/sparse.py`.

### 3.3 Basis and Tableau Information Availability

- `solve_dual_simplex` outputs `basis` (list of column indices in the basis), `states` (variable states: AT_LOWER, AT_UPPER, BASIC, FREE, FIXED), `x` (primal point), and `dual_exact_fraction` / `y` (dual multipliers).
- However, the basis inverse $B^{-1}$ and the tableau rows $B^{-1} A$ are maintained inside `SparseLUEngine` during the dual simplex solve and are **not** currently exported as an inspection API in `res_dict`.
- Consequently, generating tableau-based cuts (such as canonical Gomory mixed-integer cuts) requires either:
  - Re-factoring $B$ using sovereign LU, or
  - Exposing an explicit tableau row extraction method on `DualSimplex`.
  - A formal audit of tableau extraction feasibility is conducted in `reports/gate20c_milp_cuts/gomory_feasibility.md`.

### 3.4 Warm-Start and Row Addition

- Adding a constraint row to dual simplex increases the row dimension from $m$ to $m+1$.
- In classic dual simplex, a new slack variable $s_{m+1} = \beta - \alpha^T x^*$ can be introduced as basic with initial value $\beta - \alpha^T x^* < 0$. This basis is immediately dual feasible.
- In `sovopt/milp.py`, `solve_node_lp` cleanly falls back to cold dual simplex if warm-start dimension mismatch occurs. Cold dual simplex on small/medium models solves in milliseconds, providing an ultra-safe, rock-solid baseline.

### 3.5 Serialization Requirements

- In accordance with SIH requirements, all cut generation, cut validation, LP re-solves, and branch-and-bound iterations **must remain strictly deterministic and serial**. No multi-threading or parallel race conditions may be introduced into the core solver.
