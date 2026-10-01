# QPLIB Support & Convex Continuous QP Specification — SOV-OPT

**MRPL SIH Problem Statement 26119**  
**Specification Reference:** QPLIB 2018 (Furini et al., *Mathematical Programming Computation*, 2019)  
**Primary Source:** https://qplib.zib.de/doc.html  
**Solver Version:** `0.3.1`  
**Core Dependencies:** Python standard library and NumPy only.

---

## 1. Overview and Problem Formulation

SOV-OPT provides native, sovereign parsing and solution support for continuous, convex Quadratic Programs (QP) formatted in the official **QPLIB** benchmark format (`.qplib`).

In accordance with official QPLIB documentation ([qplib.zib.de/doc.html](https://qplib.zib.de/doc.html)), the mathematical optimization problem is defined as:

$$\min_{x \in \mathbb{R}^n} \left[ \frac{1}{2} x^T Q^0 x + (b^0)^T x + q^0 \right]$$

subject to:

$$l_i \le \frac{1}{2} x^T Q^i x + (b^i)^T x \le u_i, \quad i = 1, \dots, m$$

$$l^{\text{var}}_j \le x_j \le u^{\text{var}}_j, \quad j = 1, \dots, n$$

> [!IMPORTANT]
> **Mandatory Factor of 1/2:** The factor $\frac{1}{2}$ precedes the quadratic form $x^T Q^0 x$ in the objective. Off-diagonal coefficients in QPLIB files specify entries $Q^0_{ij}$ for $i \ge j$. When assembling symmetric matrix $Q$, off-diagonal terms are split equally: $Q_{ij} = Q_{ji} = \frac{1}{2} Q^0_{ij}$ for $i \neq j$.

---

## 2. Problem Classification (`PROBTYPE`) and Support Envelope

Every QPLIB instance declares a 3-character `PROBTYPE` encoding problem structure:
1. **Objective Type:**
   - `C`: Continuous/Convex Quadratic
   - `D`: Diagonal Quadratic
   - `L`: Linear
   - `Q`: General Quadratic (potentially Nonconvex)
2. **Constraint Type:**
   - `L`: Linear Constraints ($Q^i = 0$ for all $i \ge 1$)
   - `B`: Box/Bound Constraints Only ($m = 0$)
   - `Q`: Quadratic Constraints (QCQP)
   - `N`: Non-linear Constraints
3. **Variable Domain:**
   - `C`: Continuous ($x_j \in \mathbb{R}$)
   - `B`: Binary ($x_j \in \{0, 1\}$)
   - `M`: Mixed-Integer ($x \in \mathbb{R}^{n_c} \times \mathbb{Z}^{n_i}$)
   - `I`: Pure Integer ($x_j \in \mathbb{Z}$)

### 2.1 Admitted Continuous Convex Classes

SOV-OPT admits instances matching:
- `CCL`: Continuous Convex Quadratic Objective with Linear Constraints
- `DCL`: Continuous Diagonal Quadratic Objective with Linear Constraints
- `CCB`: Continuous Convex Quadratic Objective with Box Constraints Only
- `DCB`: Continuous Diagonal Quadratic Objective with Box Constraints Only
- `LCL`: Continuous Linear Objective with Linear Constraints (admitted via standard LP pipeline)

### 2.2 Rigorous Rejection Classes

Any instance falling outside the convex continuous envelope is immediately rejected with a typed `UnsupportedQPLIBError`:

| Condition / Problem Class | Error Code | Rationale & Safety Invariant |
| :--- | :--- | :--- |
| Discrete variables present (`M`, `B`, `I`) | `UNSUPPORTED_DISCRETE_VARIABLES` | Sovereign MIQP/B&B branch-and-bound on quadratic relaxations is not certified in Gate 7. |
| Quadratic constraints present ($Q^i \neq 0$ or constraint char `Q`) | `UNSUPPORTED_QUADRATIC_CONSTRAINTS` | Quadratically constrained QP (QCQP) requires second-order cone or SOCP interior-point barriers. |
| Nonconvex quadratic objective ($\lambda_{\min} < -\tau$) | `UNSUPPORTED_NONCONVEX_QP` | Mehrotra predictor-corrector requires $Q \succeq 0$. Nonconvex QP could diverge or return non-optimal saddle points. |
| Dimension limit exceeded ($n > 5000$ or memory $> 250$ MB) | `DIMENSION_LIMIT_EXCEEDED` | Dense quadratic representation $Q \in \mathbb{R}^{n \times n}$ guarded against memory exhaustion before allocation. |

---

## 3. Scale-Aware Convexity Verification

Convexity is verified dynamically by inspecting the eigenvalues of the assembled symmetric quadratic matrix $Q$:

$$\tau = 10^{-10} \times \max\left(1.0, \max_{1 \le i \le n} |Q_{ii}|\right)$$

$$\lambda_{\min}(Q) \ge -\tau \implies Q \succeq 0 \quad (\text{Convex})$$

If $\lambda_{\min}(Q) < -\tau$, the model is rejected with `UNSUPPORTED_NONCONVEX_QP`.

### Authentic Negative Rejection Test (`QPLIB_0018`)
- **Instance:** `QPLIB_0018`
- **Official PROBTYPE:** `QCL` (Continuous Nonconvex Quadratic Objective, Linear Constraints)
- **Minimum Eigenvalue:** $\lambda_{\min} \approx -6.386 < 0$
- **Solver Behavior:** Safely rejected at parse stage without allocating unsafe dense structures or reporting spurious solutions.

---

## 4. Native Equality-Aware Mehrotra Predictor-Corrector QP Algorithm

Convex QPs are solved using an equality-aware infeasible-start primal-dual interior point method (`sovopt/qp.py`):
1. **Native Partitioning:**
   $$\min \frac{1}{2} x^T Q x + c^T x \quad \text{s.t.} \quad E x = f, \quad G x \le h$$
   - Equality rows ($l_i = u_i$) and fixed variables are represented natively in $E x = f$ without slacks or barrier penalties.
   - Dual multipliers $y \in \mathbb{R}^{m_e}$ are free (unrestricted in sign).
   - Slacks $s > 0$ and duals $z \ge 0$ exist exclusively for genuine inequalities $G x \le h$.
2. **Reduced Augmented Saddle-Point System:**
   $$\begin{bmatrix} H + \delta_p I & E^T \\ E & -\delta_d I \end{bmatrix} \begin{bmatrix} \Delta x \\ \Delta y \end{bmatrix} = \begin{bmatrix} \text{rhs}_x \\ -r_e \end{bmatrix}$$
   where $H = Q + G^T \text{diag}(z/s) G$, solved with 1 step of iterative refinement against the unregularized operator.
3. **Predictor-Corrector Steps:**
   - Affine predictor step solves for $(\Delta x^{\text{aff}}, \Delta y^{\text{aff}}, \Delta s^{\text{aff}}, \Delta z^{\text{aff}})$.
   - Centering parameter $\sigma = (\mu_{\text{aff}} / \mu)^3$ is computed from affine slacks and inequality duals.
   - Combined Mehrotra corrector step incorporates second-order perturbation $\Delta S^{\text{aff}} \Delta Z^{\text{aff}} \mathbf{1} - \sigma \mu \mathbf{1}$.
   - Step sizes $\alpha_p, \alpha_d$ are determined with fraction-to-boundary factor $\eta = 0.995$ applied to $s$ and $z$ only.

---

## 5. Independent Postsolve and KKT Residual Verification

Upon termination, the primal solution $x \in \mathbb{R}^n$ and dual multipliers $y, z$ are checked by `sovopt/verify.py` against the **original untransformed model**:

1. **Primal Feasibility:**
   $$\| (A x - b)^+ \|_\infty \le 10^{-7}$$
   $$l^{\text{var}}_j - x_j \le 10^{-7}, \quad x_j - u^{\text{var}}_j \le 10^{-7}$$
2. **Dual Stationarity:**
   $$\| Q x + c - A^T y - z \|_\infty \le 10^{-7}$$
3. **Complementary Slackness:**
   $$\max_j |z_j (x_j - \text{bound}_j)| \le 10^{-7}$$
4. **Objective Alignment:**
   Reported objective must match:
   $$\text{obj} = \frac{1}{2} x^T Q^0 x + (b^0)^T x + q^0$$
   to machine precision ($\le 10^{-12}$).
