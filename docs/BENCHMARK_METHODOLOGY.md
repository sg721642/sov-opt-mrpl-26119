# Benchmark Methodology & Integrity Guarantees — SOV-OPT

**MRPL SIH Problem Statement 26119**  
**Solver Version:** `0.3.1` (Gate 7 Complete)  
**Sovereign Solver Core:** Python standard library and NumPy only.  
**Differential Solvers:** HiGHS / SciPy invoked exclusively in isolated subprocess worker processes.

---

## 1. Core Principles of Benchmark Integrity

Benchmarking in SOV-OPT is governed by strict scientific integrity guarantees to prevent bias, cherry-picking, and false performance claims:

1. **Primary Official Sources Only:**
   - **Netlib LP:** Retrieved from official Netlib repository (`https://www.netlib.org/lp/data/` and `/infeas/`), unpacked using authentic Bell Labs `emps` decompressor.
   - **MIPLIB 2017:** Retrieved from Zuse Institute Berlin (`https://miplib.zib.de/`), anchored against the official ground-truth solution file `miplib2017-v37.solu`.
   - **QPLIB 2018:** Retrieved from Zuse Institute Berlin (`https://qplib.zib.de/`), verified against published literature solutions (Furini et al., 2019).
2. **Frozen Manifests Before Solving:**
   - Candidate instance sets, bounding boxes, and SHA-256 digests are permanently frozen in machine-readable manifests (`data/manifests/netlib_lp.json`, `data/manifests/miplib_milp.json`, `data/manifests/qplib_convex_qp.json`, `data/manifest.json`) and documented in `reports/FROZEN_BENCHMARK_SELECTION.md` prior to executing benchmark runs.
3. **Strict Prohibition of Cherry-Picking:**
   - Every candidate instance included in the frozen manifest must be evaluated and reported. Failed instances (`NUMERICAL_FAILURE`, `LIMIT_REACHED`, `UNSUPPORTED`) are displayed prominently in summary tables alongside passing instances. No instance may be removed or replaced post-hoc to inflate success rates.
4. **Zero Synthetic Benchmarks in Public Aggregates:**
   - Synthetic fixtures and the MRPL refinery twin are strictly segregated from public benchmark metrics. Headline benchmark tables contain 100% public, peer-reviewed, independently verifiable instances.

---

## 2. MIPLIB 2017 Stratification & Ground Truth Grounding

MIPLIB 2017 Benchmark Set v2 comprises 240 diverse, challenging mixed-integer linear programs. To evaluate solver capabilities systematically across problem scales, instances compatible with standard MPS semantics were classified into four deterministic size bins:

| Bin | Variable Count ($n$) | Constraint Count ($m$) | Nonzeros ($nnz$) | Instances | Benchmark Purpose |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Bin 1: Tiny** | $n < 200$ | $m < 200$ | $nnz \le 2000$ | 5 | Exact search tree exploration, root LP relaxation, integer leaf fathoming |
| **Bin 2: Small** | $200 \le n < 600$ | $m < 600$ | $nnz \le 5000$ | 15 | Pseudocost branching, dual warm restarts, safe lower bound evaluation |
| **Bin 3: Medium** | $600 \le n < 1500$ | $m < 1500$ | $nnz \le 10000$ | 10 | Search frontier scalability, memory boundaries, node budget limits |
| **Bin 4: Large** | $1500 \le n \le 3000$ | $m \le 3000$ | $nnz \le 15000$ | 8 | Stress limits, honest budget exhaustion (`LIMIT_REACHED`), safe bounding |

### Ground Truth Grounding (`miplib2017-v37.solu`)
Every MIPLIB instance is verified against the official ZIB solution file:
- **Location:** `data/miplib2017-v37.solu`
- **SHA-256:** `04250ce7597bdc14f6341b323c8b4be42416102e370f93102fab1ff1f85aa977`
- **Directional Safety Invariant:** For every minimization instance with reported lower bound $\underline{b}$ and official solution reference $z^*$:
  $$\underline{b} \le z^* + 10^{-6}$$
  Any violation where $\underline{b} > z^*$ triggers an immediate hard assertion failure.

---

## 3. Measurement Protocols & Resource Limits

To guarantee reproducibility and prevent runaway processes:
- **Node Budget:** Default branch-and-bound node budget is fixed at 30 nodes (or 50 nodes for deep ablation).
- **Time Limit:** Each individual node solve and total instance execution is constrained by a strict wall-clock deadline (e.g. 3.0s). Deadlines are evaluated directly within inner simplex pivot loops to guarantee timely termination.
- **Memory & Dimension Limits:** Dense representations are guarded by strict pre-allocation checks ($n \le 5000$, $\text{memory} \le 250$ MB). Models exceeding bounds are rejected cleanly before allocation.
- **Hardware Telemetry:** Every solve record logs machine architecture (`platform.machine()`), core count, Python version, NumPy version, and git commit SHA.

---

## 4. Differential Verification Rules (HiGHS / SciPy)

Differential verification validates SOV-OPT outputs against trusted external solvers under strict procedural boundaries:
1. **Subprocess Isolation:** External solvers (`highspy`, `scipy`) are executed exclusively within independent worker subprocesses (`scripts/baseline_worker.py`) using a separate benchmark virtual environment (`.venv-benchmark/`).
2. **Zero Influence on Sovereign Path:** External solvers are never imported, linked, or invoked from `sovopt/` or `server.py`. They have zero influence on internal solution paths, basis selections, or certificates.
3. **No Unwarranted Speedup Claims:** Pivot count reductions (e.g., warm dual-simplex reoptimization reducing pivots by 81.3% on FLUGPL) must not be reported as end-to-end runtime speedups without verified, measured wall-clock evidence.

---

## 5. Separation of Industrial Refinery Twin

The MRPL Refinery Planning Digital Twin (`sovopt/refinery_twin.py`) represents a multi-period refinery planning formulation based on open literature:
- It contains **no proprietary MRPL operational data**, proprietary crude assays, or confidential refinery recipes.
- It is evaluated solely to demonstrate solver versatility across 4 operational paradigms (LP, MILP, QP, Infeasible Farkas).
- It is strictly segregated from public benchmark tables in `reports/VERIFIED_BENCHMARKS.md` and excluded from all statistical aggregations.
 
---

## 6. Convex QP Interior-Point Benchmark Methodology (Gate 7.2)

Public continuous convex quadratic programs from QPLIB 2018 (`https://qplib.zib.de/`) are evaluated under strict mathematical integrity rules:
1. **Direct Equality-Aware Saddle-Point Architecture:**
   - Problem constraints are partitioned into native equalities ($E x = f$) and genuine inequalities ($G x \le h$).
   - Direct augmented saddle-point Newton systems of size $(n + m_e) \times (n + m_e)$ avoid artificial inequality-slack duplication that would otherwise destroy the relative interior.
   - Quasidefinite regularization ($\delta_p, \delta_d = 10^{-12}$) and iterative refinement guarantee numerical stability without altering the mathematical optimum.
2. **Strict Internal Initialization:**
   - The interior-point solver uses 100% internal starting point generation (`initialization_source = 'SOVOPT_INTERNAL'`).
   - Official published solution vectors (`.sol`) are never read, accessed, or used in the search trajectory or starting point.
   - Proof of independence is verified programmatically in `tests/test_qplib.py` (`test_18_no_reference_leakage_when_sol_file_hidden`).
3. **Rigorous Original-Model KKT Verification:**
   - Every reported solve is verified against the original untransformed model at tolerance $10^{-7}$:
     - Primal feasibility: $\|E x - f\|_\infty \le 10^{-7}, G x \le h + 10^{-7}$
     - Dual feasibility: $z \ge -10^{-7}$
     - Stationarity: $\|Q x + c + E^T y + G^T z\|_\infty / (1 + \|c\|_\infty + \|Q x\|_\infty) \le 10^{-7}$
     - Complementarity: $z^T (h - G x) / (1 + |c^T x + \frac{1}{2} x^T Q x|) \le 10^{-7}$
4. **Segregation of Reference Solution Comparisons:**
   - Published reference objectives are recorded in separate differential comparison columns.
   - Independent sovereign solves (`QPLIB_8845`, `QPLIB_9002`) are verified and recorded as `OPTIMAL_VERIFIED` with evidence source `SOVOPT_SOLVER`.
5. **Memory and Dimension Boundaries:**
   - Dense $Q$ allocation is strictly bounded by a 250 MB memory guard.
   - Large instances (`QPLIB_8938`, 488 MB) are honestly reported as `UNSUPPORTED_RESOURCE_LIMIT` without crashing or allocating.
   - Nonconvex instances (`QPLIB_0018`) are rejected cleanly with `UNSUPPORTED_NONCONVEX_QP`.
