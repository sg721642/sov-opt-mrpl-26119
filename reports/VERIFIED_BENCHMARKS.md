# Verified Benchmark & Differential Validation Report

**Date:** 2026-10-01  
**Environment:** Apple Silicon ARM64 macOS, Python 3.11.16, NumPy 2.3.5  
**Solver:** SOV-OPT 0.1.2 (Original Sovereign Numerical Optimization Core)  
**External Solvers in Core:** None (NumPy + Python stdlib only)  

---

## 1. Verified Benchmark Results

All instances below are from official public repositories (Netlib LP, MIPLIB, published literature).
No synthetic or fabricated instances are used as performance evidence.

| Instance | Problem Class | Dimensions (m x n) | SOV-OPT Status | SOV-OPT Objective | Published Reference Text | Discrepancy | Primal Residual | Stationarity (Dual) | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 0.0 | 5.55e-17 | 2.88e-17 | 8.5 ms |
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -4.6475314286E+02 (Netlib README) | < 1e-10 | 1.42e-14 | 1.72e-17 | 18.1 ms |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -6.4575077059E+01 (Netlib README) | < 1e-10 | 5.37e-16 | 4.09e-17 | 33.5 ms |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -7.0000000000E+01 (Netlib README) | 0.0 | 2.49e-16 | 3.97e-17 | 29.5 ms |
| **BLEND** | LP | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -3.0812149846E+01 (Netlib README) | 1.72e-10 | 1.78e-15 | 1.23e-16 | 827.2 ms |
| **AVGAS (PDHG-CPU)** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 1.1e-7 | 1.31e-08 | 1.90e-09 | 3.6 ms |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **769500.0** | 1201500 (MIPLIB 1.0); root: 769500 | N/A | N/A | N/A | 877.3 ms |

---

## 2. Analysis of Results and Algorithmic Solutions

### Optimal Verified Instances
- **AVGAS, AFIRO, SC50A, SC50B, BLEND** all achieved `OPTIMAL_VERIFIED`.
- In all five instances, primal and dual residuals are at or near machine epsilon ($10^{-14}$ to $10^{-17}$), with KKT conditions independently verified.
- The objectives match published literature values to full precision.

### BLEND Resolution:
- BLEND has 43 equality rows. Directly standardizing equality rows ($A_{\text{eq}} x = b_{\text{eq}}$) with Phase I artificials (avoiding redundant opposing slack pairs that cause simplex cycling) and adding an unscaled fallback for ill-conditioned equilibration cleanly solved BLEND in 555 iterations to machine precision ($1.78 \times 10^{-15}$).
- Discrepancy against Netlib's 11-digit published reference (`-3.0812149846E+01`): the computed objective `-30.812149845828237` differs by approximately $1.72 \times 10^{-10}$, fully accounted for by 11-digit truncation in the 1988 MINOS 5.3 report.

### FLUGPL Resolution:
- Branch-and-bound explores the tree and prunes infeasible branches using exact rational Farkas certificates ($G^T z = 0, h^T z < 0, z \ge 0$).
- Implementing exact rational linear algebra on the Phase I basis solves the exact Farkas dual losslessly.
- At node limit 50, the solver safely reports `LIMIT_REACHED` with conservative rational lower bound `769500.0`, verified integer relaxation bounds, and no divergence.

---

## 3. Disclosed Exclusions and Empty States

1. **Proprietary MRPL Production Data (Empty State):**
   - No authorized MRPL dataset is available in this project. Confidential refinery operational LP matrices are not public. Fictional refinery parameters are strictly prohibited.
   - Documented historical petroleum blending benchmark `AVGAS` (Symonds 1955) and Netlib refinery problem `BLEND` (Murtagh) are provided instead.

2. **Industrial Convex QP Data (Empty State):**
   - No authentic public industrial convex QP benchmark is currently admitted in the verified active suite. Toy synthetic QP instances have been removed.
   - Numerical eigenvalue inspection and pivoted Schur complements are floating-point checks, not exact rational PSD certificates.

---

## 4. Hardware and Acceleration Disclosures

- **CPU Only:** All benchmarks ran on Apple Silicon ARM64 CPU.
- **`gpu_executed`:** Strictly `false` in all audit JSON records.
- **CUDA Status:** CUDA acceleration remains blocked on Apple Silicon (no NVIDIA GPU or CUDA runtime available on this machine). No GPU speedup claim is made.
