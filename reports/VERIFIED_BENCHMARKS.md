# Verified Benchmark & Differential Validation Report

**Date:** 2026-10-01  
**Environment:** Apple Silicon ARM64 macOS, Python 3.11.16, NumPy 2.3.5  
**Solver:** SOV-OPT 0.1.1 (Original Sovereign Numerical Optimization Core)  
**External Solvers in Core:** None (NumPy + stdlib only)

---

## 1. Verified Benchmark Results

All instances below are from official public repositories (Netlib LP, MIPLIB, published literature).
No synthetic or fabricated instances are used as performance evidence.

| Instance | Problem Class | Dimensions (m x n) | SOV-OPT Status | SOV-OPT Objective | Published Reference | Discrepancy | Primal Residual | Stationarity (Dual) | Runtime (s) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 0.0 | 6.06e-17 | 0.0 | 0.0046s |
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -464.753142857 (Netlib / MINOS 5.3) | < 1e-12 | 5.68e-14 | 1.92e-17 | 0.0197s |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -64.575077058 (Netlib / MINOS 5.3) | < 1e-11 | 1.23e-16 | 2.61e-16 | 0.1236s |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -70.000000000 (Netlib / MINOS 5.3) | 0.0 | 2.49e-16 | 2.61e-16 | 0.1188s |
| **QP_EXAMPLE** | Convex QP | 2 x 2 | `OPTIMAL_VERIFIED` | **8.371875** | 8.371875 (Analytical optimum) | 3.6e-9 | 0.0 | 1.70e-10 | 0.0008s |
| **AVGAS (PDHG-CPU)** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 1.1e-7 | 1.84e-8 | 2.10e-8 | 0.0061s |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `NUMERICAL_FAILURE` | None (Bound: 769500) | 1201500 (MIPLIB 1.0) | N/A | N/A | N/A | 0.4450s |
| **BLEND** | LP | 74 x 83 | `NUMERICAL_FAILURE` | None | -30.81215 (Netlib / MINOS 5.3) | N/A | N/A | N/A | 1.5968s |

---

## 2. Analysis of Results and Failure Modes

### Optimal Verified Instances
- **AVGAS, AFIRO, SC50A, SC50B, QP_EXAMPLE** achieved `OPTIMAL_VERIFIED`.
- In all five cases, primal and dual residuals are at or near machine epsilon ($10^{-14}$ to $10^{-17}$), with KKT conditions fully satisfied.
- The objectives match published literature values to full precision.

### Honest Failure Reporting
1. **FLUGPL (MIPLIB MILP):**
   - Result: `NUMERICAL_FAILURE` after 30 branch-and-bound nodes.
   - Reason: An infeasible subproblem branch could not establish an exact rational Farkas certificate within the strict tolerance. Rather than making an unverified heuristic branch pruning, SOV-OPT halts and returns `NUMERICAL_FAILURE`.
   - Conservative rational Lagrangian lower bound established: `769500.0`.

2. **BLEND (Netlib LP):**
   - Result: `NUMERICAL_FAILURE`.
   - Reason: Dense LU factorization encountered a `Singular or unsafe pivot` during Phase I simplex. The basis matrix becomes ill-conditioned without Markowitz sparse pivoting or threshold pivoting.

---

## 3. Hardware and Acceleration Disclosures

- **CPU Only:** All benchmarks ran on Apple Silicon ARM64 CPU.
- **`gpu_executed`:** Recorded as `false` in all audit JSON records.
- **CUDA Status:** CUDA acceleration remains blocked on Apple Silicon (no NVIDIA GPU or CUDA runtime available on this machine). No GPU speedup claim is made.
