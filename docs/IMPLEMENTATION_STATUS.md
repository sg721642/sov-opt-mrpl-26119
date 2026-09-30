# Implementation & Validation Status — SOV-OPT MRPL PS 26119

**Date:** 2026-10-01  
**Repository:** https://github.com/sg721642/sov-opt-mrpl-26119 (Private)  
**Latest Git Commit SHA:** Pushed to `main` (see Git log)  
**Environment:** macOS Apple Silicon ARM64, Python 3.11.16, NumPy 2.3.5

---

## 1. Roadmap Gates Status (from `docs/04_IMPLEMENTATION_PLAN.md`)

| Gate | Title | Status | Evidence |
|:---|:---|:---:|:---|
| **Gate 0** | Establish a reproducible starting point | **SATISFIED** | All 18 unit tests pass; baseline established and committed in initial Git commit `31f8de8`. |
| **Gate 1** | Broaden mathematical coverage | **SATISFIED** | Supported infinite/unbounded variables ($x \ge 0, x \le \infty$), maximization objective sense, objective offsets from RHS N-row, continuation lines in fixed/free MPS, and `QUADOBJ` in QPS. Tested on AFIRO, SC50A, SC50B, AVGAS, QP_EXAMPLE. |
| **Gate 2** | Build real sparse numerical infrastructure | *NOT IMPLEMENTED* | Solver core remains dense LU factorization. Dense size limits (250 variables / 1000 rows) are strictly enforced. Instances exceeding limits or requiring sparse pivoting (like BLEND) report honest `NUMERICAL_FAILURE`. |
| **Gate 3** | Implement robust dual simplex | *NOT IMPLEMENTED* | Primal revised simplex remains the implemented algorithm. No dual simplex or Devex pricing has been claimed. |
| **Gate 4** | Add reversible presolve and scaling | *PARTIAL* | Diagonal row equilibrating and variable shifting implemented; presolve reductions (singleton, fixed-variable elimination) remain planned. |
| **Gate 5** | Improve MILP without weakening bounds | *PARTIAL* | Conservative rational Lagrangian bounds implemented; branch-and-bound tested on FLUGPL (MIPLIB). Failure paths preserve honest `NUMERICAL_FAILURE` when Farkas cert cannot be established. |
| **Gate 6** | Harden convex QP | *PARTIAL* | Infeasible-start Mehrotra predictor-corrector QP tested on PSD quadratic objectives with general $Q \succ 0$ (`qp_example.qps`), verified against analytical KKT optimum. |
| **Gate 7** | Validate actual GPU execution | *UNAVAILABLE ON MAC* | Apple Silicon hardware has no NVIDIA CUDA capability. `gpu_executed: false` is reported on all CPU runs; no GPU speedup is claimed. |

---

## 2. Tested Datasets and Measured Results

| Dataset | Class | Source | Result | Measured Objective | Published Reference | Discrepancy |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | Symonds (1955) Refinery Blending | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 | 0.0 |
| **AFIRO** | LP | Netlib / Saunders Stanford SOL | `OPTIMAL_VERIFIED` | **-464.753143** | -464.753142857 | < 1e-12 |
| **SC50A** | LP | Netlib Staircase Model | `OPTIMAL_VERIFIED` | **-64.575077** | -64.575077058 | < 1e-11 |
| **SC50B** | LP | Netlib Staircase Model | `OPTIMAL_VERIFIED` | **-70.000000** | -70.000000000 | 0.0 |
| **QP_EXAMPLE**| QP | QPSReader Test Suite | `OPTIMAL_VERIFIED` | **8.371875** | 8.371875 (Analytical) | 3.6e-9 |
| **FLUGPL** | MILP | MIPLIB 1.0 (Wagner / Cray) | `NUMERICAL_FAILURE` | Bound: 769500 | 1201500 | N/A (safe halt) |
| **BLEND** | LP | Netlib (Murtagh) | `NUMERICAL_FAILURE` | None | -30.81215 | N/A (singular pivot) |

---

## 3. Synthetic Content Disposition

- **Retired Files:** `refinery_lp.json`, `refinery_milp.json`, `refinery_qp.json`, `tiny.mps`, and `scripts/make_examples.py`.
- **Current Location in History:** Archived in initial Git commit `31f8de8` and archived under `data/legacy_synthetic/` with an explicit disclaimer in `data/legacy_synthetic/PROVENANCE.md`.
- **Active Demo & Tests:** Completely replaced with verified instances (`data/verified/` and `examples/`). The feed-cost multiplier slider and fabricated refinery numbers have been removed from the active web dashboard and test suite.

---

## 4. Remaining Unsupported Features & Blockers

- **Sparse LU / Markowitz Pivoting:** Needed for larger problems (>250 variables) or degenerate bases (e.g. BLEND).
- **MRPL Production Data:** MRPL operational LP matrices are proprietary internal refinery data and not publicly available. Authentic public benchmark AVGAS serves as the petroleum industry reference.
- **CUDA Acceleration:** Permanently unavailable on macOS Apple Silicon. Requires NVIDIA hardware and CuPy for execution.
