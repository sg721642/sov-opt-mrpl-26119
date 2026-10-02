# Gate 9 Final Physical CUDA Revalidation Report — NVIDIA RTX 5050 Laptop GPU

## Provenance & Exact Frozen Source

- **GATE9_VALIDATED_SOURCE_SHA**: `51b71bb8468bd4375e572b2537d69e30a0e60684`
- **Provenance Statement**: All performance measurements in this directory were executed from a clean working tree at the exact committed source SHA shown above.
- **Gate 8 Baseline SHA**: `cefa9c33f1d4d44be13765c0d2d5b72c89c9a1a4`
- **GPU Device**: NVIDIA GeForce RTX 5050 Laptop GPU
- **Compute Capability**: 12.0
- **VRAM Total**: 7.96 GB
- **Driver / CUDA Version**: 12090
- **Preflight Status**: `NVIDIA_CUDA_READY` (Micro SpMV max discrepancy: `3.55e-15`)

---

## Core Performance Summary

> **Executive Conclusion**:
> Gate 9 CUDA optimizations significantly improved CUDA PDHG performance on the physical RTX 5050 by an overall aggregate factor of **1.81x** compared to Gate 8 CUDA (SMALL stratum CUDA execution improved by **5.65x**, MEDIUM stratum CUDA execution improved by **3.74x**).
> Overall suite Gate 9 CUDA end-to-end speedup relative to Gate 9 CPU is **1.07x** (SMALL: **0.61x**, MEDIUM: **0.93x**, LARGE: **1.13x**).

*Note: The repository's LARGE stratum is relative to this frozen Netlib suite subset (`data/manifests/gpu_pdhg_large_public.json`).*
*Note: CPU and CUDA statuses and CPU original-model verification outcomes were compared; numerical objective differences are reported separately.*

---

## Stratum Aggregates & Improvement Matrix

| Stratum | Gate 8 CUDA (s) | Gate 9 CUDA (s) | Gate 9 CPU (s) | CUDA Improvement Factor (Gate8 / Gate9 CUDA) | Gate 9 Speedup (Gate9 CPU / Gate9 CUDA) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SMALL** | 50.93 | 9.02 | 5.53 | **5.65x** | **0.61x** |
| **MEDIUM** | 105.07 | 28.07 | 26.00 | **3.74x** | **0.93x** |
| **LARGE** | 186.63 | 152.60 | 172.04 | **1.22x** | **1.13x** |
| **TOTAL** | 342.64 | 189.69 | 203.56 | **1.81x** | **1.07x** |

---

## Complete Per-Instance Comparison Table

| Instance | Stratum | Status | `gpu_executed` | Gate 8 CUDA (ms) | Gate 9 CUDA (ms) | Gate 9 CPU (ms) | CUDA Improvement Factor | Gate 9 Speedup (CPU/CUDA) | Obj Discrepancy |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **afiro** | SMALL | `OPTIMAL_VERIFIED` | `True` | 2749.82 | 432.92 | 223.29 | **6.35x** | **0.52x** | `5.68e-14` |
| **kb2** | SMALL | `LIMIT_REACHED` | `True` | 11384.73 | 1920.70 | 1158.52 | **5.93x** | **0.60x** | `1.14e-13` |
| **sc50a** | SMALL | `LIMIT_REACHED` | `True` | 11293.80 | 1961.44 | 1122.46 | **5.76x** | **0.57x** | `5.68e-14` |
| **sc50b** | SMALL | `LIMIT_REACHED` | `True` | 11277.15 | 1976.63 | 1108.33 | **5.71x** | **0.56x** | `0.00e+00` |
| **adlittle** | SMALL | `LIMIT_REACHED` | `True` | 11549.81 | 2222.38 | 1541.18 | **5.20x** | **0.69x** | `1.16e-10` |
| **blend** | SMALL | `OPTIMAL_VERIFIED` | `True` | 2677.71 | 502.43 | 375.62 | **5.33x** | **0.75x** | `5.68e-14` |
| **sc105** | MEDIUM | `LIMIT_REACHED` | `True` | 11886.38 | 2426.98 | 1637.14 | **4.90x** | **0.67x** | `7.99e-15` |
| **stocfor1** | MEDIUM | `LIMIT_REACHED` | `True` | 12053.50 | 2562.10 | 1920.72 | **4.70x** | **0.75x** | `9.46e-11` |
| **scagr7** | MEDIUM | `LIMIT_REACHED` | `True` | 12590.66 | 2938.05 | 2397.50 | **4.29x** | **0.82x** | `4.66e-10` |
| **recipe** | MEDIUM | `LIMIT_REACHED` | `True` | 13279.22 | 3367.34 | 2819.76 | **3.94x** | **0.84x** | `1.14e-13` |
| **israel** | MEDIUM | `LIMIT_REACHED` | `True` | 12347.19 | 3219.63 | 3051.07 | **3.83x** | **0.95x** | `0.00e+00` |
| **sc205** | MEDIUM | `LIMIT_REACHED` | `True` | 13719.23 | 4211.82 | 3556.07 | **3.26x** | **0.84x** | `1.67e-16` |
| **share1b** | MEDIUM | `LIMIT_REACHED` | `True` | 13852.87 | 3583.12 | 4088.94 | **3.87x** | **1.14x** | `8.73e-11` |
| **brandy** | MEDIUM | `LIMIT_REACHED` | `True` | 15342.75 | 5761.74 | 6528.40 | **2.66x** | **1.13x** | `2.27e-13` |
| **grow15** | LARGE | `LIMIT_REACHED` | `True` | 41372.30 | 28697.45 | 34595.08 | **1.44x** | **1.21x** | `6.56e-07` |
| **grow22** | LARGE | `LIMIT_REACHED` | `True` | 72325.93 | 63286.21 | 71687.13 | **1.14x** | **1.13x** | `9.76e-07` |
| **scfxm2** | LARGE | `LIMIT_REACHED` | `True` | 51342.82 | 40126.48 | 44272.90 | **1.28x** | **1.10x** | `7.28e-12` |
| **sctap2** | LARGE | `OPTIMAL_VERIFIED` | `True` | 21589.29 | 20490.39 | 21480.05 | **1.05x** | **1.05x** | `9.09e-13` |

---

## Verification & Integrity Safeguards

1. **Exact-SHA Clean Source Execution**: All physical benchmarks were performed from a clean working tree at exact committed SHA `51b71bb8468bd4375e572b2537d69e30a0e60684`.
2. **Physical GPU Verification**: `gpu_executed = True` recorded on all CUDA solver runs.
3. **Honest Reporting**: Full suite results reported without cherry-picking.
