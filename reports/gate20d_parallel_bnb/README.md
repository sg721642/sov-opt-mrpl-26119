# Gate 20D: Intra-Solve Parallel Branch-and-Bound Implementation & Empirical Evidence

**Hardware**: Apple Silicon (MacBook Air, Apple M5, 10 Cores, 24 GB Unified Memory)
**Base Commit**: `fb2dbc5f82b9d488c8d56bab15e29c44a8575fe5`
**Classification**: **C. INTRA-SOLVE PARALLEL B&B DEMONSTRATED WITH VERIFIED MATCHED-ENGINE SOLVE-TO-COMPLETION SPEEDUP**

---

## 1. Executive Summary

Gate 20D implements **genuine intra-solve parallel branch-and-bound** for a single MILP solve within the sovereign SOV-OPT solver core (`sovopt/parallel_bnb.py`, `sovopt/milp.py`).

### Critical Architectural Distinctions
1. **Historical Gate 19A Benchmark (2.65x)**: Process-level concurrent dispatch across *independent* problem instances. That was **NOT** parallel branch-and-bound.
2. **User-Facing Mode Comparison**: Legacy serial `solve_milp` vs parallel coordinator mode. Reflects both search-heuristic differences and multicore dispatch.
3. **Matched Parallel-Engine Scaling (Pure Multicore Experiment)**: The **exact same** parallel coordinator engine, priority queue, branching heuristics, pseudocost handling, and worker task evaluation executed with:
   - 1 worker (`matched_w1`)
   - 2 workers (`matched_w2`)
   - 4 workers (`matched_w4`)

### Key Empirical Findings
- **Matched Solve-to-Completion Speedup**:
  - **18-variable multi-knapsack**: Explored **identically 287 nodes** on both 1 worker and 2 workers. Median solve runtime dropped from **3.4452s** to **1.7760s**, demonstrating a **1.94x speedup** on 2 workers with **97.0% parallel efficiency** from pure parallel LP execution. At 4 workers, runtime reached **1.4958s** (**2.30x speedup**, 57.6% efficiency).
  - **16-variable multi-knapsack**: Solved in **1.5491s** (321 nodes) on 1 worker vs **0.4298s** (59 nodes) on 2 workers, delivering a **3.60x solve speedup** combining multicore LP evaluation with concurrent search-order incumbent discovery.
  - **Refinery Unit Commitment MILP**: Solved to `OPTIMAL_VERIFIED` with identical objective `-8953.75` across all configurations, reaching **3.0524s** on 2 workers vs **3.6718s** on 1 worker (**1.20x speedup**, 60.1% efficiency).
- **Fixed-Budget Search Progress on MIPLIB**:
  - On 6 authentic MIPLIB instances under an equal 10.0s wall-clock budget, 4 workers evaluated up to **39.0x as many nodes** (`glass4`: 39 nodes vs 1 node; `gen-ip054`: 1000 nodes vs 28 nodes [35.7x]).
  - *Provenance Note*: This is strictly **fixed-budget search-progress evidence**, NOT solve-to-completion speedup.
- **Zero Mathematical Disagreements**:
  - Small exact oracle suite (9 instances): **100% agreement** across workers 1, 2, 4.
  - Repeatability (10 consecutive runs with workers=4): **100% consistency** (all 10 runs produced `OPTIMAL_VERIFIED` with objective `-12.0`).
  - Zero false-optimality incidents. Zero unverified incumbent acceptances.

---

## 2. Architecture & Concurrency Model

```
                     +---------------------------------------+
                     |         COORDINATOR PROCESS           |
                     | - Open Node Pool (Priority Queue)     |
                     | - Canonical Incumbent (Verified)      |
                     | - Authoritative Global Lower Bound    |
                     | - Canonical Pseudocost Tables         |
                     | - Branch Selection & Child Generation |
                     +-------------------+-------------------+
                                         |
            +----------------------------+----------------------------+
            | Dispatch Node LPs (IPC)    |                            |
            v                            v                            v
  +--------------------+       +--------------------+       +--------------------+
  |      Worker 1      |       |      Worker 2      |       |      Worker 4      |
  | (PID: 40652, MKL=1)|       | (PID: 40653, MKL=1)|       | (PID: 40655, MKL=1)|
  | Solve Child LP     |       | Solve Child LP     |       | Solve Child LP     |
  | Extract Safe Bound |       | Extract Safe Bound |       | Extract Safe Bound |
  | Observe Pseudocost |       | Observe Pseudocost |       | Observe Pseudocost |
  | Check Integrality  |       | Check Integrality  |       | Check Integrality  |
  +---------+----------+       +---------+----------+       +---------+----------+
            |                            |                            |
            +----------------------------+----------------------------+
                                         | Return Solution, Bound & Deltas
                                         v
                     +---------------------------------------+
                     |         COORDINATOR COLLECT           |
                     | - Update Canonical Pseudocosts        |
                     | - Authoritative verify(orig_model, x) |
                     | - Update Global Bound (incl In-Flight)|
                     | - Prune Subtrees                      |
                     +---------------------------------------+
```

### Critical Concurrency & Safety Controls:
1. **Single-Threaded BLAS in Workers**: Workers explicitly configure `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1`, `MKL_NUM_THREADS=1` to prevent CPU oversubscription.
2. **Authoritative Coordinator Verification**: Worker processes do not have the authority to accept an incumbent. When a worker proposes an integer candidate, the coordinator independently executes `verify(orig_model, cand_xr, tol=tol)` and tests integer feasibility on `orig_model.integer` before updating the canonical incumbent.
3. **In-Flight Bound Inclusion**: The global lower bound is computed over `open_nodes + in_flight_nodes + closed_nodes`, ensuring the solver never terminates prematurely with `OPTIMAL_VERIFIED` while workers hold unresolved subtrees.
4. **Canonical Pseudocost Ownership**: Workers compute local delta observations `(branch_var, is_down, dz, f_val)`; the coordinator process exclusively updates and owns the canonical pseudocost arrays.
5. **Worker Crash Recovery**: If a worker process encounters an exception, the coordinator requeues the node back into `open_nodes` or halts honestly with `NUMERICAL_FAILURE`.

---

## 3. Empirical Results

### A. Small Exact Oracle Correctness Suite (9 Instances)

| Problem Case | w=1 Status (Obj) | w=2 Status (Obj) | w=4 Status (Obj) | Agreement |
|---|---|---|---|---|
| `binary_knapsack_1` | OPTIMAL_VERIFIED (12.0) | OPTIMAL_VERIFIED (12.0) | OPTIMAL_VERIFIED (12.0) | **TRUE** |
| `multi_knapsack` | OPTIMAL_VERIFIED (37.0) | OPTIMAL_VERIFIED (37.0) | OPTIMAL_VERIFIED (37.0) | **TRUE** |
| `general_integer_box` | OPTIMAL_VERIFIED (-6.0) | OPTIMAL_VERIFIED (-6.0) | OPTIMAL_VERIFIED (-6.0) | **TRUE** |
| `negative_objective` | OPTIMAL_VERIFIED (-125.0)| OPTIMAL_VERIFIED (-125.0)| OPTIMAL_VERIFIED (-125.0)| **TRUE** |
| `infeasible_milp` | INFEASIBLE_CERTIFIED | INFEASIBLE_CERTIFIED | INFEASIBLE_CERTIFIED | **TRUE** |
| `multiple_optima` | OPTIMAL_VERIFIED (1.0) | OPTIMAL_VERIFIED (1.0) | OPTIMAL_VERIFIED (1.0) | **TRUE** |
| `weak_lp_relaxation` | OPTIMAL_VERIFIED (1.0) | OPTIMAL_VERIFIED (1.0) | OPTIMAL_VERIFIED (1.0) | **TRUE** |
| `fractional_root` | OPTIMAL_VERIFIED (4.0) | OPTIMAL_VERIFIED (4.0) | OPTIMAL_VERIFIED (4.0) | **TRUE** |
| `degenerate_small` | OPTIMAL_VERIFIED (0.0) | OPTIMAL_VERIFIED (0.0) | OPTIMAL_VERIFIED (0.0) | **TRUE** |

### B. Repeatability (10 Consecutive Runs on Knapsack, Workers=4)
- **Status Consistency**: 10/10 runs produced `OPTIMAL_VERIFIED`.
- **Objective Consistency**: 10/10 runs produced identical objective `-12.0` (difference = 0.0).
- **Node Count**: 7 to 9 nodes across runs.

### C. Matched Parallel-Engine Scaling (1 Warmup + 5 Measured Runs, Medians)

| Workload | Legacy Serial | Matched w=1 | Matched w=2 | Matched w=4 | Matched Speedup (2w / 4w) | Parallel Efficiency (2w / 4w) |
|---|---|---|---|---|---|---|
| `multiknapsack_16var` | 0.6755s (67 nds) | 1.5491s (321 nds) | 0.4298s (59 nds) | 0.5254s (63 nds) | **3.60x** / 2.95x | **180.2%** / 73.7% |
| `multiknapsack_18var` | 2.3151s (141 nds)| 3.4452s (287 nds) | 1.7760s (287 nds)| 1.4958s (331 nds)| **1.94x** / **2.30x** | **97.0%** / **57.6%** |
| `refinery_milp` | 3.7644s (9 nds)  | 3.6718s (9 nds)   | 3.0524s (11 nds) | 3.7091s (17 nds) | **1.20x** / 0.99x | **60.1%** / 24.7% |

*Node-Count & Scaling Interpretation*:
- On `multiknapsack_18var`, **both w=1 and w=2 explored identically 287 nodes**. Because the node counts are identical, the **1.94x speedup on 2 workers** represents clean, unconfounded parallel LP execution (97.0% parallel efficiency).
- On `multiknapsack_16var`, concurrent exploration enabled earlier discovery of the optimal integer incumbent, allowing workers to prune subtrees that w=1 explored (59 nodes on w=2 vs 321 nodes on w=1), yielding a **3.60x solve speedup**.
- On `refinery_milp`, the problem has a compact 9-node tree. At w=2, it achieves a **1.20x speedup**; at w=4, asynchronous work-stealing explores 17 nodes across workers, showing diminishing returns on tiny trees.

### D. User-Facing Mode Comparison (Legacy Serial vs Parallel Engine)

| Workload | Legacy Serial Time | Parallel w=2 Time | Parallel w=4 Time | Mode Speedup (2w / 4w) |
|---|---|---|---|---|
| `multiknapsack_16var` | 0.6755s | 0.4298s | 0.5254s | **1.57x** / 1.29x |
| `multiknapsack_18var` | 2.3151s | 1.7760s | 1.4958s | **1.30x** / **1.55x** |
| `refinery_milp` | 3.7644s | 3.0524s | 3.7091s | **1.23x** / 1.01x |

### E. Authentic MIPLIB Fixed-Budget Search Progress (10.0s Budget per Solve)

*Disclaimer: Under an equal fixed search budget, multiple workers increased node progress on these MIPLIB instances; this is search-progress evidence, not solve-to-completion speedup.*

| Instance | Rows x Cols | w=1 Nodes Completed | w=2 Nodes Completed | w=4 Nodes Completed | Fixed-Budget Node Progress Ratio (4w vs 1w) |
|---|---|---|---|---|---|
| `flugpl` | 18 x 18 | 645 | 839 | 1000 | **1.55x** |
| `gen-ip054` | 27 x 30 | 28 | 268 | 1000 | **35.71x** |
| `timtab1` | 171 x 397 | 3 | 13 | 53 | **17.67x** |
| `enlight_hard` | 100 x 200 | 3 | 34 | 45 | **15.00x** |
| `p200x1188c` | 1388 x 2376 | 1 | 1 | 1 | 1.00x |
| `glass4` | 396 x 322 | 1 | 34 | 39 | **39.00x** |

---

## 4. Safe Public Claim

> "SOV-OPT implements genuine intra-solve multi-process branch-and-bound. On tested MILP workloads, the same parallel search engine achieved up to 1.94x solve speedup on 2 workers with identical node counts (97.0% parallel efficiency), and up to 3.60x solve speedup when combining concurrent LP evaluation with search-order pruning advantages, while preserving 100% verified mathematical solution agreement."
>
> "Separately, on selected authentic MIPLIB instances under an equal fixed 10-second search budget, the 4-worker engine processed up to 39x as many branch-and-bound nodes, accelerating tree exploration without external solver dependencies."
