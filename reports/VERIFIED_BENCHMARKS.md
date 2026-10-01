# Verified Benchmark & Differential Validation Report

**Date:** 2026-10-01  
**Environment:** Darwin arm64, Python 3.11.16  
**Solver Revision:** `2c8e33930856142e` (includes +dirty if uncommitted changes)  
**Core Dependencies:** NumPy and Python standard library only (strictly sovereign core)  
**External Validation:** via `scripts/baseline_worker.py` isolated subprocess (highspy or scipy fallback)  

---

## 1. Verified Benchmark Results

All instances below are from official public repositories (Netlib LP, MIPLIB, published literature).
No synthetic or fabricated instances are used as performance evidence.

| Instance | Problem Class | Dimensions (m x n) | SOV-OPT Status | SOV-OPT Objective | Published Reference Text | Discrepancy | Primal Residual | Stationarity (Dual) | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -4.6475314286E+02 | 2.86e-09 | 1.42e-14 | 1.72e-17 | 24.7 ms |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -6.4575077059E+01 | 4.35e-10 | 5.37e-16 | 4.09e-17 | 50.0 ms |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -7.0000000000E+01 | 0.0 | 2.49e-16 | 3.97e-17 | 47.2 ms |
| **BLEND** | LP | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -3.0812149846E+01 | 1.72e-10 | 1.78e-15 | 1.23e-16 | 918.0 ms |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **1173645** | 1201500 (integer optimal); 769500.0 (LP relaxation root bound) | N/A | N/A | N/A | 1040.4 ms |
| **AFIRO (PDHG-CPU)** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753142** | -464.75314286 (Netlib) | 6.3e-07 | 8.07e-09 | 5.93e-08 | 105.2 ms |

---

## 2. Independent Differential Verification (External Subprocess)

External validation is performed by invoking `scripts/baseline_worker.py` in a separate interpreter process.
The worker tries `highspy` (native C++ HiGHS) first; if unavailable, falls back to `scipy.optimize.linprog/milp`.
If neither is available, status is `NOT_RUN` or `FAILED` with the actual error recorded.

| Instance | Input MPS File | External Status | External Objective | SOV-OPT Objective / Bound | Discrepancy | Comparison |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **AFIRO** | `data/verified/afiro.mps` | `HighsModelStatus.kOptimal` | -464.753143 | -464.753143 | 0.0 | `MATCH` |
| **SC50A** | `data/verified/sc50a.mps` | `HighsModelStatus.kOptimal` | -64.575077 | -64.575077 | 0.0 | `MATCH` |
| **SC50B** | `data/verified/sc50b.mps` | `HighsModelStatus.kOptimal` | -70.000000 | -70.000000 | 1.42e-14 | `MATCH` |
| **BLEND** | `data/verified/blend.mps` | `HighsModelStatus.kOptimal` | -30.812150 | -30.812150 | 0.0 | `MATCH` |
| **FLUGPL** | `data/verified/flugpl.mps` | `HighsModelStatus.kOptimal` | 1201500.000000 | Bound: 1173644.9999999998 | Bound vs optimum only | `BOUND_ONLY` |

### Notes on External Differential Comparison:
1. **Netlib BLEND:** Both SOV-OPT and the external solver (if available) read `blend.mps` directly. Agreement between them shows they compute the same objective on the same model. The Netlib MINOS 5.3 README reference (-3.0812149846E+01, 11 significant digits) differs by ~1.72e-10 from the full-precision result.
2. **MIPLIB FLUGPL Bound:** MIPLIB integer optimum is 1201500.0. SOV-OPT produces a conservative lower bound of approximately 1173644.9999999998 (floating-point display) at 50 nodes with no incumbent found. Status: LIMIT_REACHED. This is not a completed MILP solve.
3. **Quarantined Instance (AVGAS):** `avgas.mps` is quarantined under `data/quarantined/` pending independent primary literature verification of its historical attribution (Charnes et al. 1952 / Symonds 1955). It is excluded from the active verified suite above.

---

## 3. Disclosed Exclusions and Empty States

1. **Proprietary MRPL Production Data (Empty State):**
   - No authorized MRPL dataset is available in this project. Confidential refinery operational LP matrices are not public. Fictional refinery parameters are strictly prohibited.
   - Netlib refinery blending benchmark `BLEND` (Murtagh) is provided as an authentic benchmark problem.

2. **Industrial Convex QP Data (Empty State):**
   - No authentic public industrial convex QP benchmark is currently admitted in the verified active suite. Toy synthetic QP instances have been removed.
   - Numerical eigenvalue inspection and pivoted Schur complements are floating-point checks, not exact rational PSD certificates.

---

## 4. Hardware and Acceleration Disclosures

- **CPU Only:** All benchmarks ran on Apple Silicon ARM64 CPU.
- **`gpu_executed`:** Strictly `false` in all audit JSON records.
- **CUDA Status:** CUDA acceleration remains blocked on Apple Silicon (no NVIDIA GPU or CUDA runtime available on this machine). No GPU speedup claim is made.
