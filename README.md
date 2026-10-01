# SOV-OPT — Sovereign Numerical Optimization Core

**MRPL SIH Problem Statement 26119**  
**Repository:** https://github.com/sg721642/sov-opt-mrpl-26119 (Private)  
**Solver Core Dependencies:** Python standard library and NumPy 2.3.5 only.

> *"GPU accelerates. CPU verifies. No result is trusted merely because an optimization algorithm stopped."*  
> *Core Engineering Philosophy: Correctness first. Robustness second. Performance third. Breadth fourth.*

SOV-OPT is an original numerical optimization research prototype developed for linear programming (LP), mixed-integer linear programming (MILP), and convex quadratic programming (QP). The solver core (`sovopt/`) is strictly sovereign: it does not import or depend on HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX, or any other optimization package.

---

## The Sovereignty Boundary

| In Scope: Sovereign Core (`sovopt/`) | Out of Scope: Isolated External Validation |
|:---|:---|
| **Dependencies:** NumPy and Python stdlib only | **Dependencies:** `highspy`, `scipy` allowed |
| **Execution:** In-process Python / CUDA C++ kernel | **Execution:** Isolated subprocess worker (`scripts/baseline_worker.py`) |
| **Role:** Produces all application solutions | **Role:** Produces differential validation comparisons only |
| **Trust:** Every solution verified by independent KKT & rational verifier | **Trust:** External solver results never substituted into `sovopt/` |

---

## Quick Start

### 1. Installation
Requires Python 3.11+ on Linux, macOS, or Windows:

```bash
# Create and activate a project-local virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install core runtime dependencies (NumPy 2.3.5)
pip install -r requirements.txt
```

### 2. Run Comprehensive Unit Tests
```bash
.venv/bin/python -m unittest discover -s tests -v
```

### 3. Launch Local Dashboard
```bash
.venv/bin/python server.py --port 8000
```
Open http://127.0.0.1:8000 in your browser to view the interactive dashboard, load genuine Netlib benchmarks, and execute solves.

### 4. MRPL Refinery Planning Digital Twin Demonstration
Run the 5-step mathematical verification demonstration:
```bash
.venv/bin/python scripts/demonstrate_refinery_twin.py
```

### 5. CLI Solve & Numerical Trust Report
```bash
# Print formatted Numerical Trust Report for genuine Netlib benchmark
.venv/bin/python -m sovopt examples/afiro.json --report

# Solve MRPL Refinery Planning Twin variants directly from CLI
.venv/bin/python -m sovopt --refinery-twin lp --report
.venv/bin/python -m sovopt --refinery-twin milp --report
.venv/bin/python -m sovopt --refinery-twin qp --report
.venv/bin/python -m sovopt --refinery-twin infeasible --report

# Automatic algorithm dispatcher with explicit method overrides
.venv/bin/python -m sovopt examples/afiro.json --method simplex
.venv/bin/python -m sovopt examples/afiro.json --backend pdhg-cpu
```

### 6. Automated Benchmark Reports & Differential Validation
```bash
# Run local solve benchmarks and regenerate reports
.venv/bin/python scripts/generate_reports.py

# Optional: Run with external HiGHS differential validation
bash scripts/create_benchmark_env.sh .venv-benchmark
SOVOPT_BENCHMARK_PYTHON=.venv-benchmark/bin/python .venv/bin/python scripts/generate_reports.py

# Verify cryptographic checksums of all tracked artifacts
.venv/bin/python scripts/verify_checksums.py
```

---

## Implemented Algorithms & Automatic Dispatcher

- **Automatic Algorithm Dispatcher (`sovopt.auto_dispatch`):** Inspects problem dimensions, matrix sparsity, dynamic range, integrality, and quadratic objective structure to select the appropriate solver core automatically:
  - **Linear Programming (LP):** Two-phase primal revised simplex with dense LU factorization, Markowitz partial pivoting, iterative refinement, and exact rational basis dual recovery.
  - **Mixed-Integer Linear Programming (MILP):** Branch-and-bound with exact rational Lagrangian lower bounds (`safe_lower_bound`) and exact Farkas infeasibility pruning.
  - **Convex Quadratic Programming (QP):** Infeasible-start Mehrotra predictor-corrector primal-dual interior point algorithm for convex objectives ($\min \frac{1}{2} x^T Q x + c^T x$) with linear constraints.
  - **First-Order LP (PDHG):** Primal-Dual Hybrid Gradient method (Chambolle-Pock) with diagonal preconditioning and periodic restart. Includes CPU SpMV and CUDA RawKernel source.

---

## MRPL Refinery Planning Digital Twin

The repository includes a parameterised multi-period digital twin formulation representing Mangalore Refinery and Petrochemicals Limited (MRPL) operations:
- **Atmospheric & Vacuum Distillation (CDU/VDU):** Arab Light and Basrah crude blending and primary cuts.
- **Secondary Conversion:** Fluid Catalytic Cracking (FCC) and Continuous Catalytic Reforming (CCR).
- **Product Blending & Quality Specs:** BS-VI Motor Spirit (Gasoline, RON $\ge 93$) and Euro-VI High Speed Diesel (Cetane $\ge 48$).
- **Multi-Period Intermediate Inventory:** Dynamic balance across storage tankage.

### Four Operational Variants
1. **`lp` (Continuous Economic Plan):** Minimizes net crude acquisition and processing costs minus finished product revenues.
2. **`milp` (Discrete Operational Plan):** Enforces binary unit commitment ($z \in \{0, 1\}$) and physical minimum turndown throughput limits.
3. **`qp` (Smooth Operational Dispatch):** Introduces positive semidefinite quadratic throughput-flutter penalties ($\frac{1}{2} \Delta u^T Q \Delta u$) to protect heavy processing units against thermal and mechanical stress.
4. **`infeasible` (Diagnostic Scenario):** Evaluates impossible market demand specifications to verify exact binary-rational Farkas certificates ($y \ge 0, y^T A \le 0, y^T b > 0$).

> *PROVENANCE DISCLAIMER: The refinery planning twin is an original engineering formulation developed for MRPL SIH PS 26119 demonstration and benchmarking from open refining literature (Gary & Handwerk; Meyers). It does not contain proprietary MRPL operating data, actual commercial contracts, or confidential refinery telemetry.*

---

## Active Verified Datasets & Model Categories

All models in the active performance suite (`data/verified/`) are genuine, provenance-verified instances from authoritative sources:

| Dataset | Problem Class | Origin | Reference Objective / Bound |
|:---|:---:|:---|:---|
| **AFIRO** | LP | Netlib / Stanford Systems Optimization Lab | -464.75314286 (MINOS 5.3) |
| **SC50A** | LP | Netlib staircase dynamic production LP | -64.575077059 (MINOS 5.3) |
| **SC50B** | LP | Netlib staircase dynamic production LP | -70.000000000 (MINOS 5.3) |
| **BLEND** | LP | Netlib petroleum refinery blending LP (Murtagh) | -30.812149846 (MINOS 5.3) |
| **FLUGPL** | MILP | MIPLIB airline fleet allocation model (Wagner et al.) | 1201500.0 (integer optimum) |

### Dataset Architecture & Category Separation

SOV-OPT maintains strict dataset separation across five categories:
1. **Category A (Public Performance Benchmark):** 5 instances in `data/verified/` (AFIRO, SC50A, SC50B, BLEND, FLUGPL).
2. **Category B (Public Certificate-Validation Dataset):** 1 instance in `data/certificate_validation/` (WOODINFE — Netlib infeasible LP collection, Chinneck 1993 / Greenberg 1993; evaluated strictly for Farkas certificate validity, not runtime speed).
3. **Category C (Representative Refinery Formulation):** 1 model with 4 operational variants (`sovopt/refinery_twin.py`, MRPL digital twin with continuous LP, discrete MILP, smooth QP, and infeasible diagnostic variants).
4. **Category D (Internal Mathematical Unit Fixture):** 18 edge cases in `TestUnboundedCertificateHardening` (`tests/test_solver.py`).
5. **Category E (Quarantined Dataset):** 1 instance in `data/quarantined/` (AVGAS).

> *COMPETITION INTEGRITY STATEMENT: No synthetic or team-invented model is used as public benchmark, performance evidence, accuracy evidence, or industrial-data evidence. Small handcrafted models are used only as isolated mathematical unit tests.*

*Full provenance, hashes, and redistribution terms are recorded in [`data/CATALOGUE.md`](data/CATALOGUE.md).*

---

## Non-Linear Extension Roadmap

Refinery planning exhibits non-linear phenomena (pooling, octane blending non-linearities, pressure drop). SOV-OPT follows a rigorous mathematical progression:
$$\text{LP} \longrightarrow \text{MILP} \longrightarrow \text{QP} \longrightarrow \text{Bilinear Pooling} \longrightarrow \text{SLP / Convex Relaxation} \longrightarrow \text{NLP} \longrightarrow \text{MINLP}$$
- **Phase 1 (Delivered):** Verified LP, MILP, and convex QP cores with independent KKT and rational certificates.
- **Phase 2 (Roadmap Gate):** McCormick envelopes and piecewise-linear convex relaxations for bilinear crude blend pooling.
- **Phase 3 (Roadmap Gate):** Successive Linear Programming (SLP) and Augmented Lagrangian SQP with exact constraint verification.

---

## Honest Limitations & Competition Disclosures

- **Dense Linear Algebra:** The solver core uses dense LU factorization. Size caps are enforced: 250 variables / 1000 rows (CLI), 100 variables / 150 rows (web). Problems exceeding limits report `LIMIT_REACHED` or `NUMERICAL_FAILURE`. Sparse LU is planned.
- **Primal Simplex Only:** The current LP implementation is primal revised simplex. Dual simplex, Devex pricing, and basis warm-starts are not yet implemented.
- **MILP Scale:** Branch-and-bound uses cold-start LP relaxations. Large integer problems reach node limits. FLUGPL terminates at `LIMIT_REACHED` at 50 nodes with a valid conservative lower bound, but no incumbent found.
- **QP Conditioning:** The interior-point method solves normal equations via dense LU; severely ill-conditioned matrices may encounter numerical failure.
- **Public Unbounded Benchmark:** No suitable provenance-verified public unbounded LP instance was identified in the Netlib and HiGHS collections searched during this audit (search date: 2026-10-01). Therefore: `PUBLIC UNBOUNDED CERTIFICATE BENCHMARK: NOT YET AVAILABLE`. Handcrafted test cases are used solely as internal mathematical unit fixtures.
- **CUDA / GPU Acceleration:** The development environment is macOS Apple Silicon (ARM64), which lacks NVIDIA CUDA hardware. `gpu_executed` is strictly `false` on all local runs. CUDA source exists in `sovopt/pdhg.py` but requires physical NVIDIA hardware to execute.
- **Defensible Competition Claims:** We do not claim commercial-solver parity across all benchmark libraries or universal zero errors. We do claim: an original sovereign core, mathematically verified solutions with rigorous KKT and exact rational certificates, zero external solver dependencies in the solver core, and an authentic parameterised refinery planning digital twin.

---

## Documentation Index

- [Architecture & Mathematics](docs/ARCHITECTURE.md): Implemented algorithms, variable transformations, objective conventions, verification semantics, and roadmap gates.
- [Validation Guide & Evidence](docs/VALIDATION.md): Reproducible test and benchmark commands, differential comparisons, evidence file locations, and coverage gaps.
- [Dataset Catalogue](data/CATALOGUE.md): Dataset provenance, cryptographic hashes, source links, and empty state declarations.
- [Changelog](CHANGELOG.md): Complete release history and development record.
- [Contributor Workflow](AGENTS.md): Dataset integrity, Git workflow, and sovereign core requirements.
