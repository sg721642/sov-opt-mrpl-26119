# SOV-OPT Solver Status Semantics

**Version:** 0.1.5  
**Applies to:** `sovopt/simplex.py`, `sovopt/milp.py`, `sovopt/qp.py`, `sovopt/pdhg.py`

Every result dict returned by `solve()`, `solve_lp()`, `solve_milp()`, `solve_qp()`,
and `solve_pdhg()` contains a `status` field. This document defines precisely what
each status value means, what certificates accompany it, and what it does NOT claim.

---

## Status Values

### `OPTIMAL_VERIFIED`

**Meaning:** The solver found a candidate solution `x` that passes the independent
floating-point KKT check in `sovopt/verify.py`.

**What is checked:**
- Primal feasibility: all row constraints and variable bounds satisfied within `tol`.
- Dual non-negativity: dual multipliers `z >= 0` (for inequality constraints).
- Stationarity: `c + G^T z ≈ 0` (or `Qx + c + G^T z ≈ 0` for QP).
- Complementary slackness: `z_i * (G_i x - h_i) ≈ 0`.

**What this is NOT:**
- Not a formal interval-arithmetic or exact rational optimality certificate.
- Not a proof that no better feasible solution exists globally.
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

**Meaning:** The LP is unbounded — there exists a feasible recession direction `d`
along which the objective decreases without bound. The direction is independently
verified by `verify_unbounded_ray()` before this status is assigned.

**What is checked (by `verify_unbounded_ray`):**
1. **Improving direction:** `c^T d < 0` (for minimization; `c` is internal form).
2. **Row recession:** For each row constraint, `A[i] @ d` satisfies the recession
   condition for that row's bound type (equality, upper, lower, or range).
3. **Variable bound directions:** For each variable, `d[j]` is consistent with the
   variable's bound type (non-negative for lower-bounded-only variables, etc.).

**What this is NOT:**
- Not certifying that the LP has a feasible point (feasibility is assumed from the
  Phase I completion; the recession direction is verified independently).
- Floating-point verification, not exact rational.

**Accompanying fields:** `ray` (verified direction vector), `ray_verification` dict
containing `verified`, `obj_direction`, `max_row_violation`, `max_bound_violation`,
`message`.

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
primal feasibility, nonfinite iterates, or an `UNBOUNDED_CERTIFIED` direction that
failed independent verification). No result can be trusted from this run.

**What to do:**
- Inspect `message` for the specific failure reason.
- Try with `scaling=False` (simplex already retries once automatically).
- Check the model for extreme dynamic range or near-degenerate structure.

**Accompanying fields:** `message`, and optionally `ray_verification` if the failure
was due to a failed ray check.

---

### `INVALID_MODEL`

**Meaning:** The model failed structural validation (`Model.validate()`) before solving.
This is raised as a `ValueError` rather than returned as a status dict.

---

## Verification Architecture

```
solve_lp() / solve_qp() / solve_milp() / solve_pdhg()
    |
    |-- sovopt/verify.py::verify()              KKT check (floating-point)
    |-- sovopt/verify.py::exact_farkas()        Farkas check (exact rational Fractions)
    |-- sovopt/verify.py::safe_lower_bound()    Lagrangian lower bound (exact rational)
    +-- sovopt/verify.py::verify_unbounded_ray() Ray check (floating-point)
```

**All checks are floating-point unless explicitly marked "exact rational".**
Exact rational checks use Python `fractions.Fraction` on IEEE 754 binary64 inputs,
which are losslessly representable as rational numbers.

---

## Status Transition Rules

| Status | Implies feasibility? | Implies optimality? | Certificate type |
|---|---|---|---|
| `OPTIMAL_VERIFIED` | Yes (floating-point) | Yes (floating-point KKT) | KKT multipliers |
| `INFEASIBLE_CERTIFIED` | No | N/A | Exact rational Farkas |
| `UNBOUNDED_CERTIFIED` | Assumed (Phase I passed) | N/A (minus-infinity) | Verified floating-point ray |
| `LIMIT_REACHED` | Unknown | No | Conservative rational bound (MILP only) |
| `NUMERICAL_FAILURE` | Unknown | No | None |

---

## Honest Limitations

- All floating-point KKT checks are necessary but not sufficient conditions for exact
  optimality. They are not formal mathematical proofs.
- Exact rational Farkas and Lagrangian bounds use the binary64 model coefficients as
  exact rationals; they do not account for measurement error in input data.
- The simplex implementation is dense (no sparse infrastructure in this version).
- `UNBOUNDED_CERTIFIED` from the simplex path uses the Phase II entering column
  direction; if the basis is numerically ill-conditioned, verification may fail and
  `NUMERICAL_FAILURE` is returned instead.

---

*This document is part of the SOV-OPT architecture specification.*
*See also: docs/ARCHITECTURE.md, docs/VALIDATION.md, sovopt/verify.py*
