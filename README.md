# SOV-OPT

**Sovereign Numerical Optimization Core**

Smart India Hackathon 2026 · Problem Statement MRPL PS 26119<br>
Team VarunNetra · Team ID 177365 · Rajiv Gandhi Institute of Petroleum Technology (RGIPT)<br>
**Release:** `SOV-OPT v0.3.2` · **Core Freeze Commit:** `17e46f2`<br>
**Live Cloud Portal:** [https://sov-opt-mrpl-26119.onrender.com](https://sov-opt-mrpl-26119.onrender.com) (CPU-only cloud instance)<br>
**Repository:** [https://github.com/sg721642/sov-opt-mrpl-26119](https://github.com/sg721642/sov-opt-mrpl-26119)

---

## ⚡ 30-Second Judge Executive Summary

1. **What is SOV-OPT?**
   SOV-OPT is an indigenous, dependency-free mathematical optimization core built from first principles in pure Python and NumPy (`numpy==2.3.5`). It contains **zero third-party solver dependencies or wrappers** (no HiGHS, SCIP, CBC, PuLP, CVXPY, Gurobi, or CPLEX inside the core).

2. **Why MRPL Needs It**
   Designed to **reduce dependency on proprietary commercial solvers** for refinery production planning, blending, and conversion scheduling, delivering complete source-code auditability, transparent mathematical provenance, and verifiable computational trust.

3. **Sovereignty Boundary & Verification Guarantee**
   The core solver (`sovopt/`) is strictly sovereign. An **independent Numerical Trust Layer** re-evaluates Karush-Kuhn-Tucker (KKT) residuals, complementary slackness, integer tolerances, and certificate rays directly on unscaled original equations before any result is accepted as `OPTIMAL_VERIFIED`.

4. **Core Capabilities**
   - **Continuous LP:** Revised primal simplex and bounded-variable dual simplex with threshold Markowitz sparse LU ($u=0.1$) and PFI eta updates; first-order restarted PDHG.
   - **MILP:** Branch-and-bound with pseudocost branching, dual warm starts, safe primal heuristics (rounding and root diving), and **validated binary cover cuts** (40–54.5% node reduction on knapsack/oracle benchmarks).
   - **Intra-Solve Parallel B&B:** Genuine multi-process tree search with shared incumbent and bound synchronization (**1.94× speedup on 2 workers with 97.0% parallel efficiency** on identical 287-node search).
   - **Convex QP:** Infeasible-start Mehrotra predictor-corrector primal-dual interior point method with exact Lagrangian KKT verification.
   - **GPU Acceleration:** Restarted Primal-Dual Hybrid Gradient (PDHG) implemented via custom CUDA C++ `RawKernel` SpMV routines (**5.81× end-to-end acceleration** over CPU on 10K true-sparse workload on physical RTX 5050).
   - **Diagnostic Infeasibility:** Exact rational Farkas ray certificates ($\mathbb{Q}$) and Farkas Lens diagnostic ranking (*diagnostic ranking, not a minimal IIS*).

5. **Verified Evidence Summary**
   - **Netlib LP:** 17 authentic instances solved and KKT verified; differentially compared against HiGHS 1.15.1.
   - **MIPLIB 2017:** 38 authentic instances evaluated under honest bounded budgets (`LIMIT_REACHED` reported without false claims); up to 39× fixed-budget node progress with 4 parallel workers.
   - **QPLIB 2018:** 4 authentic convex QP instances evaluated and KKT verified.
   - **Hans Mittelmann LP:** 4 authentic instances acquired (`qap15`, `brazil3`, `chromaticindex1024-7`, `supportcase10`); on the physical RTX 5050 CUDA backend, SOV-OPT reached `OPTIMAL_VERIFIED` for the authentic Mittelmann `chromaticindex1024-7` instance in the recorded 80.21 s run, with the returned solution passing the project's numerical KKT verification.
   - **Physical GPU:** 5.81× end-to-end acceleration on 10K true-sparse PDHG on physical NVIDIA RTX 5050 Laptop GPU; 448.3× steady-state compute-loop ratio (secondary microbenchmark metric).
   - **Scale Stress Validation:** 1M-variable $\times$ 500K-row true-sparse GPU representation and SpMV were validated on the physical RTX 5050 (1,000,000 variables $\times$ 500,000 rows $\times$ 2,999,993 nonzeros; GPU upload ~108.0 ms, SpMV median ~0.178 ms, transpose SpMV median ~0.199 ms across 5 timed repetitions; representation stress test, not an optimization solve). Earlier Gate 20A CPU sparse representation stress test evaluated 2,500,000 nonzeros. Architectural guard rail at 10M variables.

6. **How to Run & Verify**
   ```bash
   # 1. Run full 368-test automated regression suite (357 passed, 11 skipped)
   .venv/bin/python -m unittest discover -s tests -v

   # 2. Verify repository cryptographic integrity ledger (SHA-256)
   .venv/bin/python scripts/verify_checksums.py

   # 3. Launch local interactive workstation
   python server.py --host 127.0.0.1 --port 8000
   ```

7. **External Solver Baseline Policy**
   External solvers (HiGHS 1.15.1, SciPy) are used exclusively in isolated subprocess worker scripts (`scripts/baseline_worker.py`) for differential benchmarking. Every result, including baseline speed advantages and timeout/limit cases, is published transparently without cherry-picking.

---

## What SOV-OPT Does

SOV-OPT provides an indigenous, dependency-free mathematical programming engine implementing:

- Continuous Linear Programming (revised primal simplex, bounded-variable revised dual simplex, and first-order PDHG).
- Mixed-Integer Linear Programming (serial branch-and-bound with warm-started dual simplex reoptimization and pseudocost branching).
- Convex Quadratic Programming (equality-aware infeasible-start primal-dual interior-point method).
- Optional GPU-accelerated first-order LP solving via restarted Primal-Dual Hybrid Gradient (PDHG).
- Automatic solver dispatch with scale-aware model inspection.
- Reversible presolve and Ruiz equilibration matrix scaling.
- An independent Numerical Trust Layer validating solutions against original unscaled models.
- Exact-rational Farkas certificates for certified infeasibility diagnosis where supported.
- Conservative MILP dual bounds evaluated in exact rational arithmetic ($\mathbb{Q}$).
- Deterministic SHA-256 model fingerprinting and exportable Trust Passports.

> **Core Philosophy:** *GPU accelerates. CPU verifies. No result is trusted merely because an optimization algorithm stopped.*

*Note on verification scope:* For continuous LP and QP models, verification denotes rigorous numerical Karush-Kuhn-Tucker (KKT) residual verification evaluated within double/extended precision tolerance, rather than formal computer-algebra interval proofs.

---

## Problem Context

Smart India Hackathon Problem Statement 26119 (Ministry of Petroleum and Natural Gas / MRPL) concerns an indigenous GPU-accelerated numerical optimization solver as a sovereign alternative for mission-critical industrial planning and scheduling.

Refinery production planning involves complex operational decisions:
- Crude oil selection and multi-component feedstock evaluation.
- Process unit capacity limits (Atmospheric Distillation, Fluid Catalytic Cracking, Catalytic Reforming).
- Quality specification and component blending constraints (RON, cetane, sulfur, Reid vapor pressure).
- Fluctuating commercial product demand targets and finished fuel shipments.

SOV-OPT demonstrates these capabilities on a parameterised digital twin based on representative open-literature refinery planning formulations (Gary & Handwerk; Meyers). The repository does not claim proprietary MRPL refinery operating data.

---

## Architecture

The SOV-OPT execution pipeline cleanly decouples acceleration from verification:

```text
Model Input (MPS / JSON / QPLIB)
       │
       ▼
Presolve & Scaling (Reversible bound tightening & equilibration)
       │
       ▼
Problem Classification & Dispatch (Integrality, quadratic terms, sparsity)
       │
       ▼
Solver Engine Execution
 ├─ LP: Revised Primal Simplex / Bounded Dual Simplex
 ├─ MILP: Branch-and-Bound (Warm-started Dual Simplex)
 ├─ Convex QP: Primal-Dual Interior-Point Method (Mehrotra)
 └─ GPU LP: Restarted PDHG (CuPy / RawKernel)
       │
       ▼
Original-Model Postsolve & Reconstruction
       │
       ▼
Numerical Trust Layer (KKT residuals, rational Farkas rays, safe bounds)
       │
       ▼
Trust Passport & Telemetry Output
```

1. **Model Ingestion:** Parsed into canonical bounded form ($c, A, l_{\text{row}}, u_{\text{row}}, l_{\text{var}}, u_{\text{var}}, Q, \text{integers}$).
2. **Presolve & Scaling:** Bounded reversible reductions tighten ranges without changing the optimum.
3. **Dispatch:** Analyzes dimensions, density, curvature, and variable types to select the optimal algorithm.
4. **Solver Core:** Solves the transformed system using sovereign numerical routines.
5. **Postsolve:** Losslessly recovers primal and dual multipliers on original coordinates.
6. **Numerical Trust Layer:** Evaluates constraint residuals independently of internal stopping conditions.
7. **Trust Passport:** Emits an exportable, reproducible audit bundle.

---

## Solver Components

| Problem Class | Core Method | Linear Algebra Backend | Verification Method |
| :--- | :--- | :--- | :--- |
| **Linear Program (LP)** | Revised Primal Simplex / Bounded-Variable Dual Simplex (Devex pricing, Harris ratio test) | Sovereign Sparse CSR/CSC LU (Threshold Markowitz $u=0.1$, PFI eta updates) & Dense LU | Original-model KKT residuals ($r_p, r_d, \text{comp} \le 10^{-7}$) & exact basis duals |
| **Mixed-Integer LP (MILP)** | Branch-and-Bound with pseudocosts, dual warm starts, validated binary cover cuts, safe primal heuristics, & intra-solve parallel search | Sovereign Sparse CSR/CSC & Dense LU | Integer residual verification ($\le 10^{-6}$) & exact rational lower bound ($\mathbb{Q}$) |
| **Convex Quadratic (QP)** | Infeasible-start Mehrotra predictor-corrector Primal-Dual Interior-Point Method | Dense normal equations factorization ($LDL^T$ / LU) | Equality-aware KKT stationarity, primal/dual residuals, & eigenvalue check |
| **First-Order LP (GPU/CPU)** | Restarted Primal-Dual Hybrid Gradient (PDHG / Chambolle-Pock) with $\ell_1$ preconditioning | Custom CUDA C++ `RawKernel` SpMV (GPU, 5.81× on 10K true-sparse LP) / Sovereign `CSRMatrix` (CPU) | Independent CPU simplex basis reconstruction & original-model KKT audit |

---

## Numerical Trust Layer

Optimization solvers can terminate prematurely due to stagnation, stalling, or loose internal tolerances. SOV-OPT enforces an independent trust evaluation on unscaled original equations:

- **Primal Feasibility:** Evaluates maximum absolute and relative violations across all row constraints and variable bounds.
- **Dual Feasibility & Stationarity:** Measures gradient residuals ($c + Qx - A^T y - z = 0$) and multiplier signs ($y \ge 0$ for $\le$ inequalities, $z \ge 0$ for lower bounds).
- **Complementary Slackness:** Verifies orthogonality between slack variables and dual multipliers.
- **Integrality Audit:** Enforces strict integer tolerances ($\max |x_j - \lfloor x_j \rceil| \le 10^{-6}$) on all discrete indices.
- **Farkas Infeasibility Rays:** Emits certified certificates $y^T A = 0$ with $y^T b > 0$ represented in exact rational arithmetic ($\mathbb{Q}$).
- **Unbounded Recession Rays:** Verifies feasible base point $x_0$ and direction $d$ satisfying $A d \le 0, d \ge 0, c^T d < 0$.
- **Safe Rational MILP Bounds:** Computes provable dual lower bounds via Neumaier-Shcherbina Lagrangian verification in exact rational arithmetic.
- **Farkas Lens Diagnostic:** Identifies and ranks constraint contributions to infeasibility. *Note:* The Farkas Lens provides an analytical diagnostic ranking; it is not a minimal Irreducible Infeasible Subsystem (IIS).

---

## Trust Passport

Every live optimization run produces an auditable **Trust Passport** payload that captures solver provenance without exposing proprietary intellectual property:

- `schema_version`: Trust Passport schema definition (`1.0.0`).
- `model_sha256`: Cryptographic SHA-256 fingerprint computed from canonical model matrices.
- `solver_version` & `solver_commit`: Package version and exact Git commit SHA.
- `algorithm` & `backend`: Executed algorithm and compute target (`cpu`, `pdhg-cpu`, `pdhg-cuda`).
- `input_snapshot`: Verifiable snapshot of operator parameters.
- `status`: Definitive solver termination state.
- `objective`: Evaluated optimal objective in original problem sense.
- `verified`: Boolean certifying independent KKT or certificate validation.
- `verification_precision`: Precision format utilized (`IEEE_754_double`, `exact_rational_Q`, `longdouble_extended`).
- `primal_residual`, `dual_residual`, `kkt_residual`: Evaluated unscaled residuals.
- `certificate_type` & `certificate_verified`: Infeasibility or unboundedness certificate telemetry.

> **Integrity Notice:** *The SHA-256 model fingerprint is an integrity identifier; the Trust Passport is not a digital signature.*

---

## Web Portal

The interactive web portal (`web/`) delivers a production-grade operational workstation inspired by MRPL institutional design standards:

- **Refinery Overview & PFD:** Interactive Process Flow Diagram with dynamic stream inspection, flow balances, and unit shadow prices.
- **Optimization Console:** Real-time parameter dispatch, crude slate selection, and live solve telemetry.
- **Scenario Comparison:** Side-by-side economic netback, yield distribution, and production comparisons across 6 industrial scenarios.
- **Solver Analytics:** Convergence logs, iteration counts, matrix statistics, and KKT residual monitors.
- **Trust & Verification:** Live inspection of the Numerical Trust Layer, Farkas Lens rankings, and Trust Passport JSON export.
- **Public Benchmarks & Evidence:** Pre-loaded authentic Netlib, MIPLIB, and QPLIB test cases with differential verification tables.
- **Audit & Export:** One-click JSON audit bundle and CSV production schedule exports.
- **Institutional Identity:** Team VarunNetra roster, technical background, and RGIPT institutional credentials.
- **Bilingual Interface:** Full English/Hindi UI toggle with persistent preference and accessible contrast.
- **Responsive Layout:** Adaptive desktop and mobile navigation rail.

---

## Representative Refinery Planning Demo

The built-in digital twin simulates an integrated hydroskimming/reforming/cracking refinery:
- **Feeds:** Arab Light and Basrah Heavy crude slates with distinct distillation cut yields and pricing.
- **Processing Units:** Atmospheric Distillation Unit (CDU), Fluid Catalytic Cracker (FCC), and Catalytic Reformer.
- **Finished Products:** High-octane Gasoline, Ultra-Low Sulfur Diesel, and Heavy Fuel Oil.
- **Problem Variations:**
  - `refinery-lp`: Continuous linear throughput optimization.
  - `refinery-milp`: Discrete FCC unit on/off commitment and startup cost modeling.
  - `refinery-qp`: Nonlinear catalytic cracking yield trade-offs and quality penalty curves.
  - `refinery-infeasible`: Demand commitments exceeding total CDU hydraulic capacity.

> **Dataset & Model Disclosure:** *Demonstration model — representative open-literature refinery data (Gary & Handwerk; Meyers); not actual MRPL operational data. All units, yields and economics are representative engineering approximations. Numerically verified for the evaluated prototype model.*

---

## CPU and GPU Execution

- **CPU Path (Default):** Pure Python and standard NumPy. Requires no GPU hardware, compilers, or binary extensions. Runs identically across Linux, macOS, and Windows.
- **GPU Path (Restarted PDHG):** Utilizes NVIDIA CUDA via CuPy device arrays and custom C++ `RawKernel` SpMV routines. Supported on NVIDIA hardware with compute capability $\ge 7.0$.
- **Render Production Service:** The live deployment runs in a standard cloud container utilizing the sovereign CPU engine (**CPU-only; no GPU in cloud container**).
- **Hardware Isolation:** On systems lacking CUDA support (such as Apple Silicon or CPU cloud nodes), requests for CUDA execution truthfully return `status="CUDA_UNAVAILABLE"` with `gpu_executed=false`.

---

## Physical GPU Validation

Physical CUDA validation was conducted on a dedicated Acer Laptop equipped with an **NVIDIA GeForce RTX 5050 Laptop GPU** (8 GB VRAM, Driver 572.16, CUDA 12.8, Compute Capability 12.0) running Linux x86_64:

- **Gate 20B True-Sparse PDHG Acceleration (Primary Result):** On a 10,000-variable true-sparse LP workload (`sparse_10k`), both CPU and CUDA backends executed 3,000 iterations from the same random seed, converging to the identical objective ($-20950.957738171615$). The GPU completed in 9.95s compared to 57.75s on CPU, demonstrating an authentic **5.81× end-to-end acceleration**.
- **Steady-State Compute-Loop Ratio (Secondary Metric):** Under a dedicated microbenchmark measuring raw inner-loop SpMV and vector arithmetic without host-to-device transfers, a 448.3× compute-loop ratio was observed. *Engineering note: This is strictly a steady-state loop ratio, NOT an end-to-end solve speedup.*
- **Scale Stress Validation:** 1M-variable $\times$ 500K-row true-sparse GPU representation and SpMV were validated on the physical RTX 5050 (1,000,000 variables $\times$ 500,000 rows $\times$ 2,999,993 nonzeros; GPU upload ~108.0 ms, SpMV median ~0.178 ms, transpose SpMV median ~0.199 ms across 5 timed repetitions; representation stress test, not an optimization solve. Earlier Gate 20A CPU sparse representation stress test evaluated 2,500,000 nonzeros).
- **Authentic Mittelmann Instance:** On the physical RTX 5050 CUDA backend, SOV-OPT reached `OPTIMAL_VERIFIED` for the authentic Mittelmann `chromaticindex1024-7` instance in the recorded 80.21 s run, with the returned solution passing the project's numerical KKT verification.
- **Historical Gate 9 Netlib Baseline:** Preserved separately (1.07× same-machine aggregate CPU/CUDA ratio across 18 Netlib instances; 1.81× internal CUDA optimization factor).
- **Render Cloud Disclaimer:** The public Render cloud deployment runs strictly on CPU. GPU results shown here derive from physical hardware runs on the lab Acer RTX 5050 machine.

Full raw execution logs, profiler telemetry, and verification manifests are preserved under [`reports/gpu_sparse_gate20b/`](reports/gpu_sparse_gate20b/) and [`reports/gpu_gate9_final_51b71bb/`](reports/gpu_gate9_final_51b71bb/).

---

## Intra-Solve Parallel Branch-and-Bound (Multicore)

SOV-OPT implements genuine intra-solve multi-process branch-and-bound for individual MILP solves:
- **Tree Coordination:** Central coordinator manages node dispatch, incumbent sharing, global bound tracking, and canonical pseudocost state.
- **Worker Processes:** Independent worker processes evaluate continuous LP relaxations via warm-started dual simplex.
- **Matched Engine Scaling (Primary Headline):** On an 18-variable multiknapsack workload using the matched coordinator engine, runtime scaled from 3.445s (1 worker) to 1.776s (2 workers) while exploring the **exact same 287-node search tree**, achieving **1.94x matched-engine solve-to-completion speedup using 2 workers while exploring the identical 287-node search tree, with 97.0% measured parallel efficiency** and identical verified solution.
- **Search-Order Pruning Effect (Secondary Headline):** On a 16-variable multiknapsack, concurrent worker exploration discovered incumbents earlier, reducing explored nodes from 321 to 59 and yielding a **3.60× solve time reduction** (reported separately due to search divergence).
- **MIPLIB Fixed-Budget Search Progress:** Across 38 MIPLIB instances evaluated under identical 10-second budgets, 4 workers evaluated up to 39× more branch-and-bound nodes than serial search (*search-progress metric, not solve-to-completion speedup*).
- **Historical Batch Throughput:** Process-level concurrent batch dispatch across independent problem instances achieved 2.65× on 4 workers (preserved as separate throughput evidence).

Full telemetry and scaling logs are recorded under [`reports/gate20d_parallel_bnb/`](reports/gate20d_parallel_bnb/).

---

## Validated Cutting Planes

- **Binary Cover Cuts:** Automated separation of knapsack cover inequalities with greedy lifting; **0 invalid cuts found under exhaustive binary-oracle validity testing on the tested small models** (100% exhaustive binary-oracle validity agreement on the tested small models). Evaluated on knapsack/oracle MILPs, achieving a **40–54.5% reduction in branch-and-bound search nodes**.
- **Authentic MIPLIB Evaluation:** Evaluated across 38 authentic MIPLIB instances: 0 improved, 38 unchanged, 0 worsened, with zero correctness regressions or numerical failures.
- **Gomory / GMI Cuts Deferred:** Postponed for mathematical safety (Option C: current dual simplex interface does not expose a proof-safe original-space tableau mapping).

Full verification and oracle logs are recorded under [`reports/gate20c_milp_cuts/`](reports/gate20c_milp_cuts/).

---

## Public Benchmark Sources

All performance benchmarks use publicly verifiable problem instances with frozen cryptographic manifests:

- **Netlib LP:** Authentic linear programming instances (AFIRO, SC50A, SC50B, BLEND, and WOODINFE) from the Netlib repository.
- **MIPLIB 2017:** Mixed-integer linear programming instances (FLUGPL) evaluated against official ground-truth objective solutions (`miplib2017-v37.solu`).
- **QPLIB 2018:** Continuous convex quadratic instances (QPLIB_8845, QPLIB_9002) from the ZIB mathematical benchmark collection.
- **Hans Mittelmann LP:** Authentic large-scale LP benchmark instances (`qap15`, `brazil3`, `chromaticindex1024-7`, `supportcase10`) from the ASU Plato benchmark repository.

Manifest integrity, file sources, and SHA-256 digests are recorded in [`data/manifest.json`](data/manifest.json) and [`data/CATALOGUE.md`](data/CATALOGUE.md).

---

## Validation & Testing

The test suite covers linear algebra invariants, simplex correctness, QP KKT stationarity, MILP branching semantics, cover cut validity, parallel B&B race safety, certificate falsification, and HTTP API integration.

```bash
# Run full unit and regression test suite (368 tests)
.venv/bin/python -m unittest discover -s tests -v

# Verify cryptographic manifest checksums
.venv/bin/python scripts/verify_checksums.py
```

**Current Test Results (Local clean environment):**
- **Ran 368 tests in 66.8s**
- **357 passed, 11 skipped, 0 failures, 0 errors** (skipped tests correspond to optional loopback network sockets and GPU-only hardware requirements).
- `verify_checksums.py`: **SUCCESS** (All tracked files match expected SHA-256 digests).

---

## Local Setup

### 1. Prerequisites
- Python 3.11 or higher.
- `pip` package manager.

### 2. Clone and Setup Environment
```bash
git clone https://github.com/sg721642/sov-opt-mrpl-26119.git
cd sov-opt-mrpl-26119

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install runtime dependencies (NumPy 2.3.5)
pip install -r requirements.txt
```

### 3. Launch Local Server
```bash
python server.py --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## API & Deployment

The unified server (`server.py`) hosts both the frontend static assets and the HTTP API on the same origin:

- `GET /health` or `GET /api/health`: Service liveness, version, and solver readiness.
- `GET /api/manifest`: JSON catalog of benchmark instances and provenance hashes.
- `GET /api/examples`: Built-in scenario models.
- `GET /api/refinery_twin`: Parameterised refinery model generator (`?variant=lp|milp|qp&c_arab=...`).
- `GET /api/gpu_summary`: Physical GPU validation summary telemetry.
- `POST /api/solve`: Solver dispatch endpoint accepting JSON model representations (capped at 100 variables / 150 rows for public web safety).

**Production Deployment:**  
Publicly hosted on Render at [https://sov-opt-mrpl-26119.onrender.com](https://sov-opt-mrpl-26119.onrender.com).

---

## Sovereignty Boundary

The core solver (`sovopt/`) is strictly sovereign and independent:

- **Core Dependencies:** Python standard library and NumPy (`numpy==2.3.5`).
- **No Third-Party Solvers in Core:** The solver core does not import, link, or invoke Gurobi, CPLEX, HiGHS, SCIP, CBC, OR-Tools, or CVXPY.
- **External Solvers in Repository:** External solvers (`highspy`, `scipy`) are used exclusively in isolated offline baseline worker scripts (`scripts/baseline_worker.py`) for differential comparison and validation.

---

## Status Semantics

SOV-OPT enforces strict, unambiguous solver status semantics:

| Status Code | Mathematical Meaning | Verification Invariant |
| :--- | :--- | :--- |
| `OPTIMAL_VERIFIED` | Solution found and independently validated on unscaled original equations | Primal, dual, and complementarity residuals $\le \text{tol}$; integrality residuals $\le 10^{-6}$ |
| `INFEASIBLE_CERTIFIED` | Infeasibility proven via valid certificate | Farkas ray satisfies $y^T A = 0, y^T b > 0, y \ge 0$ in exact rational arithmetic |
| `UNBOUNDED_CERTIFIED` | Unboundedness proven via recession direction | Feasible base point $x_0$ and ray $d$ satisfy $A d \le 0, d \ge 0, c^T d < 0$ |
| `LIMIT_REACHED` | Computational budget exhausted (iterations, time, nodes) | No optimality claim; conservative lower bounds reported where available |
| `NUMERICAL_FAILURE` | Numerical breakdown encountered (singular basis, step-size stall) | Fail-closed; never returns false or uncertified solution vectors |
| `INVALID_MODEL` | Structural violation detected during model ingestion | Rejects dimension mismatches, invalid bounds, or nonconvex quadratic matrices |

---

## Project Structure

```text
sov-opt-mrpl-26119/
├── sovopt/              # Sovereign optimization core (simplex, dual simplex, milp, qp, pdhg, verify, sparse, cuts)
├── web/                 # Web portal frontend (index.html, app.js, style.css, static assets)
├── tests/               # Comprehensive automated test suite (368 unit and integration tests)
├── scripts/             # Offline verification, benchmarking, checksum, and reporting tooling
├── data/                # Frozen public benchmark datasets, catalogue, and integrity manifests
├── reports/             # Verified benchmark reports, physical GPU telemetry, and audit summaries
├── docs/                # Mathematical specifications, architecture, and deployment guides
├── server.py            # Lightweight production HTTP server and API backend
├── requirements.txt     # Exact pinned runtime dependencies (NumPy 2.3.5)
└── SHA256SUMS.json      # Cryptographic SHA-256 checksum ledger for repository files
```

---

## Documentation

Comprehensive technical documentation is available in the [`docs/`](docs/) directory:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Mathematical formulations, linear algebra architecture, and module structure.
- [`docs/VALIDATION.md`](docs/VALIDATION.md): Step-by-step reproducible validation guide, coverage gaps, and test organization.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Production hosting, container configuration, and environment variables.
- [`docs/PDHG.md`](docs/PDHG.md): Mathematical specification of restarted first-order primal-dual hybrid gradient methods.
- [`docs/DUAL_SIMPLEX.md`](docs/DUAL_SIMPLEX.md): Bounded-variable dual simplex, Devex pricing, and basis dynamics.
- [`docs/PRESOLVE_AND_SCALING.md`](docs/PRESOLVE_AND_SCALING.md): Reversible bound reduction rules and matrix equilibration.
- [`docs/QPLIB_SUPPORT.md`](docs/QPLIB_SUPPORT.md): QPLIB file format parsing, allow-lists, and convexity checking.
- [`docs/BENCHMARK_METHODOLOGY.md`](docs/BENCHMARK_METHODOLOGY.md): Public benchmark selection, stratification, and differential testing rules.
- [`data/CATALOGUE.md`](data/CATALOGUE.md): Dataset provenance records, source links, and SHA-256 digests.
- [`CHANGELOG.md`](CHANGELOG.md): Chronological release log across development milestones.

---

## Team VarunNetra

**Rajiv Gandhi Institute of Petroleum Technology**  
Smart India Hackathon 2026 · Team ID: 177365

1. **Khagesh Ranjan** (Team Leader)  
   B.Tech + M.Tech (Dual Degree) in Computer Science and Engineering & Artificial Intelligence  
   Email: [24cs2021@rgipt.ac.in](mailto:24cs2021@rgipt.ac.in) · [LinkedIn](https://www.linkedin.com/in/khagesh-ranjan-986721324/)

2. **Satyam Gupta**  
   B.Tech + M.Tech (Dual Degree) in Computer Science and Engineering & Artificial Intelligence  
   Email: [24cs2032@rgipt.ac.in](mailto:24cs2032@rgipt.ac.in) · [LinkedIn](https://www.linkedin.com/in/satyam-gupta-2a1021324/)

3. **Sudipto Ghosh**  
   B.Tech + M.Tech (Dual Degree) in Computer Science and Engineering & Artificial Intelligence  
   Email: [24cs2037@rgipt.ac.in](mailto:24cs2037@rgipt.ac.in) · [LinkedIn](https://www.linkedin.com/in/sudipto-ghosh-486269346/)

4. **Ayush Rao**  
   B.Tech in Information Technology  
   Email: [24it3013@rgipt.ac.in](mailto:24it3013@rgipt.ac.in) · [LinkedIn](https://www.linkedin.com/in/ayush-rao-5359bb335/)

5. **Shivanshu Tripathi**  
   B.Tech + M.Tech (Dual Degree) in Computer Science and Engineering & Artificial Intelligence  
   Email: [24cs2036@rgipt.ac.in](mailto:24cs2036@rgipt.ac.in) · [LinkedIn](https://www.linkedin.com/in/shivanshu-tripathi-254876331/)

6. **Muskan Sahu**  
   B.Tech in Information Technology  
   Email: [24it3036@rgipt.ac.in](mailto:24it3036@rgipt.ac.in) · [LinkedIn](https://www.linkedin.com/in/muskan-sahu-717162332/)

---

## Roadmap

### Completed in v0.3.2
- ✓ **Sovereign Sparse Core:** True CSR/CSC matrices, Markowitz threshold LU ($u=0.1$), PFI eta updates, SpMV stress-tested to 1,000,000 variables.
- ✓ **Physical GPU Acceleration (RTX 5050):** 5.81× end-to-end acceleration on 10K true-sparse PDHG; 448.3× steady-state compute-loop ratio.
- ✓ **Validated Binary Cover Cuts:** Exact cover separation and lifting; 40–54.5% node reduction on targeted knapsack benchmarks.
- ✓ **Intra-Solve Parallel B&B:** Genuine multi-process tree search; 1.94× matched 2-worker scaling (97.0% efficiency) on identical search tree.
- ✓ **Mittelmann Benchmark Subset:** 4 authentic instances evaluated; on physical RTX 5050 CUDA backend, SOV-OPT reached `OPTIMAL_VERIFIED` for `chromaticindex1024-7` in the recorded 80.21 s run, with the returned solution passing the project's numerical KKT verification.

### Planned Research Extensions
- **Gomory Mixed-Integer (GMI) Cuts:** Developing a proof-safe original-space tableau/basis mapping for dual simplex.
- **Nonlinear & Pooling Formulations:** McCormick relaxation envelopes and Successive Linear Programming (SLP) for multi-component crude blending and pooling models.
- **Extended Mixed-Integer Quadratic Programming (MIQP):** Branch-and-bound exploration over convex quadratic objectives.
