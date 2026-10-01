# Verified Benchmark & Differential Validation Report

**Date:** 2026-10-01  
**Environment:** Darwin arm64, Python 3.11.16  
**Solver Revision:** `531bc7c198eae691` (includes +dirty if uncommitted changes)  
**Core Dependencies:** NumPy and Python standard library only (strictly sovereign core)  
**External Validation:** via `scripts/baseline_worker.py` isolated subprocess (highspy or scipy fallback)  

---

## 1. Verified Benchmark Results

All instances below are from official public repositories (Netlib LP, MIPLIB, published literature).
No synthetic or fabricated instances are used as performance evidence.

| Instance | Problem Class | Dimensions (m x n) | SOV-OPT Status | SOV-OPT Objective | Published Reference Text | Discrepancy | Primal Residual | Stationarity (Dual) | Runtime |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 | 0.0 | 5.55e-17 | 2.88e-17 | 10.1 ms |
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -4.6475314286E+02 | 2.86e-09 | 1.42e-14 | 1.72e-17 | 22.4 ms |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -6.4575077059E+01 | 4.35e-10 | 5.37e-16 | 4.09e-17 | 50.0 ms |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -7.0000000000E+01 | 0.0 | 2.49e-16 | 3.97e-17 | 46.3 ms |
| **BLEND** | LP | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -3.0812149846E+01 | 1.72e-10 | 1.78e-15 | 1.23e-16 | 908.6 ms |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **1173645** | 1201500 (integer optimal); 769500.0 (LP relaxation root bound) | N/A | N/A | N/A | 1022.0 ms |
| **AVGAS (PDHG-CPU)** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 (Symonds 1955) | 1.1e-07 | 1.31e-08 | 1.90e-09 | 4.0 ms |

---

## 2. Independent Differential Verification (External Subprocess)

External validation is performed by invoking `scripts/baseline_worker.py` in a separate interpreter process.
The worker tries `highspy` (native C++ HiGHS) first; if unavailable, falls back to `scipy.optimize.linprog/milp`.
If neither is available, status is `NOT_RUN` or `FAILED` with the actual error recorded.

| Instance | Input MPS File | External Status | External Objective | SOV-OPT Objective / Bound | Discrepancy | Comparison |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **AVGAS** | `data/verified/avgas.mps` | `FAILED` | — | — | — | `FAILED` |
| **AFIRO** | `data/verified/afiro.mps` | `FAILED` | — | — | — | `FAILED` |
| **SC50A** | `data/verified/sc50a.mps` | `FAILED` | — | — | — | `FAILED` |
| **SC50B** | `data/verified/sc50b.mps` | `FAILED` | — | — | — | `FAILED` |
| **BLEND** | `data/verified/blend.mps` | `FAILED` | — | — | — | `FAILED` |
| **FLUGPL** | `data/verified/flugpl.mps` | `FAILED` | — | Bound: 1173644.9999999998 | Bound vs optimum only | `FAILED` |

### Notes on External Differential Comparison:
1. **Netlib BLEND:** Both SOV-OPT and the external solver (if available) read `blend.mps` directly. Agreement between them shows they parse the same file. The Netlib MINOS 5.3 README reference (-3.0812149846E+01, 11 significant digits) differs from the full-precision result; the source of this discrepancy (truncation in historical text, or solver difference) is not independently confirmed here — do not assert a specific cause.
2. **MIPLIB FLUGPL Bound:** MIPLIB integer optimum is 1201500.0. SOV-OPT produces a conservative lower bound of approximately 1173644.9999999998 (floating-point display) at 50 nodes with no incumbent found. Status: LIMIT_REACHED. This is not a completed MILP solve.
3. **AVGAS Provenance Note:** The MPS file is sourced from the HiGHS test suite (https://github.com/ERGO-Code/HiGHS). Primary historical attribution to Charnes, Cooper, Mellon (1952) *Econometrica* and Symonds (1955) has not been independently verified against the primary sources in this session. Treat provenance as plausible but unverified against primary literature.

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
