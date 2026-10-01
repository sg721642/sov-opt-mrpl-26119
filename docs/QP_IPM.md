# Sovereign Equality-Aware Primal-Dual Interior-Point Method for Convex QP

**SOV-OPT Research Prototype**  
**Problem Statement:** MRPL SIH PS 26119  
**Module:** `sovopt/qp.py`, `sovopt/verify.py`

---

## 1. Mathematical Problem Formulation

SOV-OPT solves the general convex quadratic programming problem:

$$\min_{x \in \mathbb{R}^n} \; \frac{1}{2} x^T Q x + c^T x + q$$

subject to:

$$E x = f \quad (m_e \text{ linear equality constraints})$$
$$G x \le h \quad (m_i \text{ linear inequality constraints})$$

where:
- $Q \in \mathbb{R}^{n \times n}$ is symmetric positive semidefinite ($Q \succeq 0$).
- $c \in \mathbb{R}^n$ is the linear objective vector.
- $q \in \mathbb{R}$ is the scalar objective offset.
- $E \in \mathbb{R}^{m_e \times n}, f \in \mathbb{R}^{m_e}$ represent explicit equality constraints where $l_i = u_i$.
- $G \in \mathbb{R}^{m_i \times n}, h \in \mathbb{R}^{m_i}$ represent genuine inequality rows and finite variable bounds:
  - Upper row inequality: $a_i^T x \le u_i$
  - Lower row inequality: $-a_i^T x \le -l_i$
  - Upper variable bound: $x_j \le u_j$
  - Lower variable bound: $-x_j \le -l_j$

---

## 2. Audit of Prior Implementation vs. Native Equality System

### 2.1 The Prior Defect: Paired Barrier Inequalities
In the legacy implementation (`sovopt/qp.py` prior to Gate 7.2), all constraints were flattened via `model.inequalities()`. For an equality constraint $a_i^T x = b_i$, the model produced two opposing inequalities:
$$a_i^T x \le b_i \quad \text{and} \quad -a_i^T x \le -b_i$$
In an interior-point method with logarithmic barrier terms, slacks $s_1, s_2 > 0$ are assigned to every inequality:
$$a_i^T x + s_1 = b_i, \quad -a_i^T x + s_2 = -b_i \implies s_1 + s_2 = 0$$
Because the barrier enforces $s_1 > 0$ and $s_2 > 0$, the sum $s_1 + s_2$ is strictly positive ($s_1 + s_2 > 0$). Consequently:
1. The relative interior of the artificial inequality formulation is mathematically empty.
2. The barrier forces $s_1, s_2 \to 0$, creating ill-conditioned barrier gradients and driving the step size $\alpha \to 0$.
3. On models with substantial equality constraints (such as `QPLIB_8845` with 490 equality rows out of 777), the solver inevitably stalled at `LIMIT_REACHED`.

### 2.2 The Native Equality Architecture
In Gate 7.2, equality constraints are handled natively:
- **Equalities ($E x = f$):** Retained directly without slacks and without barrier terms. Associated with free dual multipliers $y \in \mathbb{R}^{m_e}$ (no nonnegativity restriction).
- **Inequalities ($G x \le h$):** Introduced with barrier slacks $s \in \mathbb{R}^{m_i}, s > 0$, and constrained dual multipliers $z \in \mathbb{R}^{m_i}, z \ge 0$.

---

## 3. Perturbed KKT Conditions & Residuals

Introducing positive slacks $s > 0$ for inequalities, the Lagrangian is:
$$\mathcal{L}(x, y, z, s) = \frac{1}{2} x^T Q x + c^T x + y^T (E x - f) + z^T (G x + s - h) - \tau \sum_{i=1}^{m_i} \ln(s_i)$$

The perturbed Karush-Kuhn-Tucker (KKT) conditions at parameter $\tau = \sigma \mu$ are:
1. **Stationarity:**
   $$r_d = Q x + c + E^T y + G^T z = 0$$
2. **Equality Feasibility:**
   $$r_e = E x - f = 0$$
3. **Inequality Feasibility:**
   $$r_p = G x + s - h = 0$$
4. **Perturbed Complementarity:**
   $$r_c = S z - \sigma \mu \mathbf{1} = 0, \quad s > 0, \; z > 0$$

where $S = \text{diag}(s)$, $Z = \text{diag}(z)$, and the average complementarity gap is:
$$\mu = \frac{s^T z}{m_i}$$

---

## 4. Mehrotra Predictor-Corrector Newton System

### 4.1 Linearized KKT System
Taking differentials $(\Delta x, \Delta y, \Delta z, \Delta s)$:
$$\begin{aligned}
Q \Delta x + E^T \Delta y + G^T \Delta z &= -r_d \\
E \Delta x &= -r_e \\
G \Delta x + \Delta s &= -r_p \\
Z \Delta s + S \Delta z &= -r_c
\end{aligned}$$

### 4.2 Algebraic Block Elimination
From the complementarity equation:
$$\Delta z = -S^{-1} r_c - S^{-1} Z \Delta s$$
From the inequality feasibility equation:
$$\Delta s = -r_p - G \Delta x$$
Substituting $\Delta s$ into $\Delta z$:
$$\Delta z = -S^{-1} r_c - S^{-1} Z (-r_p - G \Delta x) = S^{-1} Z G \Delta x + S^{-1} Z r_p - S^{-1} r_c$$

Define the positive diagonal scaling matrix:
$$D = S^{-1} Z = \text{diag}(z_i / s_i) > 0$$
Then:
$$\Delta z = D G \Delta x + D r_p - S^{-1} r_c$$

Substitute $\Delta z$ into the stationarity equation:
$$Q \Delta x + E^T \Delta y + G^T (D G \Delta x + D r_p - S^{-1} r_c) = -r_d$$
$$(Q + G^T D G) \Delta x + E^T \Delta y = -r_d - G^T D r_p + G^T S^{-1} r_c$$

Let the condensed primal Hessian be:
$$H = Q + G^T D G \succeq 0$$
and the condensed primal right-hand side be:
$$\text{rhs}_x = -r_d + G^T (S^{-1} r_c - D r_p)$$

### 4.3 Reduced Augmented Saddle-Point System
We solve the reduced block saddle-point system of size $(n + m_e) \times (n + m_e)$:
$$\begin{bmatrix} H & E^T \\ E & 0 \end{bmatrix} \begin{bmatrix} \Delta x \\ \Delta y \end{bmatrix} = \begin{bmatrix} \text{rhs}_x \\ -r_e \end{bmatrix}$$

After obtaining $\Delta x$ and $\Delta y$, we directly recover:
$$\Delta s = -r_p - G \Delta x$$
$$\Delta z = -S^{-1} (r_c + Z \Delta s)$$

---

## 5. Mehrotra Predictor-Corrector Algorithm

1. **Affine Predictor Step ($\sigma = 0$):**
   - Set $r_c^{\text{aff}} = S z$.
   - Form $\text{rhs}_x^{\text{aff}} = -r_d + G^T (z - D r_p)$.
   - Solve saddle-point system for $\Delta x^{\text{aff}}, \Delta y^{\text{aff}}$.
   - Recover $\Delta s^{\text{aff}} = -r_p - G \Delta x^{\text{aff}}$ and $\Delta z^{\text{aff}} = -z - D \Delta s^{\text{aff}}$.
   - Compute maximal step lengths preserving $s > 0, z > 0$:
     $$\alpha_p^{\text{aff}} = \min \left( 1.0, \min_{i: \Delta s_i^{\text{aff}} < 0} \frac{-s_i}{\Delta s_i^{\text{aff}}} \right), \quad \alpha_d^{\text{aff}} = \min \left( 1.0, \min_{i: \Delta z_i^{\text{aff}} < 0} \frac{-z_i}{\Delta z_i^{\text{aff}}} \right)$$
   - Compute affine gap:
     $$\mu_{\text{aff}} = \frac{(s + \alpha_p^{\text{aff}} \Delta s^{\text{aff}})^T (z + \alpha_d^{\text{aff}} \Delta z^{\text{aff}})}{m_i}$$
   - Centering parameter:
     $$\sigma = \min \left( 1.0, \max \left( 0.0, \left(\frac{\mu_{\text{aff}}}{\mu}\right)^3 \right) \right)$$

2. **Combined Corrector Step:**
   - Set $r_c = S z + \Delta S^{\text{aff}} \Delta Z^{\text{aff}} \mathbf{1} - \sigma \mu \mathbf{1}$.
   - Form $\text{rhs}_x = -r_d + G^T (S^{-1} r_c - D r_p)$.
   - Solve saddle-point system for combined $\Delta x, \Delta y$.
   - Recover $\Delta s = -r_p - G \Delta x$ and $\Delta z = -S^{-1} (r_c + Z \Delta s)$.

3. **Step Length & Iterate Update (Fraction-to-Boundary $\eta = 0.995$):**
   $$\alpha_p = \min \left( 1.0, \eta \min_{i: \Delta s_i < 0} \frac{-s_i}{\Delta s_i} \right), \quad \alpha_d = \min \left( 1.0, \eta \min_{i: \Delta z_i < 0} \frac{-z_i}{\Delta z_i} \right)$$
   Update:
   $$x \leftarrow x + \alpha_p \Delta x, \quad s \leftarrow s + \alpha_p \Delta s$$
   $$y \leftarrow y + \alpha_d \Delta y, \quad z \leftarrow z + \alpha_d \Delta z$$

---

## 6. Initialization & Regularization

- **Primal-Dual Initial Point ($x_0, y_0$):** Computed via the regularized linear KKT system:
  $$\begin{bmatrix} Q + 10^{-4} \max(1, \|\text{diag}(Q)\|_\infty) I & E_s^T \\ E_s & -10^{-8} I \end{bmatrix} \begin{bmatrix} x_0 \\ y_0 \end{bmatrix} = \begin{bmatrix} -c \\ f_s \end{bmatrix}$$
  providing a stable starting point without requiring initial feasibility.
- **Slacks $s_0$:** $s_0 = \max(h_s - G_s x_0 + \max(0, -1.5 \min(h_s - G_s x_0)), 10.0) > 0$.
- **Inequality duals $z_0$:** Linear least-squares estimate $z_{\text{ls}} = (G_s^T)^\dagger (-Q x_0 - c - E_s^T y_0)$, then $z_0 = \max(z_{\text{ls}} + \max(0, -1.5 \min(z_{\text{ls}})), 10.0) > 0$.
- **Infeasible-start support:** Nonzero initial equality residual $r_e$ and inequality residual $r_p$ are reduced concurrently with duality gap.
- **Zero Reference Leakage:** 100% internal initialization (`initialization_source = 'SOVOPT_INTERNAL'`, `reference_solution_used_as_initialization = false`). No external .sol files are ever read by the solver.
- **Numerical Regularization & Iterative Refinement:**
  $$\begin{bmatrix} H + \delta_p I & E_s^T \\ E_s & -\delta_d I \end{bmatrix}$$
  where $\delta_p = 10^{-12} \max(1, \|\text{diag}(Q)\|_\infty)$ and $\delta_d = 10^{-12}$.
  One step of iterative refinement against the unregularized saddle-point operator cancels the $O(\delta)$ perturbation down to machine precision ($10^{-15}$).

---

## 7. Verification Invariant

Convergence is declared when scaled residuals satisfy:
$$\frac{\|r_e\|_\infty}{1 + \|f\|_\infty} \le \text{tol}, \quad \frac{\|r_p\|_\infty}{1 + \|h\|_\infty} \le \text{tol}, \quad \frac{\|r_d\|_\infty}{1 + \|c\|_\infty + \|Q x\|_\infty} \le \text{tol}, \quad \mu \le \text{tol}$$

Every candidate solution is independently verified on the original untransformed `Model` via `sovopt.verify.verify(model, x, duals)` before granting `OPTIMAL_VERIFIED`.
