# Implementation & Validation Status — SOV-OPT MRPL PS 26119

**Date:** 2026-10-01  
**Repository:** https://github.com/sg721642/sov-opt-mrpl-26119 (Private)  
**Latest Git Commit SHA:** Pushed to `main` (see Git log)  
**Environment:** macOS Apple Silicon ARM64, Python 3.11.16, NumPy 2.3.5  
**Solver Version:** 0.1.2  

---

## 1. Roadmap Gates Status (from `docs/04_IMPLEMENTATION_PLAN.md`)

| Gate | Title | Status | Evidence |
|:---|:---|:---:|:---|
| **Gate 0** | Establish a reproducible starting point | **SATISFIED** | All unit tests pass; baseline established and committed in initial Git commit `31f8de8`. |
| **Gate 1** | Broaden mathematical coverage | **SATISFIED** | Supported infinite/unbounded variables ( \ge 0, x \le \infty$), maximization objective sense, objective offsets from RHS N-row, continuation lines in fixed/free MPS, and `QUADOBJ` in QPS. Tested on AFIRO, SC50A, SC50B, AVGAS, BLEND. |
| **Gate 2** | Build real sparse numerical infrastructure | *NOT IMPLEMENTED* | Solver core remains dense LU factorization with iterative refinement. Dense size limits (250 variables / 1000 rows) are strictly enforced. Instances exceeding limits report honest `LIMIT_REACHED` or `NUMERICAL_FAILURE`. |
| **Gate 3** | Implement robust dual simplex | *NOT IMPLEMENTED* | Primal revised simplex remains the implemented algorithm. No dual simplex or Devex pricing has been claimed. |
| **Gate 4** | Add reversible presolve and scaling | **SATISFIED (Variable Transforms)** | Reversible variable transformations (`sovopt/transforms.py`) handling box, lower, upper-only, free, and fixed variables with exact primal and dual recovery. Tested via invertible affine change of variables ( = D 	ilde{x} + s$) on AFIRO to machine precision (.22 	imes 10^{-16}$ primal, .11 	imes 10^{-17}$ dual). |
| **Gate 5** | Improve MILP without weakening bounds | **SATISFIED** | Conservative rational Lagrangian bounds implemented with exact rational basis dual calculations; exact rational Phase I basis solves and exact Farkas certificate generation. Clean branch-and-bound exploration of MIPLIB FLUGPL to `LIMIT_REACHED` advancing safe lower bound from root to 1173645.0 at 50 nodes without numerical failure. |
| **Gate 6** | Harden convex QP | *PARTIAL* | Infeasible-start Mehrotra predictor-corrector QP verified on PSD quadratic objectives with general  \succ 0$. Numerical eigenvalue inspection documented as floating-point check. Toy model excluded from active benchmarks pending genuine industrial QP data. |
| **Gate 7** | Validate actual GPU execution | *UNAVAILABLE ON MAC* | Apple Silicon hardware has no NVIDIA CUDA capability. `gpu_executed: false` is reported on all CPU runs; no GPU speedup is claimed. |

---

## 2. Tested Datasets and Measured Results

| Dataset | Class | Source | Result | Measured Objective | Published Reference | Discrepancy |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | Symonds (1955) Refinery Blending | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 | 0.0 |
| **AFIRO** | LP | Netlib / Saunders Stanford SOL | `OPTIMAL_VERIFIED` | **-464.753143** | -464.753142857 | < 1e-12 |
| **SC50A** | LP | Netlib Staircase Model | `OPTIMAL_VERIFIED` | **-64.575077** | -64.575077058 | < 1e-11 |
| **SC50B** | LP | Netlib Staircase Model | `OPTIMAL_VERIFIED` | **-70.000000** | -70.000000000 | 0.0 |
| **BLEND** | LP | Netlib Blending LP | `OPTIMAL_VERIFIED` | **-30.812150** | -30.812149846 | +1.72e-10 |
| **FLUGPL** | MILP | MIPLIB 1.0 (Wagner / Cray) | `LIMIT_REACHED` | Bound: **1173645.0** | 1201500 | N/A (Node limit: 50) |

---

## 3. Synthetic Content Disposition

- **Retired Files:** `refinery_lp.json`, `refinery_milp.json`, `refinery_qp.json`, `tiny.mps`, `scripts/make_examples.py`, and synthetic test fixtures (`test_box_and_unconstrained`, `test_nonconvex_and_miqp_rejected`).
- **Current Location in History:** Archived in initial Git commit `31f8de8` and subsequent git history.
- **Active Demo & Tests:** Completely replaced with verified genuine instances (`data/verified/` and `examples/`). Active test suite (`tests/test_solver.py`, `tests/test_server.py`) uses 100% genuine benchmark models, real basis matrices, and real infeasible branches. 12 of 12 tests pass deterministically.

---

## 4. Remaining Unsupported Features & Blockers

- **Sparse LU / Markowitz Pivoting:** Needed for larger problems (>250 variables) or degenerate high-dimensional bases.
- **Dual Simplex:** Phase II dual simplex algorithm for re-optimization in branch-and-bound.
- **MRPL Production Data:** Confidential internal MRPL refinery models are not in the public domain. Notice declared: *"No authorized MRPL dataset is available in this project."* Authentic public benchmark AVGAS serves as the historical petroleum blending reference.
- **CUDA Acceleration:** Permanently unavailable on macOS Apple Silicon. Requires NVIDIA hardware and CuPy for execution.
