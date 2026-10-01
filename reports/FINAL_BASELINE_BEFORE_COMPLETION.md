# SOV-OPT: Final Baseline Before Engineering Completion

**Date:** 2026-10-01  
**Baseline HEAD Commit:** `bad592015cea06c583136cbf90c039fde10bdbaa`  
**Problem Statement:** MRPL SIH PS 26119  
**Specification Document:** *Final Deep-Research Solution for MRPL PS 26119: A Verified Sovereign GPU-Accelerated LP/MILP/QP Solver Core*  

---

## 1. Baseline System & Hardware Environment

- **Python Version:** 3.11.16 (Clang 21.0.0, 64-bit)
- **NumPy Version:** 2.3.5
- **Operating System:** macOS Darwin (Release 25.6.0, macOS 26.6.2)
- **Architecture:** ARM64
- **Processor / CPU Model:** Apple M5 (24.00 GB unified RAM)
- **CUDA Hardware Availability:** `False` (Apple Silicon development environment; lacks physical NVIDIA GPU)
- **SOV-OPT Core Version:** 0.1.5
- **Unit Test Results:** 34 passed, 0 failed, 2 loopback network tests skipped in sandbox
- **Tracked Files in Checksum Manifest:** 86 verified in `SHA256SUMS.json`

---

## 2. Requirement Baseline Audit Matrix

| # | PDF Requirement | Current Implementation | Source File | Actual Execution Path | Current Test | Current Benchmark Evidence | Status | Current Limitation |
|---|---|---|---|---|---|---|---|---|
| 1 | **Sovereign Solver Core** | Pure NumPy & Python stdlib only in `sovopt/`; no imports of HiGHS, SCIP, CBC, OR-Tools, etc. | `sovopt/` | Internal modules only | `test_verified_real_instances` | Netlib AFIRO, SC50A, SC50B, BLEND; MIPLIB FLUGPL | **COMPLETE** | Core is in Python/NumPy; native compiled C/Rust core deferred. |
| 2 | **Independent Trust & Verification Layer** | Original-model KKT residual checks ($r_p, r_d, r_I$), exact rational Farkas certificates, and bounds | `sovopt/verify.py` | `verify()` called after every solve | `test_bad_candidate_validation` | Residuals recorded for all 5 verified benchmarks | **COMPLETE** | Floating-point KKT checks are numerical tests, not formal mathematical proofs. |
| 3 | **Primal Revised Simplex** | Two-phase primal simplex with dense LU factorization, partial pivoting, iterative refinement | `sovopt/simplex.py` | `solve_lp()` | `test_verified_real_instances` | Solves AFIRO, SC50A, SC50B, BLEND to $10^{-14}$ | **COMPLETE** | Dense factorization limits scale to $\le 1000$ rows. |
| 4 | **Sparse Linear Algebra & Markowitz** | Dense LU implementation in `sovopt/linalg.py`; no CSR/CSC basis factorization | `sovopt/linalg.py` | Dense `LU` | `test_lu_pivot_refinement_real_basis` | Netlib AFIRO/SC50A bases factored densely | **PARTIAL / GATE 3** | True sparse CSR/CSC Markowitz factorization not yet implemented. |
| 5 | **Bounded-Variable Revised Dual Simplex** | Primal simplex implemented; dual simplex listed as planned in ARCHITECTURE | `sovopt/simplex.py` | `solve_lp()` (primal) | `test_verified_real_instances` | Primal simplex only | **MISSING / GATE 4** | Dual simplex with Devex pricing not yet implemented. |
| 6 | **Exact Rational Basis Dual Engine** | `_exact_dual_from_basis` solves $B^T y = c_B$ in exact rational arithmetic (`fractions.Fraction`) | `sovopt/simplex.py` | Inverted during optimal solve | `test_exact_rational_lagrangian_bound` | Tested on MIPLIB FLUGPL LP relaxation | **COMPLETE** | Dense rational inversion slower on large bases. |
| 7 | **Exact Rational Farkas Certificate** | Checks $y \ge 0, y^T A \le 0, y^T b > 0$ in exact rational arithmetic | `sovopt/verify.py`, `sovopt/simplex.py` | Evaluated on Phase-I infeasibility | `test_infeasible_farkas_certificate_genuine` | Validated on genuine FLUGPL branch & infeasible twin | **COMPLETE** | Currently verified for LP simplex paths. |
| 8 | **Unbounded Ray Recovery** | Ray recovery in `postsolve_ray`; lacks explicit recession ray verification gate | `sovopt/simplex.py`, `sovopt/transforms.py` | Simplex Phase II unbounded | Regression test needed | Not exercised on benchmark suite (no unbounded instance in active suite) | **PARTIAL / GATE 2** | Must require independent original-model verifier acceptance. |
| 9 | **Conservative MILP Branch & Bound** | Serial B&B with Neumaier-Shcherbina rational Lagrangian bounds; safe leaf fathoming | `sovopt/milp.py` | `solve_milp()` | `test_milib_flugpl_solve_and_lower_bound`, `test_refinery_twin_milp_optimal_verified` | MIPLIB FLUGPL (bound certified), Twin MILP (verified optimal) | **COMPLETE** | Cold-start LPs; no pseudocosts or basis warm-starts yet. |
| 10 | **MILP Warm Starts & Advanced Branching** | Cold-start LP per node; most-fractional variable selection; no pseudocosts | `sovopt/milp.py` | Cold-start `solve_lp()` per node | `test_flugpl_honest_metadata` | FLUGPL 50 nodes limit | **PARTIAL / GATE 6** | Warm-starts and pseudocost branching needed for Gate 6. |
| 11 | **Convex Quadratic Programming (QP)** | Infeasible-start Mehrotra predictor-corrector interior point method; normal equations | `sovopt/qp.py` | `solve_qp()` | `test_refinery_twin_qp_kkt_verified` | Operational QP refinery twin ($r_p \le 10^{-16}, r_d \le 10^{-7}$) | **COMPLETE** | Dense normal equations; no authentic public QPLIB instance in active suite yet. |
| 12 | **Real QPLIB Benchmark Support** | Parser supports QPS `QUADOBJ`; no QPLIB instances downloaded or verified in `data/verified` | `sovopt/mps.py` | QPS parser exists | Synthetic models previously removed | Evidence gap disclosed in `data/CATALOGUE.md` | **MISSING / GATE 7** | Authentic convex QPLIB instances must be frozen and benchmarked. |
| 13 | **First-Order LP (PDHG CPU & CUDA)** | Primal-Dual Hybrid Gradient with diagonal scaling & restart; CPU SpMV & CUDA RawKernel | `sovopt/pdhg.py` | `solve_pdhg()` | `test_pdhg_cpu_convergence` | AFIRO solved to $10^{-7}$ on CPU | **COMPLETE** | CUDA execution requires NVIDIA hardware (unavailable on Apple Silicon). |
| 14 | **GPU Acceleration Validation** | CUDA source present; `gpu_executed` strictly `false` on Apple Silicon | `sovopt/pdhg.py` | CPU execution only | `test_pdhg_cpu_convergence` | Honest disclosure in all reports | **BLOCKED BY HARDWARE / GATE 9** | Physical NVIDIA GPU needed for measured speedup validation. |
| 15 | **Reversible Presolve & Scaling** | Geometric row scaling & variable bounds transformations; no column scaling or singleton reduction | `sovopt/transforms.py` | `transform_model()` | `test_variable_transformations_equiv` | Presolve scaling active on all simplex runs | **PARTIAL / GATE 5** | Presolve lacks column scaling, singleton rows, and bound propagation. |
| 16 | **Automatic Algorithm Dispatcher** | Inspects dimensions, sparsity, dynamic range, integrality, and QP matrix $Q$ | `sovopt/dispatcher.py` | `auto_dispatch()` | `TestAutoDispatcher` (3 tests) | Routes LP $	o$ simplex, MILP $	o$ B&B, QP $	o$ IPM | **COMPLETE** | Integrates with `--method auto` in CLI and core API. |
| 17 | **MRPL Refinery Planning Twin** | Unified multi-period model with LP, MILP, QP, and Infeasible variants | `sovopt/refinery_twin.py` | `build_refinery_twin()` | `TestRefineryPlanningTwin` (4 tests) | `scripts/demonstrate_refinery_twin.py` (5 steps) | **COMPLETE / PROVENANCE AUDIT NEEDED (GATE 1)** | Representative open-literature model; not proprietary MRPL production telemetry. |
| 18 | **CLI Numerical Trust Report** | Formatted report printing $r_p, r_d, r_I$, gap, certificate status, and basis | `sovopt/__main__.py` | `--report` | Tested via CLI execution | Formatted report output demonstrated | **COMPLETE** | Displays complete verification metrics. |
| 19 | **Real Public Benchmark Coverage** | 5 active datasets: Netlib AFIRO, SC50A, SC50B, BLEND; MIPLIB FLUGPL. AVGAS quarantined | `data/verified/`, `data/CATALOGUE.md` | `scripts/generate_reports.py` | `test_verified_real_instances` | Verified in `reports/VERIFIED_BENCHMARKS.md` | **PARTIAL / GATE 8** | Suite needs expansion to comprehensive Netlib/MIPLIB/QPLIB subsets. |
| 20 | **Differential External Validation** | Isolated subprocess worker (`scripts/baseline_worker.py`) using native HiGHS C++ | `scripts/baseline_worker.py` | Subprocess only | `TestDifferentialComparisonLogic` (8 tests) | 4 MATCH, 1 BOUND_ONLY against HiGHS 1.15.1 | **COMPLETE** | External solvers never called from solver core. |

---

## 3. Immediate Action Plan Across Gates

1. **Gate 1 (Provenance & Data Audit):**
   - Trace all parameters in `sovopt/refinery_twin.py` and produce `data/refinery/PROVENANCE_MATRIX.md`.
   - Formally declare Option B: "Representative open-literature refinery planning formulation" (do not call real MRPL telemetry).
   - Re-verify AFIRO, SC50A, SC50B, BLEND, FLUGPL hashes and sources. Maintain AVGAS quarantine.
2. **Gate 2 (Status Semantics & Certificate Correctness):**
   - Produce `docs/STATUS_SEMANTICS.md`.
   - Audit `UNBOUNDED_CERTIFIED` in `simplex.py` to ensure recession ray is postsolved and independently verified.
3. **Gate 3 (Sparse Linear Algebra & Markowitz):**
   - Implement CSR/CSC representation, sparse FTRAN/BTRAN, Markowitz threshold pivoting, and eta updates.
4. **Gate 4 (Bounded-Variable Revised Dual Simplex):**
   - Implement bounded-variable revised dual simplex with Devex pricing and Phase I/II dual feasibility.
5. **Gate 5 (Reversible Presolve & Column Scaling):**
   - Implement empty/singleton elimination, bound propagation, and column scaling with exact postsolve.
6. **Gate 6 (MILP Engine Upgrades):**
   - Implement basis warm starts, pseudocost branching, and incumbent propagation.
7. **Gate 7 (Real QPLIB Data):**
   - Ingest authentic public continuous convex QPLIB instances with cryptographic verification.
8. **Gate 8 (Benchmark Expansion):**
   - Expand Netlib LP, MIPLIB, and QPLIB coverage with immutable manifests.
9. **Gate 9 & 10 (GPU PDHG Hardening & Ablations):**
   - Prepare NVIDIA validation harness and run comprehensive feature ablations.
10. **Gate 11 & 12 (Claims Audit & Final Competition Evidence):**
    - Repos-wide audit for unverified claims; generate `reports/FINAL_COMPETITION_EVIDENCE.md`.
