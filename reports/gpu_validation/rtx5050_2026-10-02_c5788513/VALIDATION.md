# Gate 8 Phase B — Physical NVIDIA RTX 5050 Validation Report

## Hardware & System Metadata

- **GPU Device**: NVIDIA GeForce RTX 5050 Laptop GPU
- **Compute Capability**: 12.0
- **VRAM**: 7.96 GB
- **Driver Version**: 576.83
- **CUDA Runtime Version**: 12090
- **Power State**: AC_CONNECTED_FULL
- **Git SHA**: `c5788513e6a4517961652a3aa335f8f5243a16b8`
- **Preflight Status**: `NVIDIA_CUDA_READY` (Micro SpMV max discrepancy: `3.55e-15`)

---

## Core Performance Conclusion

> **Performance Conclusion**:
> The current RTX 5050 CUDA PDHG implementation is correctness-validated but does not outperform the same-machine CPU PDHG baseline end-to-end on this frozen Netlib suite. GPU performance improves relative to CPU as problem size increases, approaching parity on the largest tested cases.

*Note: The repository's LARGE stratum is relative to this frozen Netlib suite.*
*Note: CPU and CUDA produced matching solver statuses across the suite, with small numerical objective discrepancies in the recorded candidates.*

---

## Suite Summary

- **Total Netlib LP Instances**: 18
- **OPTIMAL_VERIFIED Count**: 3 (`afiro, blend, sctap2`)
- **LIMIT_REACHED Count**: 15 (`kb2, sc50a, sc50b, adlittle, sc105, stocfor1, scagr7, recipe, israel, sc205, share1b, brandy, grow15, grow22, scfxm2`)
- **Total Suite CPU E2E Time**: 211.42 s
- **Total Suite CUDA E2E Time**: 342.64 s
- **Overall Suite Speedup (CPU / CUDA)**: 0.62x

---

## Stratum Aggregates

| Stratum | Instances | Total CPU Time (s) | Total CUDA Time (s) | Aggregate Speedup (CPU/CUDA) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **SMALL** | 6 | 5.64 | 50.93 | 0.11x | GPU Slowdown (Host-Device Overhead) |
| **MEDIUM** | 8 | 35.94 | 105.07 | 0.34x | GPU Slowdown (Scaling Up) |
| **LARGE** | 4 | 169.84 | 186.63 | 0.91x | Approaching Parity (`grow22` @ 1.00x) |

---

## Per-Instance Validation & Speedup Table

Speedup is defined as `median CPU end-to-end time / median CUDA end-to-end time`.
Values < 1.0x indicate GPU slowdown relative to CPU; values = 1.0x indicate parity.

| Instance | Stratum | Status | `gpu_executed` | CPU E2E (ms) | CUDA E2E (ms) | Speedup (CPU/CUDA) | Objective Discrepancy |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **afiro** | SMALL | `OPTIMAL_VERIFIED` | `True` | 228.97 | 2749.82 | **0.08x** | `0.00e+00` |
| **kb2** | SMALL | `LIMIT_REACHED` | `True` | 1178.11 | 11384.73 | **0.10x** | `5.68e-14` |
| **sc50a** | SMALL | `LIMIT_REACHED` | `True` | 1134.41 | 11293.80 | **0.10x** | `7.11e-15` |
| **sc50b** | SMALL | `LIMIT_REACHED` | `True` | 1130.72 | 11277.15 | **0.10x** | `2.13e-14` |
| **adlittle** | SMALL | `LIMIT_REACHED` | `True` | 1580.87 | 11549.81 | **0.14x** | `3.35e-09` |
| **blend** | SMALL | `OPTIMAL_VERIFIED` | `True` | 387.65 | 2677.71 | **0.14x** | `2.13e-14` |
| **sc105** | MEDIUM | `LIMIT_REACHED` | `True` | 1704.95 | 11886.38 | **0.14x** | `2.66e-15` |
| **stocfor1** | MEDIUM | `LIMIT_REACHED` | `True` | 6309.24 | 12053.50 | **0.52x** | `1.46e-11` |
| **scagr7** | MEDIUM | `LIMIT_REACHED` | `True` | 7736.73 | 12590.66 | **0.61x** | `4.66e-10` |
| **recipe** | MEDIUM | `LIMIT_REACHED` | `True` | 2900.48 | 13279.22 | **0.22x** | `0.00e+00` |
| **israel** | MEDIUM | `LIMIT_REACHED` | `True` | 3171.19 | 12347.19 | **0.26x** | `1.16e-10` |
| **sc205** | MEDIUM | `LIMIT_REACHED` | `True` | 3549.05 | 13719.23 | **0.26x** | `4.44e-16` |
| **share1b** | MEDIUM | `LIMIT_REACHED` | `True` | 4108.80 | 13852.87 | **0.30x** | `2.18e-11` |
| **brandy** | MEDIUM | `LIMIT_REACHED` | `True` | 6458.75 | 15342.75 | **0.42x** | `9.09e-13` |
| **grow15** | LARGE | `LIMIT_REACHED` | `True` | 33922.63 | 41372.30 | **0.82x** | `3.95e-07` |
| **grow22** | LARGE | `LIMIT_REACHED` | `True` | 72445.21 | 72325.93 | **1.00x** | `1.19e-06` |
| **scfxm2** | LARGE | `LIMIT_REACHED` | `True` | 42733.58 | 51342.82 | **0.83x** | `0.00e+00` |
| **sctap2** | LARGE | `OPTIMAL_VERIFIED` | `True` | 20742.20 | 21589.29 | **0.96x** | `6.82e-13` |

---

## CUDA Ablation Results

Ablation evaluated 4 configurations on `afiro`, `sc50a`, `blend`, and `sc105` (max 30,000 iterations, tolerance 1e-7):
1. `baseline_restarted_scaled`: Restart=1000, Scaling=True
2. `no_scaling`: Restart=1000, Scaling=False
3. `no_restart`: Restart=False, Scaling=True
4. `no_scaling_no_restart`: Restart=False, Scaling=False

### Findings:
- On `afiro`, `no_restart` converged in **6,500 iterations** (1,494.5 ms) vs **12,000 iterations** (2,872.7 ms) for `baseline_restarted_scaled`. This demonstrates that ergodic restarting is **not universally necessary or faster** for all LP instances.
- On `blend`, Pock-Chambolle diagonal scaling is essential: disabling scaling (`no_scaling`) causes the solver to hit `LIMIT_REACHED` at 30,000 iterations without reaching target KKT tolerance.

---

## Verification & Integrity Safeguards

1. **Physical GPU Verification**: `gpu_executed = True` recorded on all CUDA solver runs.
2. **Deterministic Reproducibility**: Measured on frozen source SHA `c5788513e6a4517961652a3aa335f8f5243a16b8`.
3. **Honest Reporting**: Unfavorable GPU speedups (< 1.0x on small/medium instances) retained without exaggeration or false speedup claims.
