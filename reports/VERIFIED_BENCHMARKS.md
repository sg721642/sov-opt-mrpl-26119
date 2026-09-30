# Verified Benchmark & Differential Validation Report

**Date:** 2026-10-01  
**Environment:** Apple Silicon ARM64 macOS, Python 3.11.16, NumPy 2.3.5  
**Solver:** SOV-OPT 0.1.1 (Original Sovereign Numerical Optimization Core)  
**External Solvers in Core:** None (NumPy + stdlib only)  

---

## 1. Verified Benchmark Results

All instances below are from official public repositories (Netlib LP, MIPLIB, published literature).
No synthetic or fabricated instances are used as performance evidence.

| Instance | Problem Class | Dimensions (m x n) | SOV-OPT Status | SOV-OPT Objective | Published Reference | Discrepancy | Primal Residual | Stationarity (Dual) | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 0.0 | 6.06e-17 | 0.0 | 8.8 ms |
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -464.753142857 (Netlib / MINOS 5.3) | < 1e-12 | 1.42e-14 | 1.72e-17 | 31.5 ms |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -64.575077058 (Netlib / MINOS 5.3) | < 1e-11 | 5.37e-16 | 4.09e-17 | 35.7 ms |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -70.000000000 (Netlib / MINOS 5.3) | 0.0 | 2.49e-16 | 3.97e-17 | 30.9 ms |
| **BLEND** | LP | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -30.812149846 (Netlib / MINOS 5.3) | < 1e-10 | 1.78e-15 | 1.23e-16 | 828.2 ms |
| **AVGAS (PDHG-CPU)** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 1.1e-7 | 1.84e-8 | 2.10e-8 | 6.1 ms |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **769500.0** | 1201500 (MIPLIB 1.0) | N/A | N/A | N/A | 881.6 ms |

---

## 2. Analysis of Results and Algorithmic Solutions

### Optimal Verified Instances
- **AVGAS, AFIRO, SC50A, SC50B, BLEND** all achieved `OPTIMAL_VERIFIED`.
- In all five instances, primal and dual residuals are at or near machine epsilon (^{-14}$ to ^{-17}$), with KKT conditions independently verified.
- The objectives match published literature values to full precision.

### BLEND Resolution:
- BLEND has 43 equality rows. Previously, splitting each equality row into opposing inequality pairs created 43 degenerate zero-slack pairs that stalled simplex under Bland's rule and caused dense LU to hit singular pivots.
- Directly standardizing equality rows ({eq} x = b_{eq}$) with Phase I artificials (no redundant slack pairs) and adding an unscaled fallback for ill-conditioned equilibration completely resolved BLEND in 555 iterations to machine precision (^{-15}$).

### FLUGPL Resolution:
- Previously, branch-and-bound failed at node 4 because floating-point roundoff in Phase I duals failed the exact rational Farkas certificate test (^T z = 0, h^T z < 0, z \ge 0$).
- Implementing exact rational linear algebra on the Phase I basis solves the exact Farkas dual and preserves certificate validity. The solver cleanly explores 50 and 500 nodes without divergence, returning conservative rational lower bound `769500.0`.

---

## 3. Disclosed Exclusions and Empty States

1. **Proprietary MRPL Production Data (Empty State):**
   - Confidential refinery operational LP matrices are not publicly available. Fictional refinery parameters are strictly prohibited.
   - Genuine historical petroleum blending benchmark `AVGAS` and Netlib refinery problem `BLEND` are provided instead.

2. **Industrial Convex QP Data (Empty State):**
   - `qp_example.qps` (a 2-variable toy example from the QPSReader.jl test suite) has been removed from active verification.
   - Real-world convex QP benchmarks will be admitted only when documented authentic industrial datasets are verified.

---

## 4. Hardware and Acceleration Disclosures

- **CPU Only:** All benchmarks ran on Apple Silicon ARM64 CPU.
- **`gpu_executed`:** Strictly `false` in all audit JSON records.
- **CUDA Status:** CUDA acceleration remains blocked on Apple Silicon (no NVIDIA GPU or CUDA runtime available on this machine). No GPU speedup claim is made.
