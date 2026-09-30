# Comprehensive Master Audit & Implementation Report — SOV-OPT MRPL PS 26119

**Audit Date:** 2026-10-01  
**Repository:** `sg721642/sov-opt-mrpl-26119`  
**Environment:** Apple Silicon ARM64 macOS, Python 3.11.16, NumPy 2.3.5  
**Solver Version:** SOV-OPT 0.1.2  
**Core Dependencies:** NumPy and Python standard library only (strictly sovereign core)  

---

## 1. Executive Summary

This master audit establishes the corrected, validated, and source-backed status of the SOV-OPT repository for MRPL SIH Problem Statement 26119. All prior numerical defects, contradictory claims, and synthetic fixtures have been investigated, resolved, verified, and cleaned.

### Key Audit Findings & Resolutions

1. **Sovereign Core Architecture Enforced:**
   - The core solver (`sovopt/`) and application server (`server.py`) import only `numpy` and the Python standard library.
   - External solvers (HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX, cuOpt) are strictly prohibited in the core solver.
   - External benchmarking is quarantined to an isolated subprocess worker (`scripts/baseline_worker.py`), which features a completely standalone MPS parser that does not import `sovopt`.

2. **Real-Data-Only Test Suite:**
   - All synthetic optimization fixtures (`test_box_and_unconstrained`, `test_nonconvex_and_miqp_rejected`) have been completely excised from active tests.
   - Diagnostic probes in `test_bad_candidate_validation` are explicitly labeled as unit verification of the independent verifier (`verify.py`) using perturbed candidate vectors on the genuine historical AVGAS model.
   - Codebase scan confirms zero synthetic optimization models remain in active tests or benchmarks.

3. **Rigorous Variable Transformation Validation:**
   - Validated standard-form variable transformations using a mathematically sound invertible affine change of variables ( = D \tilde{x} + s$ with  > 0$) on real Netlib AFIRO.
   - Original-model recovery achieves machine precision: primal residual .22 \times 10^{-16}$, dual residual .11 \times 10^{-17}$, KKT status `OPTIMAL_VERIFIED`, objective matching reference 569X464.75314285714285$.
   - Bound dual scaling law verified: $\tilde{y}^* = y^*$, {\text{bound}} = D^{-1} \tilde{z}_{\text{bound}}$.
   - Handled edge cases: all-fixed variables ({\text{trans}} = 0$) evaluates row feasibility directly without shape errors (`np.zeros((len(rows), 0))`), returning `OPTIMAL_VERIFIED` or `INFEASIBLE_CERTIFIED`; transformed unconstrained systems ({\text{total}} = 0$) compute strictly feasible base points within 0$ and recession rays (^T d < 0$).

4. **MILP Exact Rational Bound Accounting:**
   - Eliminated the `[rootlb]` pinning bug from `all_bounds` in `sovopt/milp.py`. The global lower bound now faithfully tracks the minimum of open branch nodes and valid terminal evidence.
   - Corrected objective offset handling: `model.obj_offset` is incorporated in exact rational arithmetic (`Fraction`) *before* conservative downward float rounding: `downward_float(global_lower + offset_F)`.
   - Clarified that numerical incumbent feasibility is distinct from exact rational lower bounds.
   - Updated MIPLIB FLUGPL test to accept verified improvements while enforcing bounds and limits (.0 \le \text{best\_bound} \le 1201500.0$).

5. **Objective Conventions & Numerical Verification Rigor:**
   - Unified internal canonical minimization convention: QPS parser sets  = -Q$ when `maximize=True`, eliminating double-negation in `solve_qp`.
   - Corrected KKT relative scaling in `sovopt/verify.py`: eliminated `model.obj_offset` from `comp_denom` and `gap_denom`, ensuring KKT residuals are invariant to arbitrary constant objective shifts.
   - Documented eigenvalue / PSD inspection in `sovopt/linalg.py` and `sovopt/qp.py` as a floating-point numerical check subject to rounding errors, not an exact mathematical certificate of positive semidefiniteness.
   - Lossless exact Farkas certificate export/reload in JSON using exact string Fractions, verified on a real infeasible subproblem of FLUGPL.

6. **Independent References, Provenance & Honest Disclosures:**
   - Published reference values, sources, and precision are tracked independently from solver outputs.
   - Exact Netlib BLEND discrepancy recorded: published reference `-3.0812149846E+01` (11 significant digits from 1988 MINOS 5.3 report) vs SOV-OPT computed `-30.812149845828237` (difference 0.71763 \times 10^{-10} \approx 1.72 \times 10^{-10}$).
   - Explicit disclosures added across the documentation, catalogue, manifest, and web dashboard: *"No authorized MRPL dataset is available in this project."*
   - Honest empty states declared for proprietary refinery production matrices and industrial convex QP datasets.

---

## 2. Active Verified Benchmarks Verification Table

All results generated natively on Apple Silicon ARM64 CPU with `gpu_executed: false` using SOV-OPT 0.1.2.

| Instance | Class | Category | Dimensions | SOV-OPT Status | SOV-OPT Objective | Published Reference | Reference Discrepancy | Primal Residual | Stationarity | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | Academic solver benchmark | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000000000** | -7.75 (Symonds 1955) | 0.0 | 6.06e-17 | 0.00e+00 | 8.8 ms |
| **AFIRO** | LP | Application benchmark | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753142857143** | -464.753142857 (Netlib / MINOS 5.3) | < 1e-12 | 1.42e-14 | 1.72e-17 | 31.5 ms |
| **SC50A** | LP | Application benchmark | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077058564** | -64.575077058 (Netlib / MINOS 5.3) | < 1e-11 | 5.37e-16 | 4.09e-17 | 35.7 ms |
| **SC50B** | LP | Application benchmark | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000000000** | -70.000000000 (Netlib / MINOS 5.3) | 0.0 | 2.49e-16 | 3.97e-17 | 30.9 ms |
| **BLEND** | LP | Application benchmark | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812149845828** | -30.812149846 (Netlib / MINOS 5.3) | +1.72e-10 | 1.78e-15 | 1.23e-16 | 828.2 ms |
| **AVGAS (PDHG)** | LP | First-order CPU route | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000085449** | -7.75 (Symonds 1955) | 1.1e-7 | 1.84e-8 | 2.10e-8 | 6.1 ms |
| **FLUGPL** | MILP | Application benchmark | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **1173645.0** | 1201500 (MIPLIB 1.0) | N/A (Node limit: 50) | N/A | N/A | 1042.8 ms |

---

## 2.1. Independent Differential Verification (Native HiGHS 1.15.1)

All 6 genuine instances were solved using the native C++ HiGHS 1.15.1 solver via `highspy` in an isolated external process (completely separated from the sovereign solver core; record preserved in `reports/external_validation.json`):

| Instance | Input MPS File | HiGHS C++ Status | HiGHS Objective | SOV-OPT Objective / Bound | Discrepancy (SOV-OPT vs HiGHS) | Match Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | `data/verified/avgas.mps` | `HighsModelStatus.kOptimal` | -7.750000 | -7.750000 | 0.0 | `EXACT_MATCH` |
| **AFIRO** | `data/verified/afiro.mps` | `HighsModelStatus.kOptimal` | -464.753143 | -464.753143 | 5.68e-14 | `MATCH (< 1e-12)` |
| **SC50A** | `data/verified/sc50a.mps` | `HighsModelStatus.kOptimal` | -64.575077 | -64.575077 | 0.0 | `EXACT_MATCH` |
| **SC50B** | `data/verified/sc50b.mps` | `HighsModelStatus.kOptimal` | -70.000000 | -70.000000 | 0.0 | `EXACT_MATCH` |
| **BLEND** | `data/verified/blend.mps` | `HighsModelStatus.kOptimal` | -30.812150 | -30.812150 | 0.0 | `EXACT_MATCH` |
| **FLUGPL** | `data/verified/flugpl.mps` | `HighsModelStatus.kOptimal` | 1201500.000000 | Bound: 1173645.0 | Safe lower bound <= 1201500 | `VALIDATED_BOUND` |

Key takeaway: Netlib BLEND objective `-30.812149845828237` matches native C++ HiGHS 1.15.1 to machine precision ($0.0$ difference at double precision), proving that the discrepancy against the 1988 Netlib README (`-3.0812149846E+01`) is due entirely to 11-digit text truncation in historical MINOS 5.3 output, not a solver defect.

---

## 3. Detailed Audit Area Analyses

### Area 1: Real-Data-Only Test Suite
- **Issue:** Previous test suite contained synthetic optimization fixtures (`test_box_and_unconstrained` and `test_nonconvex_and_miqp_rejected`) with handmade numbers.
- **Resolution:** Removed both synthetic fixtures. Labeled `test_bad_candidate_validation` explicitly as a verifier unit test using perturbed candidate vectors on the real AVGAS model to test KKT and Farkas acceptance/rejection paths.
- **Verification:** Ran codebase grep across `tests/` and `sovopt/`. Verified 0 synthetic optimization fixtures in active tests. All 12 active tests pass deterministically.

### Area 2: Transformation Validation & Edge Case Robustness
- **Issue:** Previous affine transformation test manually changed bounds on AFIRO, inadvertently altering the original problem. Also, {\text{trans}} = 0$ caused array reshaping errors, and {\text{total}} = 0$ unconstrained cases lacked strictly feasible base point guarantees.
- **Resolution:**
  - Constructed an invertible affine transformation  = D \tilde{x} + s$ with  > 0, s \in \mathbb{R}^n$, scaling objective {\text{trans}} = D c$, matrix {\text{trans}} = A D$, and bounds {\text{trans}} = D^{-1}(l - s), u_{\text{trans}} = D^{-1}(u - s)$.
  - In postsolve recovery, primal is recovered via  = D \tilde{x} + s$, row duals $\tilde{y} = y$, and bound duals {\text{bound}} = D^{-1} \tilde{z}_{\text{bound}}$.
  - Primal residual on original model: .22 \times 10^{-16}$. Dual residual: .11 \times 10^{-17}$. Status: `OPTIMAL_VERIFIED`.
  - In `sovopt/transforms.py`, when {\text{trans}} = 0$, arrays are shaped as `np.zeros((len(rows), 0))` instead of invalid `reshape((-1, 0))`.
  - In `sovopt/simplex.py`, all-fixed systems evaluate row constraints against 0$ returning `OPTIMAL_VERIFIED` or `INFEASIBLE_CERTIFIED`.
  - Transformed unconstrained systems ({\text{total}} = 0$) compute strictly feasible base points within 0$ and recession rays with ^T d < 0$.
- **Verification:** `test_variable_transformations_equiv` passes with machine precision.

### Area 3: MILP Bound Accounting & Branch-and-Bound Correctness
- **Issue:** `all_bounds` in `sovopt/milp.py` unconditionally pinned the root lower bound `[rootlb]`, preventing lower bound progression if child nodes improved. Objective offsets were added to float bounds without exact arithmetic. In addition, floating-point rounding errors in dual calculation on FLUGPL (e.g. $-3.33 \times 10^{-14}$ residual on infinite upper bound variable) caused `safe_lower_bound` to return `None` and fall back to crude box bounds.
- **Resolution:**
  - Removed `[rootlb]` pinning. The lower bound is computed as the minimum of open branch nodes and valid terminal leaves.
  - Implemented `_exact_dual_from_basis` using `_exact_solve_BT` in exact rational arithmetic (`Fraction`), ensuring reduced costs on basic variables are mathematically zero ($0/1$).
  - With exact rational duals, `safe_lower_bound` evaluates reliably on every branch node, advancing the conservative lower bound on MIPLIB FLUGPL from $769500.0$ to **$1173645.0$** at 50 nodes (and $1176210.0$ at 150 nodes).
  - Added `model.obj_offset` in exact rational arithmetic (`Fraction`) prior to conservative downward rounding via `downward_float(global_lower + offset_F)`.
  - Updated FLUGPL bounds test to accept verified improvements while verifying bounds remain strictly $\le 1201500.0$.
- **Verification:** `test_milib_flugpl_solve_and_lower_bound` passes, verifying valid bounds and honest `LIMIT_REACHED` status.

### Area 4: Objective Conventions & Verification Rigor
- **Issue:** `solve_qp` negated $ and $ upon entry and then negated $ again, creating confusing double-negation. `verify.py` included `model.obj_offset` in KKT denominator scaling. Farkas certificate export was lossy.
- **Resolution:**
  - Unified canonical minimization: QPS parser sets  = -Q$ on `MAX`. `solve_qp` works natively in minimization without double-negation.
  - Corrected KKT denominators in `verify.py` to `scale_obj = 1.0 + abs(raw_obj)`, making KKT invariant under constant objective shifts.
  - Clarified that eigenvalue check in `sovopt/linalg.py` is a floating-point numerical check.
  - Implemented exact rational string serialization and lossless JSON round-trip export/reload for Farkas certificates.
- **Verification:** `test_infeasible_farkas_certificate_genuine` verifies exact Farkas export, reload, and mathematical re-verification.

### Area 5: Independent References & Provenance Tracking
- **Issue:** Solver outputs and reference values were blended in earlier summaries. Netlib BLEND discrepancy was rounded off without explanation.
- **Resolution:**
  - Separate published references, literature citations, and reporting precision.
  - Detailed BLEND discrepancy: published reference is `-3.0812149846E+01` (11 digits, MINOS 5.3 1988), SOV-OPT calculates `-30.812149845828237`. The difference is 0.71763 \times 10^{-10}$, caused by 11-digit truncation in the historical Netlib documentation.
  - Explicitly added "No authorized MRPL dataset is available in this project" to all documentation and the web dashboard.
  - Standalone MPS parser implemented in `scripts/baseline_worker.py`.
- **Verification:** All benchmark and catalogue files updated with exact discrepancy analysis.

### Area 6: Evidence Regeneration & Git Cleanup
- **Issue:** Reports and results needed programmatic regeneration with accurate UTC timestamps and synchronized versions.
- **Resolution:**
  - All local validation JSON files, benchmark reports, and manifests generated directly via live runs on genuine instances.
  - Version bumped to 0.1.2 across `pyproject.toml`, `sovopt/__init__.py`, `server.py`, `web/index.html`, and manifests.
  - Cleaned all synthetic files and unnecessary artifacts from git tracking.
- **Verification:** Full test suite passes; Git working tree clean after staging.

---

## 4. Disclosed Exclusions & Honest Empty States

1. **Proprietary MRPL Refinery Production Data (Empty State):**
   - Confidential internal refinery linear programming models (crude assays, distillation cuts, unit yield vectors) are trade secrets not in the public domain.
   - Fictional refinery numbers are strictly prohibited. SOV-OPT provides documented historical petroleum blending instances (`AVGAS` and `BLEND`) instead.
   - Disclosure: *"No authorized MRPL dataset is available in this project."*

2. **Industrial Convex QP Data (Empty State):**
   - Toy models (`qp_example.qps`) have been removed from the active benchmark suite.
   - The QP predictor-corrector implementation (`sovopt/qp.py`) remains available and mathematically verified, but benchmarks will be added only upon public release of genuine industrial QP datasets.

---

## 5. Hardware Disclosures

- All computations executed natively on Apple Silicon ARM64 CPU.
- `gpu_executed` is `false` in all audit records.
- CUDA acceleration is not available on Apple Silicon; no GPU speedup claims are made.
- First-order CPU PDHG solver is slower than direct revised simplex on small LP instances; this is reported honestly.
