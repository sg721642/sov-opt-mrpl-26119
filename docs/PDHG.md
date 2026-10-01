# Restarted Preconditioned Primal-Dual Hybrid Gradient (PDHG) Specification

## 1. Problem Formulation

SOV-OPT implements a sovereign first-order primal-dual hybrid gradient (PDHG / Chambolle-Pock) solver for continuous linear programs. The standard form continuous LP is formulated as:

$$\min_{x \in \mathbb{R}^n} c^T x \quad \text{subject to} \quad G x \le h, \quad l \le x \le u$$

where:
- $c \in \mathbb{R}^n$ is the objective cost vector.
- $G \in \mathbb{R}^{m \times n}$ is the inequality constraint matrix (derived from row constraints $row\_lower \le A x \le row\_upper$).
- $h \in \mathbb{R}^m$ is the right-hand side bound vector.
- $l \in [-\infty, \infty)^n$ and $u \in (-\infty, \infty]^n$ are lower and upper variable bounds.

The Lagrangian saddle-point problem is:
$$\min_{x \in [l, u]} \max_{y \ge 0} \mathcal{L}(x, y) = c^T x + y^T (G x - h)$$

The dual problem is:
$$\max_{y \ge 0, z_l \ge 0, z_u \ge 0} -h^T y + l^T z_l - u^T z_u \quad \text{subject to} \quad c + G^T y - z_l + z_u = 0$$

where $z_l \ge 0, z_u \ge 0$ are reduced cost multipliers for variable lower and upper bounds.

---

## 2. Chambolle-Pock Algorithm with Extrapolation

At iteration $k$, given primal iterate $x^{(k)}$, dual iterate $y^{(k)}$, and extrapolated primal point $\bar{x}^{(k)}$, the updates proceed as:

1. **Dual Update (Proximal step on $y$):**
   $$y^{(k+1)} = \max\left(0, y^{(k)} + \Sigma (G \bar{x}^{(k)} - h)\right)$$
   where $\Sigma = \text{diag}(\sigma_1, \dots, \sigma_m)$ is the diagonal dual step-size matrix.

2. **Primal Update (Proximal step on $x$ with box projection):**
   $$x^{(k+1)} = \text{proj}_{[l, u]}\left(x^{(k)} - T (c + G^T y^{(k+1)})\right)$$
   where $T = \text{diag}(\tau_1, \dots, \tau_n)$ is the diagonal primal step-size matrix, and:
   $$\text{proj}_{[l, u]}(v)_j = \min(u_j, \max(l_j, v_j))$$

3. **Primal Extrapolation:**
   $$\bar{x}^{(k+1)} = 2 x^{(k+1)} - x^{(k)}$$

---

## 3. Diagonal Preconditioning (Pock-Chambolle)

Standard fixed scalar step sizes $\tau, \sigma$ suffer from ill-conditioning when row or column norms of $G$ vary by orders of magnitude. SOV-OPT implements Pock-Chambolle $\ell_1$-norm diagonal preconditioning:

$$\tau_j = \frac{\gamma}{\max\left(\sum_{i=1}^m |G_{ij}|, 1.0\right)}, \quad \forall j = 1, \dots, n$$
$$\sigma_i = \frac{\gamma}{\max\left(\sum_{j=1}^n |G_{ij}|, 1.0\right)}, \quad \forall i = 1, \dots, m$$

where $\gamma \in (0, 1)$ is a safety damping factor (default $\gamma = 0.99$).

### Convergence Condition
By the Pock-Chambolle theorem, convergence of the saddle-point operator is guaranteed if:
$$\tau_j \sigma_i \left(\sum_{k=1}^m |G_{kj}|\right) \left(\sum_{l=1}^n |G_{il}|\right) < 1$$
which is satisfied identically when $\gamma < 1$.

In unscaled ablation mode (`scaling=False`), a single uniform bound is used:
$$B = \max\left(1.0, \sqrt{\max_j \sum_i |G_{ij}| \cdot \max_i \sum_j |G_{ij}|}\right)$$
$$\tau_j = \frac{\gamma}{B}, \quad \sigma_i = \frac{\gamma}{B}$$

---

## 4. Ergodic Averaging and Deterministic Restarts

### Running Ergodic Averages
The raw iterates $(x^{(k)}, y^{(k)})$ can oscillate around the optimal saddle point. Convergence of the primal-dual gap is established for the running ergodic sequence:
$$\bar{x}_{\text{avg}}^{(K)} = \frac{1}{K} \sum_{k=1}^K x^{(k)}, \quad \bar{y}_{\text{avg}}^{(K)} = \frac{1}{K} \sum_{k=1}^K y^{(k)}$$

Computed online via Welford-style incremental updates:
$$\bar{x}_{\text{avg}}^{(k)} = \bar{x}_{\text{avg}}^{(k-1)} + \frac{x^{(k)} - \bar{x}_{\text{avg}}^{(k-1)}}{k}$$

### Deterministic Periodic Restart
Every $K_{\text{restart}}$ iterations (default $K_{\text{restart}} = 1000$):
1. The current iterate is reset to the ergodic average:
   $$x \leftarrow \bar{x}_{\text{avg}}, \quad y \leftarrow \bar{y}_{\text{avg}}, \quad \bar{x} \leftarrow x$$
2. The ergodic accumulation counter is reset ($k \leftarrow 0$).
3. The running averages are re-initialized to $(x, y)$.

### Restart Ablation Mode
When `restart=False` or `restart=0` or `restart=None`, the periodic reset is deactivated and the ergodic average accumulates continuously over all iterations $k = 1, \dots, K_{\max}$.

---

## 5. Residuals, Stopping Criteria, and CPU Verification

### Residual Definitions
At evaluation checkpoints (every 100 iterations and at termination):

1. **Primal Infeasibility Residual:**
   $$r_p = \max_{i} \max(0, (G x)_i - h_i)$$
   plus boundary check $\max_j \max(0, l_j - x_j, x_j - u_j)$.
   Normalized primal residual:
   $$\tilde{r}_p = \frac{r_p}{\max(1.0, \|h\|_\infty)}$$

2. **Dual Infeasibility Residual:**
   Let $g = c + G^T y$. The dual bound multipliers are extracted:
   $$z_{u, j} = \max(0, -g_j) \quad \text{if } |x_j - u_j| \le \text{tol}$$
   $$z_{l, j} = \max(0, g_j) \quad \text{if } |x_j - l_j| \le \text{tol}$$
   $$r_d = \|c + G^T y - z_l + z_u\|_\infty$$
   Normalized dual residual:
   $$\tilde{r}_d = \frac{r_d}{\max(1.0, \|c\|_\infty)}$$

3. **Relative Duality Gap:**
   $$\Delta_{\text{rel}} = \frac{|c^T x - (-h^T y + l^T z_l - u^T z_u)|}{\max(1.0, |c^T x|, |-h^T y + l^T z_l - u^T z_u|)}$$

### Sovereign CPU Verification Rule
**GPU accelerates; CPU verifies.**
Regardless of whether iterations were computed on `pdhg-cpu` or `pdhg-cuda`:
1. Candidate solution vectors $(x, y, z)$ are transferred to CPU NumPy arrays.
2. The sovereign verification routine `sovopt.verify.verify(model, x, dual, tol)` executes entirely on CPU using exact IEEE 754 arithmetic.
3. Only if `verify` certifies primal feasibility, dual feasibility, and complementarity slackness within tolerance `tol` is the status reported as `OPTIMAL_VERIFIED`.

---

## 6. Architecture and Backend Separation

### Backend Identifiers
- `pdhg-cpu`: Pure NumPy implementation using sovereign CSR SpMV on CPU.
- `pdhg-cuda`: NVIDIA CUDA execution via CuPy runtime and custom SpMV raw kernel.

### Truthful Non-CUDA Execution
On Apple Silicon or systems without NVIDIA hardware:
- Explicitly requesting `backend='pdhg-cuda'` returns status `CUDA_UNAVAILABLE` with `gpu_executed=False`.
- Automatic dispatch (`backend='auto'`) detects CUDA absence and falls back to `pdhg-cpu` with:
  `requested_backend='auto'`, `executed_backend='pdhg-cpu'`, `gpu_executed=False`, `fallback_reason='CUDA_UNAVAILABLE'`.
- Zero synthetic or simulated GPU results are permitted.

---

## 7. Problem Size Stratification for Benchmarking

Public continuous LP instances in `data/manifests/gpu_pdhg_lp.json` are partitioned into three pre-declared size strata:

| Stratum | Selection Rule | Representative Netlib Instances |
| :--- | :--- | :--- |
| **SMALL** | $n + m < 200, nnz < 1000$ | `AFIRO`, `KB2`, `SC50A`, `SC50B`, `ADLITTLE`, `BLEND` |
| **MEDIUM** | $200 \le n + m \le 600, 1000 \le nnz \le 5000$ | `SC105`, `STOCFOR1`, `SCAGR7`, `RECIPE`, `ISRAEL`, `SC205`, `SHARE1B`, `BRANDY` |
| **LARGE** | $n + m > 600 \text{ and } nnz > 5000$ | `GROW15`, `GROW22`, `SCFXM2`, `SCTAP2` |
