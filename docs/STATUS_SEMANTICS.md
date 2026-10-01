# SOV-OPT Solver Status Semantics

**Version:** 0.1.6  
**Applies to:** `sovopt/simplex.py`, `sovopt/milp.py`, `sovopt/qp.py`, `sovopt/pdhg.py`

Every result dict returned by `solve()`, `solve_lp()`, `solve_milp()`, `solve_qp()`,
and `solve_pdhg()` contains a `status` field. This document defines precisely what
each status value means, what certificates accompany it, and what it does NOT claim.

---

## Status Values

### `OPTIMAL_VERIFIED`

**Meaning:** Numerically verified global optimum for the supported convex problem class
within stated tolerances; not a formal exact-rational or interval proof.

For LP and supported convex QP, satisfaction of the first-order Karush-Kuhn-Tucker (KKT)
primal-dual conditions is both necessary and sufficient for global optimality. In SOV-OPT,
these conditions are verified independently in `sovopt/verify.py` using IEEE 754
floating-point arithmetic within the user-specified tolerance `tol`.

**What is checked:**
- Primal feasibility: all row constraints and variable bounds satisfied within `tol`.
- Dual non-negativity: dual multipliers `z >= 0` (for inequality constraints).
- Stationarity: `c + G^T z ≈ 0` (or `Qx + c + G^T z ≈ 0` for QP).
- Complementary slackness: `z_i * (G_i x - h_i) ≈ 0`.

**What this is NOT:**
- Not a formal exact-rational or interval-arithmetic optimality proof (checks are
  evaluated in IEEE 754 floating-point arithmetic within tolerance `tol`).
- For MILP: not an exact rational optimality certificate. Incumbent feasibility is
  verified numerically; relative gap is floating-point (see `optimality_basis` field).

**Accompanying fields:** `x`, `dual`, `verification` (full KKT report), `objective`.

---

### `INFEASIBLE_CERTIFIED`

**Meaning:** The LP (or LP relaxation) is provably infeasible. An exact rational
Farkas certificate is constructed and independently verified.

**What is checked:**
- Phase I sum of artificials > 1e-8 (infeasibility detected).
- Farkas certificate `z` satisfies exactly (via Fraction arithmetic):
  `G^T z == 0`, `h^T z < 0`, `z >= 0`.

**What this is NOT:**
- For MILP: infeasibility of a node LP relaxation does not imply the overall MILP
  is infeasible unless every branch is certified.

**Accompanying fields:** `certificate` (float), `certificate_exact` (lossless p/q strings),
`verification.farkas_verified`, `farkas_certificate`.

---

### `UNBOUNDED_CERTIFIED`

**Meaning:** The LP is unbounded — there exists a certified certificate pair $(x_0, d)$
consisting of a feasible base point $x_0$ and an improving recession direction $d$
along which the objective decreases (or increases for maximization) without bound.
The complete certificate is independently verified by `verify_unbounded_certificate()`
against the original model before this status is assigned.

`UNBOUNDED_CERTIFIED` is returned **ONLY** when BOTH conditions hold:
1. `base_feasible == True`: $x_0$ is a feasible point for the original model within `tol`.
2. `ray_verified == True`: $d$ is a valid recession direction for the original model within `tol`.

If either condition fails, the solver returns `NUMERICAL_FAILURE`.

**What is checked (by `verify_unbounded_certificate`):**
1. **Base point feasibility ($x_0$):**
   - Correct dimension and finite components.
   - All original row lower and upper bounds satisfied within `tol`.
   - All original variable lower and upper bounds satisfied within `tol`.
2. **Row recession conditions ($d$):**
   - Finite lower AND finite upper (equality or ranged row): $|A_i d| \le \text{rtol}$.
   - Finite upper only: $A_i d \le \text{rtol}$.
   - Finite lower only: $A_i d \ge -\text{rtol}$.
   - No finite row bound: unrestricted.
3. **Variable bound directions ($d$):**
   - Finite lower AND finite upper: $|d_j| \le \text{tol}$ (bounded variable).
   - Finite lower only: $d_j \ge -\text{tol}$.
   - Finite upper only: $d_j \le \text{tol}$.
   - Free variable: unrestricted.
4. **Objective improvement:**
   - Internal canonical minimization form: $c^T d < 0$.
   - Original problem sense: objective strictly improves (decreases to $-\infty$ for min,
     increases to $+\infty$ for max).
5. **Purely linear direction postsolve:**
   - Recession directions transform strictly through the linear mapping $d_x = D d_t$
     via `postsolve_direction()`. Affine shifts $s$ are never added to directions.

**Accompanying fields:** `base_point` ($x_0$), `ray` ($d$), `x` ($x_0$), `ray_verification`
dict containing `verified`, `base_feasible`, `ray_verified`, `base_primal_residual`,
`objective_direction`, `original_objective_direction`, `max_row_direction_violation`,
`max_bound_direction_violation`, `message`.

---

### `LIMIT_REACHED`

**Meaning:** The solver exhausted its iteration budget (`max_iter` for simplex/QP/PDHG,
`max_nodes` for branch-and-bound) without achieving `OPTIMAL_VERIFIED` or
`INFEASIBLE_CERTIFIED`.

**For LP/QP/PDHG:** The last iterate is available in `x` and `verification` but KKT
is not satisfied within `tol`. The solution is a best-effort intermediate point.

**For MILP:** `best_bound` is a conservative valid lower bound on the optimal integer
objective, computed from exact rational Lagrangian bounds over the explored tree.
`objective` (if present) is the best incumbent found. `relative_gap` is defined as
`max(0, incumbent - bound) / (1 + |objective|)`.

**Accompanying fields:** `x` (if any iterate available), `best_bound`, `relative_gap`,
`open_nodes`, `nodes`.

---

### `NUMERICAL_FAILURE`

**Meaning:** The solver detected an internal numerical problem (singular basis, lost
primal feasibility, nonfinite iterates, or an unverified unbounded certificate).
No result can be trusted from this run.

**What to do:**
- Inspect `message` for the specific failure reason.
- Try with `scaling=False` (simplex already retries once automatically).
- Check the model for extreme dynamic range or near-degenerate structure.

**Accompanying fields:** `message`, and optionally `ray_verification` if the failure
was due to a failed certificate check.

---

### Model Validation Exceptions (`ValueError`)

`Model.validate()` enforces dimensional, bound, and coefficient consistency immediately
upon model creation or before solving. When a model violates structural constraints
(e.g., non-finite coefficients, contradictory bounds $l_j > u_j$, non-PSD $Q$), a
`ValueError` exception is raised immediately. It is a Python exception, not a status
code in a returned result dictionary.

---

## Verification Architecture

```
solve_lp() / solve_qp() / solve_milp() / solve_pdhg()
    │
    ├── sovopt/verify.py::verify()                     KKT check (floating-point)
    ├── sovopt/verify.py::exact_farkas()               Farkas check (exact rational Fractions)
    ├── sovopt/verify.py::safe_lower_bound()           Lagrangian lower bound (exact rational)
    └── sovopt/verify.py::verify_unbounded_certificate() Complete certificate (x0, d) check
```

**All checks are floating-point unless explicitly marked "exact rational".**
Exact rational checks use Python `fractions.Fraction` on IEEE 754 binary64 inputs,
which are losslessly representable as rational numbers.

---

## Status Transition Rules

| Status | Implies feasibility? | Implies optimality? | Certificate type |
|---|---|---|---|
| `OPTIMAL_VERIFIED` | Yes (floating-point) | Yes (floating-point KKT global optimum for convex models) | KKT multipliers |
| `INFEASIBLE_CERTIFIED` | No | N/A | Exact rational Farkas |
| `UNBOUNDED_CERTIFIED` | Yes (verified at $x_0$) | N/A (improving direction $d$) | Certified pair $(x_0, d)$ |
| `LIMIT_REACHED` | Unknown | No | Conservative rational bound (MILP only) |
| `NUMERICAL_FAILURE` | Unknown | No | None |

---

## Honest Limitations & Public Benchmark Status

- All floating-point KKT checks are necessary and sufficient for global optimality
  of continuous convex problems, evaluated numerically within tolerance `tol`.
- Exact rational Farkas and Lagrangian bounds use the binary64 model coefficients as
  exact rationals; they do not account for measurement error in input data.
- The simplex implementation is dense (no sparse infrastructure in this version).
- **Public Infeasible Certificate Benchmark:** `WOODINFE` from the official HiGHS test
  suite (`data/verified/woodinfe.mps`) is admitted as a genuine public infeasible LP
  benchmark with verified exact rational Farkas certificate.
- **Public Unbounded Certificate Benchmark:** Search of authoritative public archives
  (Netlib LP, HiGHS test suite) confirmed that no authentic public unbounded LP
  instances in standard MPS format are available. Therefore:
  **PUBLIC UNBOUNDED CERTIFICATE BENCHMARK: NOT YET AVAILABLE**.
  Unit test instances in `tests/test_solver.py` are strictly labeled
  `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA` and are explicitly excluded
  from public benchmark counts and performance reports.

---

*This document is part of the SOV-OPT architecture specification.*  
*See also: docs/ARCHITECTURE.md, docs/VALIDATION.md, sovopt/verify.py*
