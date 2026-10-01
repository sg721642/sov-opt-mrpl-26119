# Bounded-Variable Revised Dual Simplex Engine

This document specifies the mathematical foundation, algorithmic architecture, and numerical safeguards of the sovereign bounded-variable revised dual simplex solver in SOV-OPT (`sovopt/dual_simplex.py`).

## 1. Problem Formulation and Primal-Dual Relations

The solver operates on standard bounded-variable linear programs:
$$
\begin{aligned}
\min_{x \in \mathbb{R}^n} \quad & c^T x \\
\text{subject to} \quad & A x = b \\
& l \le x \le u
\end{aligned}
$$
where $l_j \in \mathbb{R} \cup \{-\infty\}$ and $u_j \in \mathbb{R} \cup \{+\infty\}$.

### 1.1 Variable States
Every variable $x_j$ ($j = 0, \dots, n-1$) is assigned exactly one state:
1. `BASIC (0)`: $x_j$ is in the basis $B$. Its value is determined by the linear system $B x_B = b - \sum_{k \in N} A_k x_k$.
2. `AT_LOWER (1)`: $x_j$ is non-basic with finite lower bound $l_j > -\infty$. Its value is $x_j = l_j$.
3. `AT_UPPER (2)`: $x_j$ is non-basic with finite upper bound $u_j < +\infty$. Its value is $x_j = u_j$.
4. `FREE_NONBASIC (3)`: $x_j$ is non-basic with $l_j = -\infty$ and $u_j = +\infty$. Its value is $x_j = 0$.
5. `FIXED (4)`: $x_j$ is non-basic with $l_j = u_j$. Its value is $x_j = l_j = u_j$.

### 1.2 Dual Feasibility Conditions
Let $B$ be a basis matrix of dimension $m \times m$ corresponding to basis indices $\{B(0), \dots, B(m-1)\}$.
The dual multipliers $y \in \mathbb{R}^m$ satisfy:
$$
B^T y = c_B \implies y = B^{-T} c_B = \text{btran}(c_B)
$$
The reduced costs $d \in \mathbb{R}^n$ are given by:
$$
d_j = c_j - A_j^T y = c_j - y^T A_j
$$
For basic variables, $d_{B(i)} = 0$ for all $i = 0, \dots, m-1$.

A basis $(B, x_N)$ is **dual feasible** (up to tolerance $\epsilon_{\text{dual}} > 0$) if and only if:
- $\forall j \in N$ `AT_LOWER`: $d_j \ge -\epsilon_{\text{dual}}$
- $\forall j \in N$ `AT_UPPER`: $d_j \le +\epsilon_{\text{dual}}$
- $\forall j \in N$ `FREE_NONBASIC`: $|d_j| \le \epsilon_{\text{dual}}$
- $\forall j \in N$ `FIXED`: no restriction on $d_j$.

### 1.3 Primal Feasibility (Optimality Test)
Given a dual-feasible basis, the solution is **primal optimal** if:
$$
l_{B(i)} - \epsilon_{\text{primal}} \le x_{B, i} \le u_{B(i)} + \epsilon_{\text{primal}} \quad \forall i = 0, \dots, m-1
$$

---

## 2. Devex Pricing (Leaving Row Selection)

When primal infeasibilities exist in the current basis, the dual simplex algorithm selects a leaving row $p \in \{0, \dots, m-1\}$ that exhibits a bound violation.

### 2.1 Bound Violation
For each row $i = 0, \dots, m-1$:
- If $x_{B, i} < l_{B(i)} - \epsilon_{\text{primal}}$, the row has a lower-bound violation:
  $$v_i = x_{B, i} - l_{B(i)} < 0 \quad (\sigma_i = +1)$$
- If $x_{B, i} > u_{B(i)} + \epsilon_{\text{primal}}$, the row has an upper-bound violation:
  $$v_i = x_{B, i} - u_{B(i)} > 0 \quad (\sigma_i = -1)$$
- Otherwise, $v_i = 0$.

### 2.2 Devex Weight Dynamics
Steepest-edge dual pricing requires computing $\|B^{-T} e_i\|_2$ at each iteration, which requires $m$ BTRAN operations. Devex pricing maintains an approximation $\gamma_i \approx \|B^{-T} e_i\|_2^2$ updated via recurrence relations:
1. **Initialization:** $\gamma_i = 1.0$ for all $i = 0, \dots, m-1$.
2. **Pricing Score:**
   $$\text{score}_i = \frac{v_i^2}{\gamma_i}$$
   Leaving row $p$ is chosen as:
   $$p = \arg\max_{i: |v_i| > \epsilon_{\text{primal}}} \text{score}_i$$
   Ties are broken deterministically by row index.
3. **Weight Update:** After pivot column $q$ enters with FTRAN direction $d = B^{-1} A_q$ and pivot $\beta = d_p$:
   - For leaving row $p$:
     $$\gamma_p^{\text{new}} = \frac{\gamma_p}{\beta^2}$$
   - For other rows $i \neq p$:
     $$\gamma_i^{\text{new}} = \max\left(\gamma_i, \left(\frac{d_i}{\beta}\right)^2 \gamma_p\right)$$
4. **Weight Resets:** $\gamma_i$ is reset to $1.0$ upon refactorization or every 50 iterations to prevent drift.

---

## 3. Two-Pass Harris Dual Ratio Test (Entering Column Selection)

Let row $p$ be the leaving row with sign $\sigma_p \in \{+1, -1\}$.
We compute the tableau row $\bar{\alpha}_p$ via BTRAN:
$$
\pi_p = B^{-T} e_p = \text{btran}(e_p), \quad \bar{\alpha}_{p, j} = A_j^T \pi_p
$$

### 3.1 Candidate Directional Pivot
For each non-basic column $j \in N$:
- If $j$ is `AT_LOWER`: directional pivot $s_j = -\sigma_p \bar{\alpha}_{p, j}$.
- If $j$ is `AT_UPPER`: directional pivot $s_j = \sigma_p \bar{\alpha}_{p, j}$.
- If $j$ is `FREE_NONBASIC`:
  - If $-\sigma_p \bar{\alpha}_{p, j} > \epsilon_{\text{piv}}$, $s_j = -\sigma_p \bar{\alpha}_{p, j}$.
  - If $\sigma_p \bar{\alpha}_{p, j} > \epsilon_{\text{piv}}$, $s_j = \sigma_p \bar{\alpha}_{p, j}$.
- If $j$ is `FIXED`: not eligible ($s_j = 0$).

A column $j$ is eligible if $s_j > \epsilon_{\text{piv}} = 10^{-8}$.
If no column is eligible, the LP is certified **PRIMAL INFEASIBLE** (dual ray detected).

### 3.2 Two-Pass Harris Selection
Let $\delta = 10^{-7}$ be the Harris numerical expansion tolerance.
1. **Pass 1 (Relaxed Step Bound):**
   For each eligible $j$:
   $$\theta_j = \frac{\max(0, \text{dist}_j)}{s_j}, \quad \theta_j^{\text{relaxed}} = \frac{\max(0, \text{dist}_j) + \delta}{s_j}$$
   where $\text{dist}_j = d_j$ if `AT_LOWER`, $-d_j$ if `AT_UPPER`, and $|d_j|$ if `FREE_NONBASIC`.
   Compute upper bound:
   $$\theta_{\max} = \min_{j \in \text{eligible}} \theta_j^{\text{relaxed}}$$

2. **Pass 2 (Pivot Maximization):**
   Among all eligible columns satisfying $\theta_j \le \theta_{\max}$, choose entering variable $q$ that maximizes the pivot magnitude $s_j$:
   $$q = \arg\max_{j: \theta_j \le \theta_{\max}} s_j$$
   Deterministic tie-breaking: prefer smaller column index $j$.

---

## 4. Bound Flipping Without Refactorization

If the chosen column $q$ has a finite opposite bound:
- $\Delta x_q = u_q - l_q < \infty$.
- The maximum change in basic variable $x_{B, p}$ achievable by flipping $q$ across its bounds is:
  $$\Delta x_{B, p} = s_q \cdot \Delta x_q$$
- If $\Delta x_{B, p} < |v_p|$:
  The variable $q$ can be moved from its current bound to its opposite bound:
  - If `AT_LOWER`: set $x_q = u_q$, new state `AT_UPPER`.
  - If `AT_UPPER`: set $x_q = l_q$, new state `AT_LOWER`.
  This updates $x_B \leftarrow x_B - A_q \Delta x_q$ **without modifying the basis matrix or computing any LU updates**.
  The remaining violation on row $p$ is reduced by $\Delta x_{B, p}$, and the ratio test continues on row $p$.
- When $\Delta x_{B, p} \ge |v_p|$ (or $q$ is unconstrained in that direction), $q$ enters the basis and row $p$ leaves.

---

## 5. Dual Phase I and Clean Fallback Hierarchy

### 5.1 Dual Phase I via Artificial Bounds
If the initial non-basic variables have reduced costs that violate dual feasibility ($d_j < 0$ at $l_j = 0$ with $u_j = +\infty$), sovereign Dual Phase I applies an artificial upper bound $M_{\text{art}} = 10^8$. Setting $x_j = M_{\text{art}}$ (`AT_UPPER`) makes $d_j \le 0$ dual-feasible immediately. Dual simplex pivots until all artificial bounds become non-basic at $0$, certifying dual feasibility for the original model.

### 5.2 Clean Fallback Hierarchy
If dual feasibility cannot be established or numerical breakdown occurs:
1. The solver attempts refactorization and re-pricing.
2. If unresolved, it transitions cleanly to the primal revised simplex workhorse.
3. The result telemetry honestly records:
   - `requested_method: "dual-simplex"`
   - `actual_method: "primal-simplex"`
   - `fallback_reason: "<explicit numerical description>"`
