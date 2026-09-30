# Comprehensive Master Audit & Implementation Report — SOV-OPT MRPL PS 26119

**Audit Date:** 2026-10-01  
**Repository:** `sg721642/sov-opt-mrpl-26119`  
**Environment:** Apple Silicon ARM64 macOS, Python 3.11.16, NumPy 2.3.5  
**Solver Version:** SOV-OPT 0.1.2  
**Core Dependencies:** NumPy and Python standard library only (strictly sovereign core)  

---

## 1. Executive Summary

This audit establishes the corrected, validated, and source-backed status of the SOV-OPT repository for MRPL SIH Problem Statement 26119. All prior numerical defects, contradictory claims, and synthetic fixtures have been investigated, resolved, verified, and cleaned.

### Key Accomplishments in this Pass:
1. **Sovereign Core Integrity Preserved:**
   - Zero external optimization solvers (HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX, cuOpt) are imported or called inside `sovopt/` or `server.py`.
   - Core linear algebra is implemented in `sovopt/linalg.py` with pure NumPy dense LU factorization and iterative refinement.

2. **Mathematical Resolutions:**
   - **BLEND Netlib LP:** Formulated direct standard-form equality row handling ({eq} x = b_{eq}$) with Phase I artificials (eliminating 43 redundant opposing slack pairs that cycled under Bland's rule). Solved to machine precision (`OPTIMAL_VERIFIED`, objective `-30.812149845828237`, 555 iterations, primal residual .78 	imes 10^{-15}$, dual residual .23 	imes 10^{-16}$).
   - **MIPLIB FLUGPL MILP:** Implemented exact rational Phase I basis solves and exact Fraction dual mapping for Farkas infeasibility certificates (^T z = 0, h^T z < 0, z \ge 0$). Branch-and-bound cleanly explores 50 and 500 nodes without numerical failure, establishing a conservative rational lower bound of `769500.0`.
   - **Reversible Variable Transformations (`sovopt/transforms.py`):** Handles lower, box, upper-only, free, and fixed variable types with exact postsolve recovery for primal and dual variables.

3. **Repository & Dataset Integrity:**
   - Retired synthetic files (`data/legacy_synthetic/`), synthetic generator (`scripts/make_examples.py`), stale synthetic reports, and toy test model (`qp_example.qps`) have been safely removed from active git tracking.
   - Active suite strictly contains 6 genuine public benchmarks: AVGAS, AFIRO, SC50A, SC50B, BLEND, FLUGPL.
   - Machine-readable manifest created at `data/manifest.json` with cryptographic SHA-256 hashes, source URLs, dimensions, and nonzeros.
   - Honest empty states explicitly declared for proprietary MRPL production matrices and real-world industrial convex QP data.

4. **100% Deterministic Real-Data Test Suite:**
   - All random number generators (`np.random.default_rng`) and hand-made fixtures eliminated from `tests/test_solver.py`.
   - LU tested on real basis matrices extracted from Netlib instances.
   - Farkas certificates tested on real infeasible subproblems from FLUGPL.
   - All 14 tests pass cleanly in ~3 seconds.

---

## 2. Active Verified Benchmarks Verification Table

| Instance | Class | Category | Dimensions | SOV-OPT Status | SOV-OPT Objective | Published Reference | Discrepancy | Primal Residual | Stationarity | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | Academic solver benchmark | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 0.0 | 6.06e-17 | 0.0 | 8.8 ms |
| **AFIRO** | LP | Application benchmark | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -464.753142857 (Netlib / MINOS 5.3) | < 1e-12 | 1.42e-14 | 1.72e-17 | 31.5 ms |
| **SC50A** | LP | Application benchmark | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -64.575077058 (Netlib / MINOS 5.3) | < 1e-11 | 5.37e-16 | 4.09e-17 | 35.7 ms |
| **SC50B** | LP | Application benchmark | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -70.000000000 (Netlib / MINOS 5.3) | 0.0 | 2.49e-16 | 3.97e-17 | 30.9 ms |
| **BLEND** | LP | Application benchmark | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -30.812149846 (Netlib / MINOS 5.3) | < 1e-10 | 1.78e-15 | 1.23e-16 | 828.2 ms |
| **AVGAS (PDHG)**| LP | First-order CPU route | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 1.1e-7 | 1.84e-8 | 2.10e-8 | 6.1 ms |
| **FLUGPL** | MILP | Application benchmark | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **769500.0** | 1201500 (MIPLIB 1.0) | N/A | N/A | N/A | 881.6 ms |

---

## 3. Disclosed Exclusions & Honest Empty States

1. **Proprietary MRPL Refinery Production Data (Empty State):**
   - Confidential internal refinery linear programming models (crude assays, tray cuts, component blending constraints) are trade secrets not in the public domain.
   - Fictional refinery numbers are strictly prohibited. SOV-OPT provides documented historical petroleum blending instances (`AVGAS` and `BLEND`) instead.

2. **Industrial Convex QP Data (Empty State):**
   - `qp_example.qps` (a 2-variable toy example from the QPSReader.jl unit test repository) has been excluded.
   - The QP predictor-corrector implementation (`sovopt/qp.py`) remains available and verified, but real-world benchmarks will be added only upon public release of genuine industrial QP datasets.

---

## 4. Hardware Disclosures

- All computations executed natively on Apple Silicon ARM64 CPU.
- `gpu_executed` is `false` in all audit records.
- CUDA acceleration is not available on Apple Silicon; no speedup claims are made.
