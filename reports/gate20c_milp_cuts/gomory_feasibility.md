# Gomory / GMI Feasibility Audit — Gate 20C

**Repository:** `sov-opt-mrpl-26119`
**Problem Statement:** MRPL SIH 2026 PS 26119
**Date:** 2026-10-05
**Audit Target:** Feasibility of Gomory Fractional / Gomory Mixed-Integer (GMI) Cutting Planes in Sovereign Simplex

---

## 1. Audit Scope & Criteria

The generation of mathematically valid Gomory Mixed-Integer (GMI) or pure-integer Gomory cuts requires exact knowledge of the canonical optimal simplex tableau:
$$x_{B,i} + \sum_{j \in N} \bar{a}_{i,j} x_j = \bar{b}_i$$
In bounded-variable revised simplex ($l_j \le x_j \le u_j$), nonbasic variables reside at either their lower or upper bounds. Deriving a valid cut requires:
1. Exact row access to the basis inverse $B^{-1}$ and tableau row $\bar{a}_i = e_i^T B^{-1} M$.
2. Exact state classification for each nonbasic variable ($x_j = l_j$, $x_j = u_j$, or free).
3. Substitution of slack and surplus variables to express the cut strictly in terms of original structural variables $x \in \mathbb{R}^n$.
4. Strict numerical tolerances to prevent catastrophic cancellation when computing fractional parts $f_j = \bar{a}_{i,j} - \lfloor \bar{a}_{i,j} \rfloor$.

---

## 2. Technical Audit of Sovereign Simplex Engine

### 2.1 Final Basis Indices & State Access
- **Current State:** `sovopt.dual_simplex.solve_dual_simplex` returns a `DualBasisState` containing `basis: List[int]` (indices of basic variables in augmented matrix $M$) and `states: List[int]` (`BASIC`, `AT_LOWER`, `AT_UPPER`, `FREE_NONBASIC`, `FIXED`).
- **Limitation:** The indices refer to columns of the augmented system $M = [A, I_m] \in \mathbb{R}^{m \times (n+m)}$. Basic variables can be either structural variables ($0 \le j < n$) or slack variables ($n \le j < n+m$).

### 2.2 $B^{-1} A$ Tableau Row Access
- **Current State:** In `sovopt/dual_simplex.py`, $B^{-1}$ is maintained inside the internal `engine: SparseLUEngine` or dense LU factorization during the execution of `solve_dual_simplex`.
- **Limitation:** The factorization `engine` is local to `solve_dual_simplex` and is discarded upon termination. The public result dictionary `res_dict` does **not** expose a method to perform BTRAN ($e_i^T B^{-1}$) or compute tableau rows $\bar{a}_i = M^T (B^{-T} e_i)$ post-solve. Computing tableau rows externally would require refactoring the basis from scratch, introducing redundant $O(m^3)$ overhead and potential numerical discrepancies.

### 2.3 Handling of Bounds and Sign Conventions
- In standard bounded-variable simplex:
  - If nonbasic $x_j$ is at its upper bound ($x_j = u_j$), the distance from the bound is $u_j - x_j \ge 0$. The tableau coefficient must be negated: $\bar{a}'_{i,j} = -\bar{a}_{i,j}$.
  - If $x_j$ is free, it cannot be complemented to a non-negative variable; if any free variable has a fractional coefficient, the standard Gomory fractional cut is invalid unless split into positive/negative parts.
  - In `sovopt/dual_simplex.py`, slack variables have mixed signs:
    - Upper-bounded row $A_i x \le b_u \implies A_i x + s_i = b_u$ with $s_i \in [0, \infty)$.
    - Lower-bounded row $A_i x \ge b_l \implies A_i x + s_i = b_l$ with $s_i \in (-\infty, 0]$.
    - Equality row $A_i x = b \implies s_i \in [0, 0]$.
  - Substituting $s_i = b_i - A_i x$ into the tableau cut requires tracking whether $s_i$ was nonbasic at lower bound or nonbasic at upper bound, or basic.

### 2.4 Numerical Sensitivity of Fractional Parts
- In floating-point arithmetic, computing $f_j = \alpha_j - \lfloor \alpha_j \rfloor$ is notoriously ill-conditioned near integers. A coefficient $\alpha_j = 1.00000000000001$ yields $f_j \approx 10^{-14}$, whereas $\alpha_j = 0.99999999999999$ yields $f_j \approx 1.0 - 10^{-14}$.
- A small roundoff error in $B^{-1}$ can cause $f_j$ to flip from 0 to 1, completely inverting the cut inequality and **cutting off valid integer feasible points**.
- Without an exact rational basis solver or multi-precision arithmetic for tableau rows, GMI cuts derived from floating-point factorizations carry a high risk of invalid cuts.

---

## 3. Formal Decision

**Selected Option:**
### **C. NOT SAFE YET — COVER CUTS ONLY**

### Formal Rationale:
"Gomory/GMI cut separation is deferred because the current revised dual simplex engine does not export its basis factorization engine or tableau row extraction API post-solve, and the bounded-variable slack transformations do not yet expose sufficient invariant information for proof-safe separation. In accordance with the SOV-OPT core directive (Rule 1: Correctness over feature claims; zero invalid cuts permitted), we restrict Gate 20C cutting planes strictly to provably valid, closed-form **Binary Cover Inequalities**."
