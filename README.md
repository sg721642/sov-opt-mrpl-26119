# SOV-OPT — Sovereign Numerical Optimization Prototype

**MRPL SIH Problem Statement 26119**  
**Repository:** https://github.com/sg721642/sov-opt-mrpl-26119 (Private)  
**Solver Core Dependencies:** Python standard library and NumPy 2.3.5 only.

SOV-OPT is an original numerical optimization research prototype developed for linear programming (LP), mixed-integer linear programming (MILP), and convex quadratic programming (QP). The solver core (\`sovopt/\`) is strictly sovereign: it does not import or depend on HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX, or any other optimization package.

External solvers are permitted solely in isolated subprocess workers (\`scripts/baseline_worker.py\`) to produce differential validation comparisons.

---

## Quick Start

### 1. Installation
Requires Python 3.11+ on Linux, macOS, or Windows:

```bash
# Create and activate a project-local virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install core runtime dependencies
pip install -r requirements.txt
```

### 2. Run Unit Tests
```bash
.venv/bin/python -m unittest discover -s tests -v
```

### 3. Launch Local Dashboard
```bash
.venv/bin/python server.py --port 8000
```
Open http://127.0.0.1:8000 in your browser to view the interactive dashboard, load genuine Netlib benchmarks, and execute solves.

### 4. Solve from the Command Line
```bash
# Solve a canonical JSON model
.venv/bin/python -m sovopt examples/afiro.json

# Solve via first-order Primal-Dual Hybrid Gradient (PDHG)
.venv/bin/python -m sovopt examples/afiro.json --backend pdhg-cpu
```

### 5. Automated Reports & Differential Validation
```bash
# Run local solve benchmarks and regenerate reports
.venv/bin/python scripts/generate_reports.py

# Optional: Run with external HiGHS differential validation
bash scripts/create_benchmark_env.sh .venv-benchmark
SOVOPT_BENCHMARK_PYTHON=.venv-benchmark/bin/python .venv/bin/python scripts/generate_reports.py
```

---

## Implemented Algorithms

- **Linear Programming (LP):** Two-phase primal revised simplex with dense LU factorization, partial row pivoting, iterative refinement, and reversible canonical variable transformations (box, free, one-sided, and fixed variables).
- **Mixed-Integer Linear Programming (MILP):** Branch-and-bound with best-bound queue and most-fractional branching. Lower bounds are evaluated using exact rational basis dual calculations (\`_exact_dual_from_basis\`) and Neumaier-Shcherbina Lagrangian bounds in exact arithmetic (\`fractions.Fraction\`). Infeasible nodes are pruned via exact binary-rational Farkas certificates.
- **Convex Quadratic Programming (QP):** Infeasible-start Mehrotra predictor-corrector primal-dual interior point algorithm for convex objectives ($\min \frac{1}{2} x^T Q x + c^T x$) with linear constraints.
- **Experimental First-Order LP (PDHG):** Primal-Dual Hybrid Gradient method (Chambolle-Pock) with diagonal preconditioning and periodic restart. Includes CPU SpMV and CUDA RawKernel source.

---

## Active Verified Datasets

All models in the active benchmark suite (\`data/verified/\`) are genuine, provenance-verified instances from authoritative sources:

| Dataset | Problem Class | Origin | Reference Objective / Bound |
|:---|:---:|:---|:---|
| **AFIRO** | LP | Netlib / Stanford Systems Optimization Lab | -464.75314286 (MINOS 5.3) |
| **SC50A** | LP | Netlib staircase dynamic production LP | -64.575077059 (MINOS 5.3) |
| **SC50B** | LP | Netlib staircase dynamic production LP | -70.000000000 (MINOS 5.3) |
| **BLEND** | LP | Netlib petroleum refinery blending LP (Murtagh) | -30.812149846 (MINOS 5.3) |
| **FLUGPL** | MILP | MIPLIB airline fleet allocation model (Wagner et al.) | 1201500.0 (integer optimum) |

*Full provenance, hashes, and redistribution terms are recorded in [\`data/CATALOGUE.md\`](data/CATALOGUE.md).*

---

## Honest Limitations & Boundaries

- **Dense Linear Algebra:** The solver core uses dense LU factorization. Size caps are enforced: 250 variables / 1000 rows (CLI), 100 variables / 150 rows (web). Problems exceeding limits report \`LIMIT_REACHED\` or \`NUMERICAL_FAILURE\`. Sparse LU is planned.
- **Primal Simplex Only:** The current LP implementation is primal revised simplex. Dual simplex, Devex pricing, and basis warm-starts are not yet implemented.
- **MILP Scale:** Branch-and-bound uses cold-start LP relaxations. Large integer problems reach node limits. FLUGPL terminates at \`LIMIT_REACHED\` at 50 nodes with a valid conservative lower bound ($\approx 1173644.9999999998$), but no incumbent found.
- **QP Conditioning:** The interior-point method solves normal equations via dense Cholesky/LU; severely ill-conditioned matrices may encounter numerical failure.MIQP is rejected.
- **CUDA / GPU Acceleration:** The development environment is macOS Apple Silicon (ARM64), which lacks NVIDIA CUDA hardware. \`gpu_executed\` is strictly \`false\` on all local runs. CUDA source exists in \`sovopt/pdhg.py\` but requires physical NVIDIA hardware to execute.
- **Disclosed Empty States:**
  - *No MRPL Production Data:* Confidential operational refinery data is proprietary. Fictional numbers are prohibited; Netlib \`BLEND\` is provided as an authentic benchmark.
  - *No Industrial QP Data:* No authentic public industrial convex QP instance is currently admitted. Synthetic toy models have been removed.

---

## Documentation Index

- [Architecture & Mathematics](docs/ARCHITECTURE.md): Implemented algorithms, variable transformations, objective conventions, verification semantics, and roadmap gates.
- [Validation Guide & Evidence](docs/VALIDATION.md): Reproducible test and benchmark commands, differential comparisons, evidence file locations, and coverage gaps.
- [Dataset Catalogue](data/CATALOGUE.md): Dataset provenance, cryptographic hashes, source links, and empty state declarations.
- [Changelog](CHANGELOG.md): Complete release history and development record.
- [Contributor Workflow](AGENTS.md): Dataset integrity, Git workflow, and sovereign core requirements.
