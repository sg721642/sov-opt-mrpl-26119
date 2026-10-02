# Gate 9 Physical CUDA Optimization Report — NVIDIA RTX 5050 Laptop GPU

## Environment & Hardware Metadata

- **Candidate SHA**: `9407fb55322fdd0b651857d5f177b85409b4b8a4`
- **Gate 8 Baseline SHA**: `cefa9c33f1d4d44be13765c0d2d5b72c89c9a1a4`
- **GPU Device**: NVIDIA GeForce RTX 5050 Laptop GPU
- **Compute Capability**: 12.0
- **VRAM Total**: 7.96 GB
- **Driver / CUDA Version**: 12090
- **Preflight Status**: `NVIDIA_CUDA_READY` (Micro SpMV max discrepancy: `3.55e-15`)

---

## Core Performance Findings

> **Executive Conclusion**:
> Gate 9 CUDA optimizations significantly improved CUDA PDHG performance on the physical RTX 5050 by an overall aggregate factor of **1.79x** compared to Gate 8 CUDA (SMALL stratum CUDA execution improved by **5.57x**, MEDIUM stratum CUDA execution improved by **3.67x**).
> Overall suite Gate 9 CUDA end-to-end speedup relative to Gate 9 CPU is **1.08x** (SMALL: **0.61x**, MEDIUM: **0.91x**, LARGE: **1.14x**).

*Note: The repository's LARGE stratum is relative to this frozen Netlib suite subset (`data/manifests/gpu_pdhg_large_public.json`).*
*Note: CPU and CUDA produced matching solver statuses across the suite, with small numerical objective discrepancies in the recorded candidates.*

---

## Stratum Aggregates & Improvement Matrix

| Stratum | Gate 8 CUDA (s) | Gate 9 CUDA (s) | Gate 9 CPU (s) | CUDA Improvement Factor (Gate8 / Gate9 CUDA) | Gate 9 Speedup (Gate9 CPU / Gate9 CUDA) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SMALL** | 50.93 | 9.15 | 5.54 | **5.57x** | **0.61x** |
| **MEDIUM** | 105.07 | 28.59 | 25.89 | **3.67x** | **0.91x** |
| **LARGE** | 186.63 | 154.12 | 175.13 | **1.21x** | **1.14x** |
| **TOTAL** | 342.64 | 191.86 | 206.57 | **1.79x** | **1.08x** |

---

## Complete Per-Instance Comparison Table

| Instance | Stratum | Status | `gpu_executed` | Gate 8 CUDA (ms) | Gate 9 CUDA (ms) | Gate 9 CPU (ms) | CUDA Improvement Factor | Gate 9 Speedup (CPU/CUDA) | Obj Discrepancy |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **afiro** | SMALL | `OPTIMAL_VERIFIED` | `True` | 2749.82 | 443.88 | 225.62 | **6.19x** | **0.51x** | `5.68e-14` |
| **kb2** | SMALL | `LIMIT_REACHED` | `True` | 11384.73 | 1929.66 | 1156.47 | **5.90x** | **0.60x** | `1.14e-13` |
| **sc50a** | SMALL | `LIMIT_REACHED` | `True` | 11293.80 | 1991.68 | 1113.48 | **5.67x** | **0.56x** | `5.68e-14` |
| **sc50b** | SMALL | `LIMIT_REACHED` | `True` | 11277.15 | 2005.08 | 1111.30 | **5.62x** | **0.55x** | `0.00e+00` |
| **adlittle** | SMALL | `LIMIT_REACHED` | `True` | 11549.81 | 2263.26 | 1556.95 | **5.10x** | **0.69x** | `1.16e-10` |
| **blend** | SMALL | `OPTIMAL_VERIFIED` | `True` | 2677.71 | 512.73 | 375.52 | **5.22x** | **0.73x** | `5.68e-14` |
| **sc105** | MEDIUM | `LIMIT_REACHED` | `True` | 11886.38 | 2468.89 | 1642.74 | **4.81x** | **0.67x** | `7.99e-15` |
| **stocfor1** | MEDIUM | `LIMIT_REACHED` | `True` | 12053.50 | 2584.20 | 1916.92 | **4.66x** | **0.74x** | `9.46e-11` |
| **scagr7** | MEDIUM | `LIMIT_REACHED` | `True` | 12590.66 | 2991.12 | 2265.04 | **4.21x** | **0.76x** | `4.66e-10` |
| **recipe** | MEDIUM | `LIMIT_REACHED` | `True` | 13279.22 | 3361.16 | 2815.53 | **3.95x** | **0.84x** | `1.14e-13` |
| **israel** | MEDIUM | `LIMIT_REACHED` | `True` | 12347.19 | 3225.63 | 3197.50 | **3.83x** | **0.99x** | `0.00e+00` |
| **sc205** | MEDIUM | `LIMIT_REACHED` | `True` | 13719.23 | 4186.34 | 3536.56 | **3.28x** | **0.84x** | `1.67e-16` |
| **share1b** | MEDIUM | `LIMIT_REACHED` | `True` | 13852.87 | 4078.65 | 3992.45 | **3.40x** | **0.98x** | `8.73e-11` |
| **brandy** | MEDIUM | `LIMIT_REACHED` | `True` | 15342.75 | 5698.08 | 6527.44 | **2.69x** | **1.15x** | `2.27e-13` |
| **grow15** | LARGE | `LIMIT_REACHED` | `True` | 41372.30 | 30456.71 | 34209.37 | **1.36x** | **1.12x** | `6.56e-07` |
| **grow22** | LARGE | `LIMIT_REACHED` | `True` | 72325.93 | 62497.02 | 74819.76 | **1.16x** | **1.20x** | `9.76e-07` |
| **scfxm2** | LARGE | `LIMIT_REACHED` | `True` | 51342.82 | 40671.05 | 44934.60 | **1.26x** | **1.10x** | `7.28e-12` |
| **sctap2** | LARGE | `OPTIMAL_VERIFIED` | `True` | 21589.29 | 20498.90 | 21167.92 | **1.05x** | **1.03x** | `9.09e-13` |

---

## CUDA Ablation Results (`ablation_pdhg_cuda_rtx5050.json`)

Ablation evaluated 4 configurations on `afiro`, `sc50a`, `blend`, and `sc105` (max 30,000 iterations, tolerance 1e-7):
1. `baseline_restarted_scaled`: Restart=1000, Scaling=True
2. `no_scaling`: Restart=1000, Scaling=False
3. `no_restart`: Restart=False, Scaling=True
4. `no_scaling_no_restart`: Restart=False, Scaling=False

### Findings:
- On `afiro`, `no_restart` converged in **6,500 iterations** (245.5 ms) vs **12,000 iterations** (457.5 ms) for `baseline_restarted_scaled`. This demonstrates that ergodic restarting is **not universally necessary or faster** for all LP instances.
- On `blend`, Pock-Chambolle diagonal scaling is essential: disabling scaling (`no_scaling`) causes the solver to hit `LIMIT_REACHED` at 30,000 iterations without reaching target KKT tolerance.

---

## Telemetry Audit & Architecture

- **Kernel Launches**: In Gate 9, kernel launch overhead per iteration was minimized by fusing primal and dual step updates (`primal_step_fused`, `dual_step_fused`). For 12,000 iterations on `afiro`, `kernel_launches_count = 48,033` ($pprox 4$ launches per iteration: 2 SpMV + primal step + dual step).
- **Iteration Loop Memory Allocation**: The iteration loop is designed to reuse preallocated work buffers on the GPU device and avoid dynamic array allocations during solver iterations.
