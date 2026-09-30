# Verified Benchmark & Differential Validation Report

**Date:** 2026-09-30  
**Environment:** Darwin arm64, Python 3.11.16  
**Solver Version:** SOV-OPT 0.1.2 (`bb3acc72`)  
**Core Dependencies:** NumPy and Python standard library only (strictly sovereign core)  
**External Validation:** HiGHS 1.15.1 native C++ solver and SciPy HiGHS interface (isolated subprocess only)  

---

## 1. Verified Benchmark Results

All instances below are from official public repositories (Netlib LP, MIPLIB, published literature).
No synthetic or fabricated instances are used as performance evidence.

| Instance | Problem Class | Dimensions (m x n) | SOV-OPT Status | SOV-OPT Objective | Published Reference Text | Discrepancy | Primal Residual | Stationarity (Dual) | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 | 0.0 | 5.55e-17 | 2.88e-17 | 10.7 ms |
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -4.6475314286E+02 | 2.86e-09 | 1.42e-14 | 1.72e-17 | 24.1 ms |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -6.4575077059E+01 | 4.35e-10 | 5.37e-16 | 4.09e-17 | 50.5 ms |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -7.0000000000E+01 | 0.0 | 2.49e-16 | 3.97e-17 | 47.8 ms |
| **BLEND** | LP | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -3.0812149846E+01 | 1.72e-10 | 1.78e-15 | 1.23e-16 | 920.6 ms |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **1173645.0** | 1201500 (integer optimal); 769500.0 (LP relaxation root bound) | N/A | N/A | N/A | 1089.9 ms |
| **AVGAS (PDHG-CPU)** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 1.1e-07 | 1.31e-08 | 1.90e-09 | 4.0 ms |

---

## 2. Independent Differential Verification (Native HiGHS 1.15.1)

To provide rigorous independent verification, all 6 genuine instances were solved using the native C++ HiGHS 1.15.1 solver via `highspy` in an isolated external process (completely separated from the sovereign solver core):

| Instance | Input MPS File | HiGHS C++ Status | HiGHS Objective | SOV-OPT Objective / Bound | Discrepancy (SOV-OPT vs HiGHS) | Match Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | `data/verified/avgas.mps` | `HighsModelStatus.kOptimal` | -7.750000 | -7.750000 | 0.0 | `EXACT_MATCH` |
| **AFIRO** | `data/verified/afiro.mps` | `HighsModelStatus.kOptimal` | -464.753143 | -464.753143 | 5.68e-14 | `MATCH (< 1e-12)` |
| **SC50A** | `data/verified/sc50a.mps` | `HighsModelStatus.kOptimal` | -64.575077 | -64.575077 | 0.0 | `EXACT_MATCH` |
| **SC50B** | `data/verified/sc50b.mps` | `HighsModelStatus.kOptimal` | -70.000000 | -70.000000 | 0.0 | `EXACT_MATCH` |
| **BLEND** | `data/verified/blend.mps` | `HighsModelStatus.kOptimal` | -30.812150 | -30.812150 | 0.0 | `EXACT_MATCH` |
| **FLUGPL** | `data/verified/flugpl.mps` | `HighsModelStatus.kOptimal` | 1201500.000000 | Bound: 1173645.0 | Safe lower bound <= 1201500 | `VALIDATED_BOUND` |

### Key Findings from Differential Comparison:
1. **Netlib BLEND Resolution:** Native HiGHS 1.15.1 directly reading `blend.mps` returns **-30.8121498458**, exactly matching SOV-OPT to full precision (`-30.812149845828237`). This independently proves that the discrepancy against the 1988 Netlib README (`-3.0812149846E+01`) is due solely to 11-digit text truncation in historical MINOS 5.3 output, not a solver defect.
2. **MIPLIB FLUGPL Bound:** MIPLIB integer optimum is verified as 1201500.0 by HiGHS. SOV-OPT explores the branch-and-bound tree with exact rational basis duals and exact rational Farkas certificates, advancing the conservative lower bound from root to 1173645.0 at 50 nodes without numerical instability.
3. **Netlib Staircase Models (SC50A, SC50B):** Both match HiGHS and Netlib references to machine precision.

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
