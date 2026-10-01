# Architecture and Mathematical Specification — SOV-OPT

**MRPL SIH Problem Statement 26119**  
**Repository:** https://github.com/sg721642/sov-opt-mrpl-26119 (Private)  
**Solver Core Dependencies:** Python standard library and NumPy 2.3.5 only.

> *"GPU accelerates. CPU verifies. No result is trusted merely because an optimization algorithm stopped."*  
> *Core Engineering Philosophy: Correctness first. Robustness second. Performance third. Breadth fourth.*

SOV-OPT is an original numerical optimization research prototype developed for linear programming (LP), mixed-integer linear programming (MILP), and convex quadratic programming (QP). The solver core (`sovopt/`) is strictly sovereign: it imports only NumPy and the Python standard library. External solvers (HiGHS, SciPy) are permitted exclusively in isolated external validation worker processes (`scripts/baseline_worker.py`).

---

## 1. Module Structure and Boundaries

| Module | Purpose | Sovereign Dependencies |
|:---|:---|:---|
| `sovopt/model.py` | Canonical `Model` dataclass: $c$, $A$, row bounds, variable bounds, integer indices, names, objective offset, and maximization flag. Validates finite bounds and cryptographic model fingerprint. | `dataclasses`, `hashlib`, `json`, NumPy |
| `sovopt/simplex.py` | Two-phase primal revised simplex algorithm with dense LU factorization, Markowitz partial pivoting, iterative refinement, exact rational basis dual solver (`_exact_dual_from_basis`), and Phase I/II ray recovery (`postsolve_ray`). | NumPy, Python `fractions.Fraction` |
| `sovopt/milp.py` | Branch-and-bound mixed-integer linear programming (MILP). Best-bound search queue, most-fractional branching, exact rational Lagrangian lower bounding via `safe_lower_bound`, safe integer leaf fathoming, and exact Farkas infeasibility pruning. | `heapq`, `math`, NumPy, `fractions.Fraction` |
| `sovopt/qp.py` | Infeasible-start Mehrotra predictor-corrector primal-dual interior point solver for convex quadratic programs: $\min \frac{1}{2} x^T Q x + c^T x$ subject to $l \le A x \le u$. Floating-point eigenvalue inspection. | NumPy |
| `sovopt/pdhg.py` | Experimental first-order Primal-Dual Hybrid Gradient (PDHG / Chambolle-Pock) solver for continuous linear programs. Supports diagonal step sizes and periodic restart. Contains CPU SpMV and CUDA RawKernel source. | NumPy (CPU); optional CuPy (CUDA) |
| `sovopt/dispatcher.py` | Automatic algorithm dispatcher inspecting problem dimensions, integrality, quadratic terms, dynamic range, and sparsity to select solver methods and backends automatically. | NumPy, Python stdlib |
| `sovopt/refinery_twin.py` | Parameterised MRPL Refinery Planning Digital Twin supporting 4 operational variants (LP, MILP, QP, Infeasible) with physical stream limits and quality constraints. | NumPy, Python stdlib |
| `sovopt/transforms.py` | Canonical reversible variable transformations mapping free, box-bounded, upper-bounded, lower-bounded, and fixed variables to standard non-negative equality form. Exact primal and dual postsolve recovery. | NumPy |
| `sovopt/verify.py` | Independent mathematical verification suite. Evaluates primal constraint violations, stationarity, complementarity, duality gap, exact binary-rational Farkas certificates, and conservative rational Lagrangian lower bounds. | NumPy, `fractions.Fraction` |
| `sovopt/linalg.py` | Dense LU decomposition with partial row pivoting, forward/backward substitution, and residual-based iterative refinement. | NumPy |
| `sovopt/mps.py` | Parser for standard fixed-column and free MPS format files (LP/MILP) and QPS format files (convex QP with `QUADOBJ`). | Python standard library |
| `server.py` | Lightweight HTTP server providing web dashboard, dataset manifest, and solve API. Request isolation, timeout limits, and memory bounds. | Python `http.server`, `subprocess`, `json` |

---

## 2. Mathematical Formulations & Conventions

### 2.1 Canonical Linear Program (LP)
SOV-OPT models all linear optimization in the general bounded form:

$$\min_{x \in \mathbb{R}^n} c^T x + \text{offset}$$

subject to:

$$l_{\text{row}} \le A x \le u_{\text{row}}$$

$$l_{\text{var}} \le x \le u_{\text{var}}$$

- **Maximization:** Maximization models are transformed by setting $c_{\text{internal}} = -c_{\text{original}}$ upon entry. The returned objective is negated and offset-adjusted prior to verification.
- **Transformations:** All-fixed variables, free variables, and general box bounds are mapped by `sovopt/transforms.py` into non-negative standard form $A_{\text{std}} x_{\text{std}} = b_{\text{std}}, x_{\text{std}} \ge 0$. Dual multipliers on original row and bound constraints are recovered losslessly during postsolve.

### 2.2 Convex Quadratic Program (QP)
Convex quadratic programs minimize:

$$f(x) = \frac{1}{2} x^T Q x + c^T x + \text{offset}$$

subject to linear inequality and box constraints.
- $Q$ must be positive semi-definite ($Q \succeq 0$). The implementation checks positive semi-definiteness numerically via eigenvalue thresholding (minimum eigenvalue $\ge -10^{-10}$). This is a numerical floating-point check, not an exact rational certificate of convexity.

### 2.3 Mixed-Integer Linear Program (MILP)
MILP adds integrality constraints $x_j \in \mathbb{Z}$ for $j \in I \subseteq \{0, \dots, n-1\}$.
- **Lower Bounding:** On every branch node, SOV-OPT evaluates exact rational basis duals using `_exact_dual_from_basis` in exact arithmetic (`fractions.Fraction`). The Neumaier-Shcherbina Lagrangian bound:

$$\underline{b} = -h^T z + \sum_{j: r_j > 0} r_j l_j + \sum_{j: r_j < 0} r_j u_j$$

where $r = c + G^T z$, is evaluated exactly. It yields provably valid lower bounds that never exceed the optimal integer objective.
- **Infeasibility Pruning:** Infeasible branch nodes are certified using exact rational Farkas certificates ($G^T z = 0, h^T z < 0, z \ge 0$).
- **Integer Leaf Fathoming:** When a node produces an integer-feasible point verified against original model constraints, it updates the incumbent and fathoms the branch conservatively.

### 2.4 MRPL Refinery Planning Digital Twin Formulation
The refinery twin (`sovopt/refinery_twin.py`) models operations over $T \ge 1$ planning periods:
- **Atmospheric & Vacuum Distillation:** Blending Arab Light ($c_0$, \$70/bbl) and Basrah ($c_1$, \$62/bbl) crudes through Crude Distillation Unit (CDU, 100 kbpd limit) producing Naphtha, Distillate, and Atmospheric Residue.
- **Secondary Conversion:** Fluid Catalytic Cracker (FCC, 50 kbpd limit) and Continuous Catalytic Reformer (CCR, 30 kbpd limit) upgrading heavy and light intermediates.
- **Finished Product Blending:**
  - BS-VI Gasoline: Research Octane Number (RON) $\ge 93$, with octane blending constraints ($98 b_{\text{ref}} + 92 b_{\text{cat}} \ge 93 s_{\text{gas}}$).
  - Euro-VI Diesel: Cetane Index $\ge 48$, with cetane blending constraints ($52 b_{\text{dist}} + 42 b_{\text{lco}} \ge 48 s_{\text{dsl}}$).
  - Fuel Oil: Heavy residue balance.
- **Storage Tankage & Inventory:** Inter-period balances $inv_{k,t} = inv_{k,t-1} + \text{yield}_{k,t} - \text{feed}_{k,t}$ with physical capacity limits ($0 \le inv_k \le 25$ kbbl).
- **Four Distinct Operational Variants:**
  1. `lp`: Continuous multi-period economic planning.
  2. `milp`: Discrete operational unit commitment binaries ($z \in \{0, 1\}$) and minimum turndown operating throughputs.
  3. `qp`: Smooth operational dispatch with positive semidefinite quadratic penalties damping throughput swings ($\frac{1}{2} \lambda_2 \sum (f_{u,t} - f_{u,t-1})^2$) to prevent thermal cycling.
  4. `infeasible`: Diagnostic scenario with demand exceeding physical refinery throughput capacity, generating an exact Farkas certificate.

### 2.5 Automatic Algorithm Dispatcher
The dispatcher (`sovopt/dispatcher.py`) analyzes model characteristics:
- If $Q \neq 0$: routes to Primal-Dual IPM for Convex QP (`ipm`).
- If $|I| > 0$: routes to exact rational Branch-and-Bound (`bb`).
- Continuous LP: defaults to dense Primal Simplex with LU refactorization (`simplex`) on CPU, or routes to PDHG if `--backend pdhg-cpu` / `pdhg-cuda` is requested.
- Inspects variables $n$, constraints $m$, nonzeros $nnz$, density, integrality, and dynamic range $\kappa_{\text{dyn}} = \max(|c|, |A|) / \min_{>0}(|c|, |A|)$.

---

## 3. Verification & Trust Semantics

Every solve is evaluated by `sovopt/verify.py` against the **original, untransformed model**:

- **`OPTIMAL_VERIFIED`**: 
  - For LP and QP: Continuous Karush-Kuhn-Tucker (KKT) conditions are satisfied within numerical tolerance ($10^{-7}$). Primal feasibility residual $\le 10^{-7}$, dual stationarity residual $\le 10^{-7}$, and complementarity $\le 10^{-7}$. This is a numerical floating-point tolerance check, not a formal rational proof of optimality.
  - For MILP: The branch-and-bound search tree closed with relative gap $\le 10^{-6}$ between a numerically verified feasible integer incumbent and the conservative rational lower bound.
- **`INFEASIBLE_CERTIFIED`**: An exact binary-rational Farkas vector $z \ge 0$ was verified in exact rational arithmetic: $G^T z = 0$ and $h^T z < 0$.
- **`UNBOUNDED_CERTIFIED`**: A feasible base point and an extreme ray of unbounded descent $d$ were verified: $c^T d < 0$ with $A d \ge 0$ (or within recession cone).
- **`LIMIT_REACHED`**: Computation reached iteration or node budget (e.g. 50 nodes in FLUGPL). A conservative rational lower bound is preserved; no incumbent was found or the search tree remains open.
- **`NUMERICAL_FAILURE`**: Iterative refinement failed, factorization encountered numerical singularity, or KKT residuals exceeded tolerance.
- **`INVALID_MODEL`**: Input validation rejected the model (e.g., mismatched dimensions, infinite bounds with wrong sign, non-unique variable names).

---

## 4. Roadmap Implementation Gates

| Gate | Description | Implemented Status | Evidence / Verification |
|:---|:---|:---:|:---|
| **Gate 0** | Reproducible baseline & sovereign boundary | **COMPLETED** | Pure NumPy core; no external optimizer imports in `sovopt/`. Initial baseline committed in git history. |
| **Gate 1** | Mathematical coverage & transformations | **COMPLETED** | Maximization, objective offsets, free variables, box bounds, one-sided bounds, `QUADOBJ` in QPS. Tested via affine transformation recovery to machine precision ($10^{-16}$). |
| **Gate 2** | Sparse numerical linear algebra | *PLANNED* | Dense LU decomposition with partial pivoting and iterative refinement is implemented. Size limits: 250 variables / 1000 rows (CLI), 100 variables / 150 rows (web). Sparse LU (Markowitz) deferred to compiled core. |
| **Gate 3** | Robust dual simplex | *PLANNED* | Current LP solver is two-phase primal revised simplex. Re-optimization in B&B uses cold starts. |
| **Gate 4** | Reversible presolve & scaling | **PARTIAL** | Reversible variable transformations (`sovopt/transforms.py`) and geometric row scaling implemented with exact primal/dual postsolve. Full bound tightening and singleton row elimination planned. |
| **Gate 5** | Conservative MILP bounds | **COMPLETED** | Exact rational basis dual engine (`_exact_dual_from_basis`), exact rational Farkas certificates, and safe leaf node fathoming. Validated on MIPLIB FLUGPL and MRPL Twin MILP. |
| **Gate 6** | Convex QP hardening | **COMPLETED** | Mehrotra predictor-corrector interior point method implemented and KKT verified on authentic and MRPL operational QP twin models. |
| **Gate 7** | GPU acceleration validation | *UNAVAILABLE ON MAC* | CUDA RawKernel source included in `sovopt/pdhg.py`. Apple Silicon hardware lacks NVIDIA CUDA. `gpu_executed` is strictly `false` on all CPU runs; no GPU speedup is claimed without physical NVIDIA hardware. |
| **Gate 8** | Validated cutting planes | *PLANNED* | Gomory mixed-integer (GMI) and mixed-integer rounding (MIR) cuts planned for future release. |

---

## 5. Non-Linear Progression Roadmap

Real refining applications contain non-linear operational dynamics:
$$\text{LP} \longrightarrow \text{MILP} \longrightarrow \text{QP} \longrightarrow \text{Bilinear Pooling} \longrightarrow \text{SLP / Convex Relaxation} \longrightarrow \text{NLP} \longrightarrow \text{MINLP}$$

1. **LP / MILP / QP Foundation (Delivered):** Verified core with exact certificates.
2. **Bilinear Pooling (Next Phase):** Crude component concentration mixing ($z_{j} = \sum x_i c_{i,j}$) modeled via McCormick convex envelopes and piecewise-linear relaxations.
3. **Successive Linear Programming (SLP):** Trust-region linearized approximations of non-linear yields and octane blending equations with independent KKT residual verification.

---

## 6. Hardware Boundaries & Execution Environment

- **Development Platform:** macOS Apple Silicon (ARM64), Python 3.11.16, NumPy 2.3.5.
- **CUDA Device Requirement:** The `pdhg-cuda` backend requires an NVIDIA GPU, Linux or Windows with NVIDIA CUDA Toolkit, and `cupy`. On Apple Silicon or machines without CUDA, solver dispatches to CPU and records `gpu_executed: false`.
- **External Validation Process:** Native HiGHS (C++) and SciPy run strictly in subprocess workers (`scripts/baseline_worker.py`) via a separate benchmark virtual environment (`.venv-benchmark`). They are never imported by `sovopt` or `server.py`.
