# Gate 20B — Physical RTX 5050 True-Sparse CUDA Validation

## Executive Summary

- **Hardware Platform:** Acer Nitro V 16S (ANV16S-71)
- **CPU:** Intel(R) Core(TM) 5 210H (8 Cores, 12 Threads)
- **RAM:** 16 GB DDR5 (16,785,596,416 bytes)
- **GPU:** NVIDIA GeForce RTX 5050 Laptop GPU (Compute Capability 12.0)
- **VRAM:** 8150.6 MiB
- **NVIDIA Driver:** 576.83 | **CUDA Runtime:** 12.9 | **CuPy:** 14.2.0
- **OS:** Windows 11 Home (Build 26200)
- **Commit SHA:** `9fc1d17682551833ed39f4eace99f49076a21a8c`
- **Execution Date:** 2026-10-05
- **Power Mode:** Best Performance (Plugged in)
- **Provenential Statement:** "Physical Acer RTX 5050 validation — not executed on Render."

---

## True-Sparse Synthetic Performance Summary Table

| Tier | Variables | Constraints | Nonzeros | Seed | CPU Median | CUDA Median | CPU/CUDA | CPU Status | CUDA Status | Verification | Qualification |
|:---:|----------:|------------:|---------:|:---:|-----------:|------------:|---------:|-----------:|------------:|-------------|--------------|
| Tier 1 | 10,000 | 5,000 | 29,994 | 51 | 57.7534s | 9.9461s | **5.81x** **(CROSSOVER)** | LIMIT_REACHED | LIMIT_REACHED | LIMIT_REACHED_CONSISTENT | VALID_COMPARISON |
| Tier 2 | 25,000 | 12,500 | 74,995 | 52 | 120.0248s | 25.0887s | NOT DETERMINED | LIMIT_REACHED (TIMEOUT > 120s) | LIMIT_REACHED | UNVERIFIED — INVALID FOR SPEEDUP CLAIM | UNVERIFIED |
| Tier 3 | 50,000 | 25,000 | 149,988 | 53 | 180.0315s | 33.4010s | NOT DETERMINED | LIMIT_REACHED (TIMEOUT > 180s) | LIMIT_REACHED | UNVERIFIED — INVALID FOR SPEEDUP CLAIM | UNVERIFIED |
| Tier 4 | 100,000 | 50,000 | 299,993 | 54 | 180.0271s | 67.2309s | NOT DETERMINED | LIMIT_REACHED (TIMEOUT > 180s) | LIMIT_REACHED | UNVERIFIED — INVALID FOR SPEEDUP CLAIM | UNVERIFIED |
| Tier 5 | 250,000 | 125,000 | 749,995 | 55 | 240.0200s | 240.0216s | NOT DETERMINED | LIMIT_REACHED (TIMEOUT > 240s) | LIMIT_REACHED (TIMEOUT > 240s) | LIMIT_REACHED_CONSISTENT | TIME_LIMIT_NO_SPEEDUP_INFERENCE |
| Tier 6 | 500,000 | 250,000 | 1,499,992 | 56 | 240.0235s | 240.0147s | NOT DETERMINED | LIMIT_REACHED (TIMEOUT > 240s) | LIMIT_REACHED (TIMEOUT > 240s) | LIMIT_REACHED_CONSISTENT | TIME_LIMIT_NO_SPEEDUP_INFERENCE |
| Tier 7 | 1,000,000 | 500,000 | 2,999,993 | 57 | 60.0000s | 60.0000s | NOT DETERMINED | LIMIT_REACHED (TIMEOUT > 60s) | LIMIT_REACHED (TIMEOUT > 60s) | LIMIT_REACHED_CONSISTENT | TIME_LIMIT_NO_SPEEDUP_INFERENCE |

---

## Authentic Mittelmann Physical CUDA Evaluation Table

| Instance | Rows | Cols | Nonzeros | Parse Time | CPU Time | CUDA Time | CPU Status | CUDA Status | GPU Executed |
|:---|---:|---:|---:|---:|---:|---:|:---|:---|:---:|
| `qap15` | 6,330 | 22,275 | 94,950 | 0.2357s | 60.00s | 18.83s | LIMIT_REACHED (TIMEOUT > 60s) | LIMIT_REACHED | YES |
| `brazil3` | 14,646 | 23,968 | 133,184 | 0.4242s | 60.00s | 29.86s | LIMIT_REACHED (TIMEOUT > 60s) | LIMIT_REACHED | YES |
| `chromaticindex1024-7` | 67,583 | 73,728 | 270,324 | 1.2229s | 60.00s | 80.21s | LIMIT_REACHED (TIMEOUT > 60s) | OPTIMAL_VERIFIED | YES |
| `supportcase10` | 165,684 | 14,770 | 555,082 | 1.7431s | 60.00s | 58.17s | LIMIT_REACHED (TIMEOUT > 60s) | LIMIT_REACHED | YES |

---

## Key Findings

- **First Valid GPU Crossover Size:** **10,000 variables**
- **Best Valid Same-Machine CPU/CUDA Ratio:** **5.81x** (at Tier 10000)
- **Speedup Definition:** `speedup = CPU_median / CUDA_median` (>1.0 indicates CUDA faster)
- **Scientific Classification:** `C. MEANINGFUL GPU ACCELERATION DEMONSTRATED ON TESTED TRUE-SPARSE WORKLOADS (5.81x at Tier 10000)`

---

## Methodology & Safety Compliance

1. **True Sovereign Sparse Representation:** CPU and CUDA were evaluated on exact mathematically identical bounded, feasible sparse LP instances using sovereign `CSRMatrix` representations with zero dense $m \times n$ array allocations.
2. **Device Memory Residency:** CSR indptr/indices/data buffers and iterate vectors remained resident on GPU memory during iteration loops.
3. **Subprocess Isolation & Hard Timeouts:** Each individual solve was executed in an isolated child process with hard wall-clock timeouts (120s–240s).
4. **Synchronized CUDA Timing:** CUDA timers included explicit stream synchronization (`cp.cuda.Stream.null.synchronize()`) before recording end times.
5. **Authentic Mittelmann Parsing:** Evaluated compressed `.mps.bz2` Mittelmann instances directly using sovereign sparse MPS ingestion.
6. **Historical Gate Protection:** Historical evidence from Gate 8, Gate 9, Gate 18, Gate 19A, Gate 19B, and Gate 20A remains strictly untouched and preserved.

---

*Report generated automatically by `scripts/run_gpu_sparse_gate20b.py` on 2026-10-05.*
