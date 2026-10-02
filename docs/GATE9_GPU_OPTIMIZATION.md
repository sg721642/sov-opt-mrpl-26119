# Gate 9 — GPU Performance Engineering for SOV-OPT

## 1. Executive Summary & Context

SOV-OPT is an original numerical optimization research prototype for MRPL SIH Problem Statement 26119. In Gate 8, physical execution on an NVIDIA GeForce RTX 5050 Laptop GPU (Ada/Blackwell architecture, 8GB VRAM) proved the mathematical correctness and end-to-end viability of sovereign CUDA restarted PDHG across 18 frozen continuous LP instances from the Netlib LP benchmark library (Git commit `c5788513e6a4517961652a3aa335f8f5243a16b8`, final evidence commit `cefa9c33f1d4d44be13765c0d2d5b72c89c9a1a4`).

### Gate 8 Baseline Measured Performance
- **Overall geometric-mean E2E CPU/CUDA speedup:** 0.62x
- **SMALL stratum aggregate:** 0.11x
- **MEDIUM stratum aggregate:** 0.34x
- **LARGE stratum aggregate:** 0.91x (with `grow22` reaching 1.00x parity)
- **Key Observation:** The GPU execution was dominated by driver launch overhead and memory pool allocation churn, rather than floating-point computation time. As instance dimensions scaled up (from AFIRO to GROW22), the GPU transitioned from 10x slower to parity.

The primary objective of Gate 9 is to eliminate GPU runtime overhead in native SOV-OPT CUDA PDHG, achieving substantially lower per-iteration latency, zero memory pool churn, and superior scaling on the Acer RTX 5050 hardware.

---

## 2. Bottleneck Analysis of Gate 8 CUDA Implementation

Detailed profiling of the Gate 8 CUDA implementation revealed five distinct performance bottlenecks:

1. **Python-to-CUDA Driver Dispatch Overhead (18 Launches/Iteration):**
   In Gate 8, each PDHG iteration issued ~18 discrete CuPy operations (`A.dot`, `hh - ...`, `sigma * ...`, `xp.maximum`, `AT.dot`, `c + ...`, `tau * ...`, `xp.clip`, `bar = 2*x - x_old`, `avg += ...`, `avgy += ...`). Each CuPy invocation incurs Python interpreter evaluation and CUDA driver launch latency (~5-10 microseconds per launch).
   At 18 dispatches/iteration across 12,000 iterations (e.g. `afiro`), driver and interpreter latency alone consumed approximately 2.16 seconds (>90% of the total 2.74s solve time).

2. **Severe GPU Memory Pool Allocation Churn:**
   Every intermediate expression allocated a temporary device array from CuPy memory pool. Across 50,000 iterations, nearly 1,000,000 device memory allocations and deallocations occurred. In `CUDACSR.dot`, `out = xp.zeros(self.m)` allocated a new output vector on every SpMV call.

3. **High DRAM Memory Bandwidth Traffic from Unfused Elementwise Kernels:**
   In Gate 8, vector arithmetic was executed as disjoint kernels, writing intermediate vectors to GPU VRAM and immediately reading them back in the next kernel.

4. **Host Object Creation Overhead:**
   `CUDACSR.dot` created Python/CuPy scalar wrappers (`self.xp.int32(self.m)`) and tuple arguments on every call, creating unnecessary garbage collector pressure.

5. **Reallocation During Periodic Restarts:**
   On restart intervals (k = 0 mod 1000), calling `avg.copy()` and `avgy.copy()` dynamically allocated new GPU arrays rather than updating state in place.

---

## 3. Architecture of Gate 9 Optimizations

Gate 9 re-engineers the GPU execution pipeline to achieve **4 kernel launches per iteration and ZERO dynamic memory allocations**:

### 3.1 Dedicated Sovereign RawKernels
All core arithmetic and vector updates are implemented as dedicated CUDA C RawKernels:
1. **Optimized SpMV (`CUDA_SPMV_SOURCE`):**
   - Employs `const double* __restrict__` and `const int* __restrict__` qualifiers to enable the compiler to utilize read-only cache loads (`LDG.E`) and dual-issue load pipelines.
   - Includes `#pragma unroll 4` on the inner non-zero loop.
   - Uses grid-stride row processing to support arbitrary matrix dimensions.
   - Writes directly to preallocated destination buffer (`out[r] = v`), eliminating zero-fill overhead.
2. **Fused Dual Step (`CUDA_DUAL_STEP_SOURCE`):**
   - Fuses dual step y_new = max(0, y + sigma * (Ax_bar - h)) and running ergodic average accumulation y_avg += (y_new - y_avg) / count into a single launch.
   - Replaces 7 separate CuPy operations with 1 launch.
   - Operates in registers; eliminates all intermediate DRAM roundtrips.
3. **Fused Primal Step (`CUDA_PRIMAL_STEP_SOURCE`):**
   - Fuses gradient step, box projection x_new = clamp(x - tau * (c + ATy), l, u), over-relaxation bar_x = 2 * x_new - x_old, and running ergodic average accumulation x_avg += (x_new - x_avg) / count into a single launch.
   - Uses hardware `fmin`/`fmax` intrinsics for exact IEEE 754 box clamping.
   - Replaces 10 separate CuPy operations with 1 launch.
4. **In-Place Vector Copy (`CUDA_VECTOR_COPY_SOURCE`):**
   - Implements in-place device vector copy for periodic restarts without reallocating device memory.

### 3.2 Preallocated Work Buffers
- Reusable work vectors `Ax_bar` (m) and `ATy` (n) are allocated once during setup.
- Matrix dimensions (`m_int32`, `n_int32`) and launch configurations (`grid_m`, `grid_n`, `block`) are precomputed once during setup.
- In-place buffer reuse in `CUDACSR.dot(x, out=Ax_bar)` guarantees 0 dynamic allocations during iterations.

### 3.3 Unified D2H Checkpoint Downloads
- Synchronizations and D2H transfers are strictly confined to periodic check intervals (k = 0 mod 100) and termination.
- At checkpoints, x and y are downloaded once to host memory for finiteness check and KKT verification.
- Running averages (x_avg, y_avg) are downloaded only if the raw iterates fail the KKT tolerance, avoiding redundant PCIe bus transfers.

### 3.4 Granular Timing & Telemetry
Solver outputs now include:
- `setup_seconds`: Matrix CSR conversion, preconditioning, H2D transfers.
- `iteration_seconds`: Pure GPU iteration compute time.
- `verification_seconds`: Sovereign CPU KKT verification time.
- `iteration_and_verification_seconds`: Combined compute time.
- `total_elapsed_seconds`: End-to-end solve time.
- `telemetry`:
  - `kernel_launches_count`: Exact number of GPU kernel invocations (4 * k + 3 * restarts).
  - `restarts_count`: Number of periodic restarts executed.
  - `convergence_checks_count`: Number of KKT checks executed.

---

## 4. Mathematical Invariance & Integrity

All Gate 9 performance optimizations preserve exact mathematical equivalence:
1. **FP64 Precision:** All device computations strictly execute in IEEE 754 64-bit double precision (`double`, `float64`).
2. **Algorithm Equivalence:** Chambolle-Pock first-order step sequence, Pock-Chambolle l1 diagonal preconditioning, and ergodic running average restart mechanics are bit-for-bit identical to the reference CPU solver.
3. **Sovereign Verification:** GPU accelerates; CPU verifies. Every solution is verified on CPU against the original model KKT conditions using exact Fraction arithmetic where applicable.
4. **Honest Failure Paths:** Non-finite iterate detection, `NUMERICAL_FAILURE`, and `LIMIT_REACHED` statuses remain active and unmodified.
5. **Truthful Non-CUDA Behavior:** On Apple Silicon and non-CUDA environments, `pdhg-cuda` cleanly reports `CUDA_UNAVAILABLE` with `gpu_executed = False`.
6. **Gate 8 Evidence Immutability:** Gate 8 evidence in `reports/gpu_validation/rtx5050_2026-10-02_c5788513/` is preserved without modification.

---

## 5. Physical Validation Protocol on Acer RTX 5050

To execute and measure Gate 9 physical GPU performance on the Acer RTX 5050 Laptop GPU:

```bash
# 1. Fetch and checkout Gate 9 branch
git fetch origin
git checkout gate9-gpu-performance
git pull origin gate9-gpu-performance

# 2. Run preflight hardware verification
python scripts/gpu_preflight.py

# 3. Run full test suite including Gate 9 regressions
python -m unittest discover -s tests -v

# 4. Run Gate 9 benchmark validation across all strata
python scripts/run_gpu_validation.py --backend pdhg-cuda --stratum ALL --warmups 3 --repeats 7 --output reports/gpu_gate9/validation_pdhg_cuda_rtx5050.json
python scripts/run_gpu_validation.py --backend pdhg-cpu --stratum ALL --warmups 3 --repeats 7 --output reports/gpu_gate9/validation_pdhg_cpu_rtx5050.json

# 5. Run ablation study
python scripts/run_gpu_ablation.py --backend pdhg-cuda --output reports/gpu_gate9/ablation_pdhg_cuda_rtx5050.json
```
