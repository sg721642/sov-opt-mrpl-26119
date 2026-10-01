# Reproducible Validation and Evidence — SOV-OPT

This document records the exact procedures for reproducing all numerical benchmarks, unit tests, differential comparisons against external reference solvers, and honest disclosures of current coverage gaps.

---

## 1. Quick Verification Commands

All commands below assume execution from the project root with the project-local virtual environment active:

```bash
# 1. Run full unit and regression test suite (81 tests: 79 passing, 2 integration tests skipped in restricted sandbox)
.venv/bin/python -m unittest discover -s tests -v

# 2. Run automated report and benchmark generator
.venv/bin/python scripts/generate_reports.py

# 3. Run with external HiGHS differential validation (requires benchmark environment)
SOVOPT_BENCHMARK_PYTHON=.venv-benchmark/bin/python .venv/bin/python scripts/generate_reports.py

# 4. Launch local dashboard
.venv/bin/python server.py --port 8000
```

---

## 2. Test Suite Organization

The active test suite is split into three modules (81 tests total):

### 2.1 Solver Correctness (`tests/test_solver.py` — 45 tests)
- Core solver tests for LU pivot refinement, verified Netlib instances (AFIRO, SC50A, SC50B, BLEND), FLUGPL MILP lower bounding and Farkas certificate generation, bad candidate rejection, affine coordinate transformations, PDHG first-order convergence, and limits enforcement.
- `TestUnboundedCertificateHardening` (18 tests): Exhaustive validation of primal-feasible base points $x_0$ and recession directions $d$ for `UNBOUNDED_CERTIFIED` status across unconstrained, constrained, free, shifted, and ranged models.
- Differential comparison unit tests and MRPL refinery planning twin tests across all 4 operational variants.

### 2.2 Server and Dashboard API (`tests/test_server.py` — 8 tests)
- **`HandlerUnitTests`**: Direct in-process testing of the HTTP request handler (`/health`, `/`, `/api/manifest`, `/api/examples`, `/api/solve`, invalid payloads).
- **`ServerIntegrationTests`**: Socket-based integration tests connecting over loopback network. (Automatically skipped when loopback sockets are restricted by sandbox policy).

### 2.3 Sparse Numerical Linear Algebra (`tests/test_sparse.py` — 28 tests)
- Unit and integration tests covering the complete sovereign sparse numerical linear algebra stack:
  1. CSR matrix construction, storage validation, and shape properties.
  2. CSC matrix construction and coordinate triplet conversion.
  3. Sparse matrix-vector product ($A x$).
  4. Sparse transpose matrix-vector product ($A^T y$).
  5. Arbitrary sparse column subset basis extraction.
  6. Deterministic column/row index sorting.
  7. Duplicate coordinate summation.
  8. Numerical zero-entry dropping.
  9. Markowitz fill-in pivot selection scoring.
  10. Threshold numerical pivot rejection ($u=0.1$).
  11. Honest singular sparse matrix error detection.
  12. Sparse LU factorization ($P B Q = L U$) numerical equality.
  13. Forward sparse solve (FTRAN) residual verification ($\le 10^{-12}$).
  14. Backward transpose sparse solve (BTRAN) residual verification ($\le 10^{-12}$).
  15. Exact agreement between sparse and dense solves across random systems.
  16. Iterative refinement residual improvement and telemetry tracking.
  17. Single Product-Form of Inverse (PFI) eta basis update.
  18. Multiple sequential eta basis updates matching direct solves.
  19. Backward eta sweep (BTRAN) with multiple accumulated eta vectors.
  20. Forced basis refactorization trigger and state reset.
  21. Eta-limit refactorization trigger (`ETA_LIMIT`).
  22. Residual-degradation refactorization trigger (`RESIDUAL_DETERIORATION`).
  23. Small-pivot near-singular basis refactorization trigger (`SMALL_PIVOT`).
  24. Sparse primal revised simplex solve on genuine Netlib AFIRO (`OPTIMAL_VERIFIED`).
  25. Sparse primal revised simplex solve on genuine Netlib SC50A (`OPTIMAL_VERIFIED`).
  26. Sparse primal revised simplex solve on genuine Netlib SC50B (`OPTIMAL_VERIFIED`).
  27. Sparse primal revised simplex solve on genuine Netlib BLEND (`OPTIMAL_VERIFIED`).
  28. Original untransformed model KKT verification after sparse solves across all 4 Netlib instances.

---

## 3. External Differential Validation Setup

External differential validation compares SOV-OPT against native HiGHS (C++) running in an isolated subprocess. External solvers are **never imported** by the core solver (\`sovopt/\`) or server.

### Creating the Benchmark Environment
Run the setup script:
```bash
bash scripts/create_benchmark_env.sh .venv-benchmark
```
This script creates an isolated virtual environment containing \`highspy\` (1.15.1) and \`scipy\` (1.17.1).

### Running Differential Validation
```bash
SOVOPT_BENCHMARK_PYTHON=.venv-benchmark/bin/python .venv/bin/python scripts/generate_reports.py
```
This script invokes \`scripts/baseline_worker.py\` in a separate subprocess for each active instance and records:
- Executed command and exit code.
- Dynamic solver version (\`1.15.1\`).
- Parsed model dimensions, objective sense, and integer variables.
- Status, objective, solution availability, and best bounds.
- Comparison status (\`MATCH\` or \`BOUND_ONLY\`) and objective discrepancy vs SOV-OPT.

Output is written to \`reports/external_validation.json\` and summarized in \`reports/VERIFIED_BENCHMARKS.md\`.

---

## 4. Current Evidence Locations

- **Automated Benchmark Report:** `reports/VERIFIED_BENCHMARKS.md`
- **External Validation JSON:** `reports/external_validation.json`
- **Local Solve Records (timestamped):** `reports/local_validation/2026-10-01_verified/`
  - `afiro.json`, `sc50a.json`, `sc50b.json`, `blend.json`, `flugpl.json`, `afiro_pdhg.json`, `summary.json`
- **Active Public Performance Benchmarks:** `data/verified/` (5 instances: AFIRO, SC50A, SC50B, BLEND, FLUGPL)
- **Public Certificate-Validation Datasets:** `data/certificate_validation/` (1 instance: WOODINFE)
- **Representative Refinery Formulations:** `sovopt/refinery_twin.py` (4 variants: LP, MILP, QP, Infeasible)
- **Dataset Provenance and Metadata:** `data/CATALOGUE.md` and `data/manifest.json`
- **Quarantined Datasets:** `data/quarantined/` (1 instance: AVGAS)

---

## 5. Coverage Gaps & Honest Disclosures

1. **Dataset Integrity & Five Distinct Categories:**
   - No synthetic or team-invented model is used as public benchmark, performance evidence, accuracy evidence, or industrial-data evidence. Small handcrafted models are used only as isolated mathematical unit tests.
   - All models are organized into five distinct tiers:
     - **Category A (Public Performance Benchmark):** 5 instances in `data/verified/` (AFIRO, SC50A, SC50B, BLEND, FLUGPL).
     - **Category B (Public Certificate-Validation Dataset):** 1 instance in `data/certificate_validation/` (WOODINFE).
     - **Category C (Representative Refinery Formulation):** 1 model with 4 operational variants (`sovopt/refinery_twin.py`).
     - **Category D (Internal Mathematical Unit Fixture):** 18 edge cases in `TestUnboundedCertificateHardening` (`tests/test_solver.py`).
     - **Category E (Quarantined Dataset):** 1 instance in `data/quarantined/` (AVGAS).

2. **MILP `OPTIMAL_VERIFIED` Coverage Gap:**
   - There is currently no admitted genuine MILP instance in the verified suite that solves to full tree closure (`OPTIMAL_VERIFIED`) within practical automated test time limits on this machine.
   - MIPLIB `FLUGPL` reaches `LIMIT_REACHED` at 50 nodes, advancing the conservative lower bound to approximately `1173644.9999999998` (optimal is 1201500).
   - The optimality basis language regression is verified by code inspection and invariant checks; no synthetic MILP model has been constructed to manufacture a false green badge.

3. **Proprietary MRPL Refinery Data (Empty State):**
   - No authorized MRPL refinery dataset is available in this project.
   - Fictional refinery numbers are prohibited. Netlib refinery LP `BLEND` is provided as an authentic blending problem.

4. **Industrial Convex QP Data (Empty State):**
   - No authentic public industrial convex QP benchmark is currently admitted. Synthetic toy models have been removed.
   - Convex QP solving is validated via continuous KKT conditions on positive semi-definite matrices.

5. **AVGAS Historical Provenance (Quarantined):**
   - `avgas.mps` is sourced from the HiGHS repository (SHA-256 verified).
   - Its historical attribution to Charnes, Cooper, Mellon (1952) and Symonds (1955) has not been verified against primary literature. It is quarantined outside active runtime paths.

6. **Public Unbounded Certificate Benchmark (Not Yet Available):**
   - No suitable provenance-verified public unbounded LP instance was identified in the Netlib and HiGHS collections searched during this audit (search date: 2026-10-01).
   - Therefore: **PUBLIC UNBOUNDED CERTIFICATE BENCHMARK: NOT YET AVAILABLE**.
   - Unit test instances in `tests/test_solver.py` are strictly labeled `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA` and are explicitly excluded from public benchmark counts and performance reports.

7. **CUDA Acceleration (Hardware Unavailable):**
   - Development is performed on Apple Silicon ARM64, which lacks NVIDIA CUDA hardware.
   - `gpu_executed` is strictly `false` on all local runs. CUDA kernels in `sovopt/pdhg.py` remain unvalidated until tested on a physical NVIDIA device.

---

## 6. Baseline History Summary (Gate 0)

At the initial Gate 0 milestone (Git commit \`31f8de8\`), the sovereign boundary was verified on macOS ARM64 with Python 3.11.16 and NumPy 2.3.5. All 17 initial unit test methods passed without external solver imports. Subsequent milestones introduced verified public benchmarks (Netlib, MIPLIB), exact rational duals, ray recovery, model validation, and the current clean test suite.
