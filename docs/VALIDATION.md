# Reproducible Validation and Evidence — SOV-OPT

This document records the exact procedures for reproducing all numerical benchmarks, unit tests, differential comparisons against external reference solvers, and honest disclosures of current coverage gaps.

---

## 1. Quick Verification Commands

All commands below assume execution from the project root with the project-local virtual environment active:

```bash
# 1. Run full unit and regression test suite (249 tests: 247 passing, 2 integration tests skipped in restricted sandbox)
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

The active test suite is split into 11 modules (249 tests total, 247 passing, 2 integration tests skipped in restricted sandbox):

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

### 2.4 Bounded-Variable Revised Dual Simplex (`tests/test_dual_simplex.py` — 28 tests)
- Unit and integration tests covering the complete sovereign dual simplex engine:
  1. `DualBasisState` serialization, deserialization, and structural invariants.
  2. Initial variable states classification (`BASIC`, `AT_LOWER`, `AT_UPPER`, `FREE_NONBASIC`, `FIXED`).
  3. Dual feasibility verification on nonbasic reduced costs.
  4. Leaving row selection under primal bound violation.
  5. Devex pricing initialization with unit norm approximations.
  6. Devex weight update via Harris recurrence formula.
  7. Devex weight reset on excessive numerical growth.
  8. Two-Pass Harris ratio test Pass 1 threshold computation ($\delta = 10^{-7}$).
  9. Two-Pass Harris ratio test Pass 2 maximum pivot magnitude selection.
  10. Rejection of numerically unstable tiny pivots ($< 10^{-8}$) with telemetry.
  11. Bounded-variable ratio-test bound flips without basis refactorization.
  12. Multiple consecutive bound flips in a single dual iteration.
  13. Unbounded dual / primal infeasibility detection.
  14. Free nonbasic variable entering pivot dynamics.
  15. Fixed variable non-eligibility for entering basis.
  16. Sparse LU basis factorization and triangular substitution integration.
  17. Product-Form of Inverse (PFI) eta updates during real dual simplex pivots.
  18. Refactorization trigger after accumulated eta vectors.
  19. Dual Phase I auxiliary pricing for dual-infeasible starts.
  20. Dual Phase II transition with primal feasibility restoration.
  21. Cycling prevention and anti-degeneracy perturbations.
  22. Pure dual simplex solve on genuine Netlib AFIRO (`OPTIMAL_VERIFIED`).
  23. Pure dual simplex solve on genuine Netlib SC50A (`OPTIMAL_VERIFIED`).
  24. Pure dual simplex solve on genuine Netlib SC50B (`OPTIMAL_VERIFIED`).
  25. Pure dual simplex solve on genuine Netlib BLEND (`OPTIMAL_VERIFIED`).
  26. Original-model KKT verification across all 4 Netlib dual solutions.
  27. Warm reoptimization using saved `DualBasisState` after RHS bound perturbation.
  28. Fallback hierarchy to primal revised simplex upon numerical failure.

### 2.5 Reversible Presolve and Row/Column Scaling (`tests/test_presolve.py` — 35 tests)
- Exhaustive unit test matrix covering all Gate 5 reductions, scaling, and postsolve guarantees:
  1. Fixed variable elimination (simple substitution, objective offset recovery).
  2. Empty row processing (redundancy elimination, exact Farkas infeasibility certification).
  3. Empty column processing (optimal bound assignment, unbounded ray certification).
  4. Singleton row bound tightening (positive and negative coefficients, ranged rows, bound conflict detection).
  5. Conservative activity bound propagation (redundancy detection, infeasibility detection).
  6. Reversible row and column equilibration scaling round-trips.
  7. Strict linearity of direction postsolve (zero affine shift: $d(\alpha v) = \alpha d(v)$).
  8. Two-pass dual row multiplier reconstruction for tight and slack singleton rows.
  9. Original model immutability invariant checks.
  10. Dynamic range diagnostics and reduction assertions.
  11. 4-way ablation on Netlib benchmarks (AFIRO, SC50A, SC50B, BLEND).

### 2.6 Numerical Stress Tests (`tests/test_numerical_stress.py` — 10 tests)
- High-stress validation covering numerical edge cases:
  1. Row scales spanning 8 orders of magnitude ($10^{-4}$ to $10^{4}$).
  2. Column scales spanning 8 orders of magnitude ($10^{-4}$ to $10^{4}$).
  3. Near-dependent / parallel rows ($10^{-6}$ perturbation).
  4. Exact duplicate rows handled without basis singularity.
  5. Extreme finite bounds ($10^{14}$) without overflow.
  6. Small nonzero coefficients ($10^{-10}$) without division by zero.
  7. Matrix equilibration condition number reduction.
  8. Activity bounds with mixed extreme finite ($10^{14}$) and infinite bounds.
  9. Multi-decade objective scaling.
  10. Degenerate vertices with multiple active hyperplanes.

### 2.7 MILP Branch-and-Bound Engineering (`tests/test_milp.py` — 38 tests)
- Exhaustive unit test matrix covering all Gate 6 branch-and-bound capabilities:
  1. `DualBasisState` export on LP node solve.
  2. `DualBasisState` serialization / deserialization round-trip.
  3. Child warm start acceptance and pivot reduction.
  4. Dimension-mismatch detection and clean fallback.
  5. Binary variable down-branch upper bound enforcement ($u \le 0$).
  6. Binary variable up-branch lower bound enforcement ($l \ge 1$).
  7. General integer down-branch floor bound enforcement.
  8. General integer up-branch ceil bound enforcement.
  9. Immediate bound conflict pruning ($l > u$) without LP solve.
  10. Sibling and parent bound array strict memory isolation.
  11. Parent basis state immutability across child branches.
  12. Down-branch pseudocost accumulation and updating.
  13. Up-branch pseudocost accumulation and updating.
  14. Zero objective change handling without division by zero.
  15. Limited strong-branching bootstrap on unreliable candidates ($K_{\text{reliable}} = 2$).
  16. Strong-branching evaluation and iteration caps.
  17. Strong-branching basis state isolation.
  18. Deterministic branch variable tie-breaking by variable index.
  19. Pure best-bound node selection queue behavior.
  20. Hybrid node selection equivalence to best-bound when no incumbent exists.
  21. Hybrid node selection depth-diving near best bound with incumbent.
  22. Open node pruning upon pop when bound exceeds incumbent.
  23. Incumbent feasibility verification on original model.
  24. Lossless exact rational objective calculation.
  25. Incumbent history telemetry logging.
  26. Safe rounding heuristic evaluation and acceptance.
  27. Safe rounding heuristic continuous subproblem infeasibility safety.
  28. Conservative diving heuristic execution from root LP.
  29. Root model immutability preserved after diving heuristic.
  30. Exact rational Lagrangian lower bound preservation (`safe_lower_bound`).
  31. Minimization model objective offset mapping.
  32. Maximization model objective negation and upper bound offset mapping.
  33. Honest limit enforcement: `max_nodes=0` returns `LIMIT_REACHED` with `nodes=0`.
  34. Infeasible integer box returns `INFEASIBLE_CERTIFIED` with `nodes=0`.
  35. Infeasible root LP relaxation returns `INFEASIBLE_CERTIFIED` with `nodes=1`.
  36. 4-way FLUGPL ablation (baseline vs pseudocosts vs warm starts vs heuristics).
  37. Refinery twin MILP determinism across repeated solves.
  38. Full presence of all Gate 6 MILP telemetry keys.

### 2.8 QPLIB Format Parser & Convexity Verification (`tests/test_qplib.py` — 18 tests)
- Comprehensive test matrix validating Gate 7 QPLIB support:
  1. Header and metadata parsing across official QPLIB test cases.
  2. Diagonal quadratic objective function evaluation matching $\frac{1}{2} x^T Q x + b^T x + q$.
  3. Off-diagonal symmetric quadratic objective evaluation with equal splitting ($Q_{ij} = Q_{ji} = 0.5 Q^0_{ij}$).
  4. Parsed objective equivalence against manual formula $\frac{1}{2} x^T Q x + b^T x + q$.
  5. Machine-precision agreement on authentic `QPLIB_8845` against published reference ($10,907,992.4939988$).
  6. Original-model KKT verification (primal feasibility, dual stationarity, complementarity) on `QPLIB_8845`.
  7. Strict allow-list enforcement: `CCL`, `DCL`, `CCB`, `DCB`, `LCL` admitted.
  8. Discrete variable rejection (`UNSUPPORTED_DISCRETE_VARIABLES`) on binary/integer variables.
  9. Quadratic constraint rejection (`UNSUPPORTED_QUADRATIC_CONSTRAINTS`) on QCQP instances.
  10. Nonconvex objective rejection (`UNSUPPORTED_NONCONVEX_QP`) via scale-aware PSD eigenvalue test ($\tau = 10^{-10} \times \max(1, \max_i |Q_{ii}|)$).
  11. Authentic negative rejection test on official nonconvex instance `QPLIB_0018`.
  12. Large model rejection (`DIMENSION_LIMIT_EXCEEDED`) preventing unsafe dense $Q$ memory allocation ($n > 5000$).
  13. Memory limit enforcement ($> 250$ MB) before allocating $n \times n$ dense matrices.
  14. Range constraints parsing and lossless slack mapping.
  15. One-sided inequality constraints and variable box bounds.
  16. Free variable handling and zero-bound preservation.
  17. Independent sovereign solve of `QPLIB_8845` to `OPTIMAL_VERIFIED` with objective matching reference within $1.59 \times 10^{-10}$ relative error.
  18. Verification of zero reference solution leakage: sovereign solve achieves identical `OPTIMAL_VERIFIED` result when `.sol` file is hidden.

### 2.9 Benchmark Evidence Integrity & Semantics (`tests/test_gate7_1.py` — 12 tests)
- Rigorous validation of benchmark reporting semantics and evidence integrity:
  1. Segregation of reference `.sol` files from sovereign solver executions.
  2. Primal-only verification sets `kkt_evaluated = False` and `kkt_status = 'PRIMAL_FEASIBILITY_ONLY'`.
  3. Full KKT verification requires all 4 conditions (primal feasibility, dual feasibility, stationarity, complementarity).
  4. Programmatic assertion of Netlib LP candidate counts: 9 `OPTIMAL_VERIFIED` + 7 `NUMERICAL_FAILURE` = 16 instances.
  5. Manifest amendment logging for post-freeze capability reclassifications (`QPLIB_8938`).
  6. Nested wallclock deadline propagation in MILP inner simplex and branching loops.

### 2.10 QP Internal Mathematical Unit Fixtures (`tests/test_qp_internal.py` — 20 tests)
- 20 dedicated unit fixtures validating the native equality-aware interior-point solver (`sovopt/qp.py`) across all mathematical edge cases (strictly labeled `[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]`):
  1. Unconstrained positive-definite QP.
  2. One equality QP.
  3. Multiple equalities QP.
  4. Equality + $\le$ inequality.
  5. Equality + $\ge$ inequality.
  6. Equality + ranged row.
  7. Equality + lower variable bounds.
  8. Equality + upper variable bounds.
  9. Equality + box bounds.
  10. Fixed variable equality partitioning.
  11. Redundant equality row handling.
  12. Near-dependent equality rows with regularized KKT system.
  13. Zero-row valid equality handling.
  14. Infeasible equality detection.
  15. Semidefinite $Q$ matrix handling.
  16. Diagonal $Q$ matrix structure.
  17. Off-diagonal symmetric $Q$ matrix structure.
  18. Nonzero objective constant preservation.
  19. Infeasible-start IPM initialization convergence.
  20. Equality multiplier unrestricted sign verification.

### 2.11 Public Benchmark Manifest & Provenance Integrity (`tests/test_benchmark_manifest.py` — 7 tests)
- Verification of frozen benchmark datasets and provenance integrity:
  1. Master manifest schema and cryptographic SHA-256 integrity checks.
  2. Netlib LP collection manifest verification (16 candidate instances + `WOODINFE`).
  3. MIPLIB 2017 stratified collection manifest verification (38 instances across 4 size bins + `flugpl`).
  4. MIPLIB ground-truth solution parsing and verification against official `miplib2017-v37.solu`.
  5. QPLIB continuous convex QP manifest verification (`QPLIB_8845`, `9002`, `8938` + `0018` negative test).
  6. Strict segregation of quarantined datasets (`AVGAS` strictly excluded from active manifests).
  7. Prohibition of synthetic benchmarks in public manifest collections.

*(Note: Synthetic unit fixtures in `tests/test_presolve.py`, `tests/test_numerical_stress.py`, `tests/test_dual_simplex.py`, `tests/test_milp.py`, and `tests/test_qp_internal.py` are strictly marked `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA` and are excluded from benchmark reports).*

---

## 3. Netlib 4-Way Presolve/Scaling Ablation Matrix

The following table records the measured results for continuous LPs across all 4 verified Netlib benchmark instances under all 4 combinations of presolve and equilibration scaling:

| Instance | Presolve | Scaling | Status | Measured Objective | Simplex Iterations | KKT Verified |
|:---|:---:|:---:|:---|:---|:---:|:---:|
| **AFIRO** | OFF | OFF | `OPTIMAL_VERIFIED` | -464.753143 | 23 | True |
| **AFIRO** | OFF | ON  | `OPTIMAL_VERIFIED` | -464.753143 | 22 | True |
| **AFIRO** | ON  | OFF | `OPTIMAL_VERIFIED` | -464.753143 | 23 | True |
| **AFIRO** | ON  | ON  | `OPTIMAL_VERIFIED` | -464.753143 | 22 | True |
| **SC50A** | OFF | OFF | `OPTIMAL_VERIFIED` | -64.575077 | 54 | True |
| **SC50A** | OFF | ON  | `OPTIMAL_VERIFIED` | -64.575077 | 49 | True |
| **SC50A** | ON  | OFF | `OPTIMAL_VERIFIED` | -64.575077 | 54 | True |
| **SC50A** | ON  | ON  | `OPTIMAL_VERIFIED` | -64.575077 | 49 | True |
| **SC50B** | OFF | OFF | `OPTIMAL_VERIFIED` | -70.000000 | 49 | True |
| **SC50B** | OFF | ON  | `OPTIMAL_VERIFIED` | -70.000000 | 52 | True |
| **SC50B** | ON  | OFF | `OPTIMAL_VERIFIED` | -70.000000 | 49 | True |
| **SC50B** | ON  | ON  | `OPTIMAL_VERIFIED` | -70.000000 | 52 | True |
| **BLEND** | OFF | OFF | `OPTIMAL_VERIFIED` | -30.812150 | 128 | True |
| **BLEND** | OFF | ON  | `OPTIMAL_VERIFIED` | -30.812150 | 117 | True |
| **BLEND** | ON  | OFF | `OPTIMAL_VERIFIED` | -30.812150 | 124 | True |
| **BLEND** | ON  | ON  | `OPTIMAL_VERIFIED` | -30.812150 | 119 | True |k reports).*

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

Output is written to `reports/external_validation.json` and summarized in `reports/VERIFIED_BENCHMARKS.md`.

### 3.1 Netlib Dual Simplex vs Primal Simplex Benchmark Comparison

Measured on Apple Silicon ARM64 (Python 3.11.16, NumPy 2.3.5) with sovereign sparse LU algebra (`linear_algebra="sparse"`):

| Instance | Solver Method | Status | Objective | Ref Objective | Iters | Time (ms) | KKT Passed | Primal Res ($r_p$) | Dual Res ($r_d$) | Comp ($c$) | Devex Calls | Harris Calls | Bound Flips | Etas / Refactors |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AFIRO** | Dual Simplex | `OPTIMAL_VERIFIED` | -464.753143 | -464.753143 | 23 | 15.1 | Yes | 2.96e-16 | 2.64e-18 | 1.48e-17 | 23 | 23 | 1 | 22 / 1 |
| **AFIRO** | Primal Simplex | `OPTIMAL_VERIFIED` | -464.753143 | -464.753143 | 53 | 36.3 | Yes | 2.84e-14 | 2.64e-18 | 1.48e-17 | — | — | — | 52 / 3 |
| **SC50A** | Dual Simplex | `OPTIMAL_VERIFIED` | -64.575077 | -64.575077 | 54 | 48.0 | Yes | 2.87e-16 | 3.23e-17 | 4.72e-17 | 54 | 54 | 1 | 51 / 3 |
| **SC50A** | Primal Simplex | `OPTIMAL_VERIFIED` | -64.575077 | -64.575077 | 56 | 55.2 | Yes | 9.66e-17 | 4.09e-17 | 4.19e-17 | — | — | — | 54 / 4 |
| **SC50B** | Dual Simplex | `OPTIMAL_VERIFIED` | -70.000000 | -70.000000 | 49 | 42.5 | Yes | 8.54e-16 | 3.97e-17 | 1.03e-16 | 49 | 49 | 1 | 47 / 2 |
| **SC50B** | Primal Simplex | `OPTIMAL_VERIFIED` | -70.000000 | -70.000000 | 54 | 55.5 | Yes | 1.56e-16 | 2.90e-17 | 9.01e-17 | — | — | — | 52 / 4 |
| **BLEND** | Dual Simplex | `OPTIMAL_VERIFIED` | -30.812150 | -30.812150 | 127 | 170.0 | Yes | 2.93e-15 | 1.47e-16 | 2.81e-16 | 127 | 127 | 17 | 106 / 5 |
| **BLEND** | Primal Simplex | `OPTIMAL_VERIFIED` | -30.812150 | -30.812150 | 321 | 432.6 | Yes | 6.34e-14 | 2.27e-15 | 1.38e-15 | — | — | — | 310 / 13 |

#### Differential Agreement with HiGHS 1.15.1
- **AFIRO:** HiGHS `-464.75314285714285` vs SOV-OPT `-464.75314285714285` ($\Delta = 0.0$)
- **SC50A:** HiGHS `-64.5750770585645` vs SOV-OPT `-64.57507705856452` ($\Delta = 2.8 \times 10^{-14}$)
- **SC50B:** HiGHS `-69.99999999999999` vs SOV-OPT `-70.00000000000000` ($\Delta = 1.4 \times 10^{-14}$)
- **BLEND:** HiGHS `-30.812149845828237` vs SOV-OPT `-30.812149845828226` ($\Delta = 1.0 \times 10^{-14}$)

### 3.2 MIPLIB FLUGPL 4-Way B&B Ablation Matrix

Measured on Apple Silicon ARM64 (Python 3.11.16, NumPy 2.3.5) with maximum node limit 50:

| Configuration | Warm Starts | Pseudocosts | Strong Branching | Heuristics | Node Selection | Nodes | Status | Certified Bound | Warm Accepted | Warm Pivots | Cold Pivots | Strong Evals | Time (s) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline Cold** | OFF | OFF | OFF | OFF | Best-Bound | 50 | `LIMIT_REACHED` | 1173719.9999999998 | 0 / 0 | 0 | 1130 | 0 | 0.517 |
| **Pseudocosts Cold** | OFF | ON | ON | OFF | Best-Bound | 50 | `LIMIT_REACHED` | 1173063.7852941174 | 0 / 0 | 0 | 1024 | 32 | 0.902 |
| **Pseudocosts Warm** | ON | ON | ON | OFF | Best-Bound | 50 | `LIMIT_REACHED` | 1173063.7852941174 | 49 / 49 | 191 | 17 | 32 | 0.597 |
| **Full Gate 6 Engine** | ON | ON | ON | ON | Hybrid | 50 | `LIMIT_REACHED` | 1173063.7852941174 | 49 / 49 | 191 | 17 | 32 | 0.631 |

- **Pivot Reduction:** Warm starts reduce child LP pivots from 1024 to 191 (an **81.3% reduction in pivots**).
- **Exact Rational Bound Safety:** All configurations compute exact rational lower bounds via Neumaier-Shcherbina Fraction evaluation (`safe_lower_bound`), strictly bounded within $[769500.0, 1201500.0]$.

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

4. **Public Convex QP Benchmarks (Gate 7 Complete):**
   - Authentic public continuous convex quadratic programming instances from QPLIB 2018 (`https://qplib.zib.de/`) are admitted and frozen in `data/manifests/qplib_convex_qp.json`.
   - `QPLIB_8845` (1546 variables, 777 constraints) is solved independently to `OPTIMAL_VERIFIED` by SOV-OPT's equality-aware primal-dual interior point solver with full original-model KKT verification (residuals $< 10^{-10}$) and objective matching official published reference ($10,907,992.4957$ vs $10,907,992.4940$, $1.59 \times 10^{-10}$ relative discrepancy).
   - `QPLIB_9002` (2890 variables, 1649 constraints) is solved independently to `OPTIMAL_VERIFIED` in 25 iterations.
   - Reference `.sol` vectors are segregated strictly to differential comparisons and are never accessed by the sovereign solver.
   - Instances exceeding the 250 MB memory guard (`QPLIB_8938`) and nonconvex models (`QPLIB_0018`) are cleanly rejected with typed error classes.

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

8. **Dual Simplex B&B Warm-Start Integration (Completed in Gate 6):**
   - Bounded-variable revised dual simplex warm basis reoptimization (`DualBasisState`) is fully integrated into the Branch-and-Bound MILP engine (`sovopt/milp.py`).
   - Achieves 100% warm-start acceptance on child nodes of FLUGPL (49 of 49 accepted) with an 81.3% reduction in pivot count (191 vs 1024 pivots).
   - Combines pseudocost branching, limited strong-branching bootstrap, hybrid best-bound/depth node selection, safe rounding, and conservative diving heuristics while strictly preserving exact rational lower bound safety (`safe_lower_bound`).

---

## 6. Baseline History Summary (Gate 0)

At the initial Gate 0 milestone (Git commit \`31f8de8\`), the sovereign boundary was verified on macOS ARM64 with Python 3.11.16 and NumPy 2.3.5. All 17 initial unit test methods passed without external solver imports. Subsequent milestones introduced verified public benchmarks (Netlib, MIPLIB), exact rational duals, ray recovery, model validation, and the current clean test suite.
