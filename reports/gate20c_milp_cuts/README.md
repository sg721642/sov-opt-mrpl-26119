# Gate 20C: Sovereign MILP Cutting-Plane Infrastructure & Empirical Evaluation

**Hardware**: Apple Silicon (MacBook Air)
**Base Commit**: `d165b9e437644c276f817e2a4325d14fa89aeb32`
**Classification**: **B. CUTS IMPROVE ROOT RELAXATION ON TESTED CASES**

---

## 1. Executive Summary

Gate 20C introduces a **safe, mathematically sound cutting-plane separation and injection layer** into the SOV-OPT sovereign MILP engine (`sovopt/milp.py`, `sovopt/cuts.py`).

Following the strict integrity rules of SIH Problem Statement 26119 and `AGENTS.md`:
- **Zero external solver dependencies**: Implemented using pure NumPy and Python standard library.
- **Strict cut validity & safety gates**: Every generated cut is verified against numerical sanity checks (no NaNs, finite bounds, minimum/maximum norm, violation threshold $\ge 10^{-4}$, parallel angle screening) before injection.
- **Formal Gomory / GMI feasibility audit**: A mathematical audit of `sovopt/dual_simplex.py` determined that internal dual simplex does not currently expose a stable tableau row or basis inverse $B^{-1}$ API. Rather than risking cut invalidity or tableau indexing errors, **Option C (Defer Gomory, Cover Cuts Only)** was formally adopted.
- **Empirical validation**:
  - **Public Findings**: Validated binary cover cuts improved root relaxation and reduced branch-and-bound nodes by 40–54.5% on targeted knapsack/oracle MILPs. Across the 38-instance authentic MIPLIB pass, the cut-enabled configuration produced no correctness regressions and no overall measurable improvement.
  - **Refinery Evaluation**: Representative refinery MILP remained OPTIMAL_VERIFIED with identical objective and node count; its continuous-coupled rows were conservatively excluded from binary cover separation.
  - **Gomory/GMI Decision**: Gomory/GMI separation was deliberately deferred because the current dual simplex interface does not expose a proof-safe original-space tableau/basis mapping.
  - **MIPLIB & gen-ip002 Accounting**: Evaluated 38 authentic MIPLIB instances (0 improved, 38 unchanged, 0 worsened, 0 correctness disagreements, 0 cut-caused numerical failures). For `gen-ip002` specifically: node-count difference observed around the later numerical basis-condition failure (node 41 ON vs 39 OFF at ~10.0s timeout), but no cover cut was accepted/applied, so this is not attributed as a cut improvement or cut regression.

---

## 2. Cutting Plane Architecture & Safety Contract

The cutting plane infrastructure is implemented in `sovopt/cuts.py`:

```
                           +----------------------------+
                           |  Root LP Relaxation Solved |
                           +--------------+-------------+
                                          |
                                          v
                           +----------------------------+
                           | Separate Binary Cover Cuts |
                           +--------------+-------------+
                                          |
                                          v
+------------------+       +----------------------------+
|  Numerical Gate  | ----> |  validate_cut()            |
|  (Norm/NaN/Inf)  |       |  - violation >= 1e-4       |
+------------------+       |  - condition & norm bounds |
                           +--------------+-------------+
                                          |
                                          v
                           +----------------------------+
                           |  CutPool Check             |
                           |  - parallel cosine test    |
                           |  - duplicate suppression   |
                           +--------------+-------------+
                                          |
                                          v
                           +----------------------------+
                           |  Inject Cuts into Model    |
                           |  Append to Dense or CSR A  |
                           +--------------+-------------+
                                          |
                                          v
                           +----------------------------+
                           | Re-solve LP Relaxation     |
                           +----------------------------+
```

### Safety Features:
1. **Separation**: Identifies minimal binary covers on constraints of the form $\sum_{j \in C} a_j x_j \le b$ where $x_j \in \{0, 1\}$.
   - If $\sum_{j \in C} a_j > b$, the valid inequality $\sum_{j \in C} x_j \le |C| - 1$ is separated.
   - Greedy reduction guarantees the cover is minimal (dropping any variable makes the sum $\le b$).
2. **Strict refusal on mixed constraints**: Any row containing continuous variables or negative coefficients is conservatively skipped.
3. **CutPool**: Enforces cosine orthogonality ($\cos \theta < 0.999$) to prevent adding collinear or duplicate rows to the LP tableau.
4. **Sparse & Dense Agnostic**: `append_rows_to_matrix` seamlessly updates both dense NumPy arrays and `CSRMatrix` representations.

---

## 3. Gomory / GMI Feasibility Audit: Option C Selection

A complete audit of `sovopt/dual_simplex.py` was conducted (`reports/gate20c_milp_cuts/gomory_feasibility.md`).

Key findings:
- The dual simplex solver transforms bounded variables internally via shifts, box transformations, and slack insertion.
- The basis factorizations ($L, U$) and intermediate tableau representations are purely local to `_iterate()` and are discarded upon return.
- Deriving valid Gomory mixed-integer (GMI) cuts requires reconstructing the exact simplex tableau row:
  $$\bar{a}_{i,j} = (B^{-1} A)_{i,j}$$
  relative to the *original* variable space, accounting for non-basic slack variables and postsolve shifts.
- Without an explicit basis export API, attempting Gomory cuts would introduce severe risks of invalid cuts (cutting off integer feasible points).

**Decision**: Formally select **Option C: NOT SAFE YET — COVER CUTS ONLY**.
This guarantees zero invalid cuts in Gate 20C while preserving the mathematical integrity of the solver.

---

## 4. Empirical Evaluation Results

### A. Small Exact Oracle Suite (9 Instances)
Every generated cut was verified against the full $2^n$ binary lattice.

| Instance | OFF Status (Obj) | ON Status (Obj) | Nodes (OFF -> ON) | Cuts Acc | Root Bound (OFF -> ON) | Agreement |
|---|---|---|---|---|---|---|
| `binary_knapsack_1` | OPTIMAL_VERIFIED (12.0) | OPTIMAL_VERIFIED (12.0) | 19 -> **11** (-42.1%) | 2 | -12.5 -> **-12.333** | **TRUE** |
| `multi_knapsack` | OPTIMAL_VERIFIED (59.0) | OPTIMAL_VERIFIED (59.0) | 31 -> **15** (-51.6%) | 6 | -63.038 -> **-62.559** | **TRUE** |
| `weak_lp_relaxation`| OPTIMAL_VERIFIED (1.0) | OPTIMAL_VERIFIED (1.0) | 11 -> **5** (-54.5%) | 2 | -1.5 -> -1.5 | **TRUE** |
| `fractional_root` | OPTIMAL_VERIFIED (4.0) | OPTIMAL_VERIFIED (4.0) | 5 -> **3** (-40.0%) | 1 | -4.667 -> **-4.000** | **TRUE** |
| `general_integer_box`| OPTIMAL_VERIFIED (5.0) | OPTIMAL_VERIFIED (5.0) | 3 -> 3 (0.0%) | 0 | 4.5 -> 4.5 | **TRUE** |
| `negative_objective`| OPTIMAL_VERIFIED (-25.0) | OPTIMAL_VERIFIED (-25.0)| 1 -> 1 (0.0%) | 0 | -25.0 -> -25.0 | **TRUE** |
| `infeasible_milp` | INFEASIBLE_CERTIFIED | INFEASIBLE_CERTIFIED | 1 -> 1 (0.0%) | 0 | None -> None | **TRUE** |
| `multiple_optima` | OPTIMAL_VERIFIED (1.0) | OPTIMAL_VERIFIED (1.0) | 1 -> 1 (0.0%) | 0 | 1.0 -> 1.0 | **TRUE** |
| `degenerate_small` | OPTIMAL_VERIFIED (0.0) | OPTIMAL_VERIFIED (0.0) | 1 -> 1 (0.0%) | 0 | 0.0 -> 0.0 | **TRUE** |

### B. Refinery MILP Model (Representative Unit Commitment)
- **Model**: 42 variables (6 binary, 36 continuous), 40 constraints.
- **Provenance**: Representative synthetic fixture (`examples/refinery_unit_commitment.py`), strictly NOT proprietary refinery data.
- **Results**:
  - Both configurations produced identical optimal solution: `OPTIMAL_VERIFIED` with objective `-8953.75`.
  - Both explored exactly 9 branch-and-bound nodes (5 pruned).
  - Cuts generated/accepted: **0**.
  - **Scientific Explanation**: Unit commitment binary variables ($u_j \in \{0, 1\}$) are coupled with continuous unit production limits ($x_j \le P_{\max} u_j$). The pure binary cover separator correctly refused mixed rows, ensuring no invalid cuts were applied.

### C. Authentic MIPLIB 38 Suite
All 38 MIPLIB instances evaluated with a 10.0-second timeout per solve:
- **Evaluated**: 38 instances.
- **Agreement**: 100% agreement on all evaluated cases.
- **Cuts Impact**: Most MIPLIB instances are large general mixed-integer programs where binary knapsack rows are either absent or coupled with continuous variables. As expected under Option C, cover cuts did not trigger on general MIPs, avoiding tableau degradation.
- **Timeouts**: 35 instances hit `LIMIT_REACHED` due to the strict 10-second evaluation window.

---

## 5. Summary & Verdict

Gate 20C successfully proves that:
1. Sovereign cutting planes can be integrated safely without modifying existing baseline LP/MIP tolerances.
2. Binary cover cuts provide significant node reductions (up to 54.5%) on knapsack-structured combinatorial models.
3. Strict conservative screening prevents numerical instability on mixed integer/continuous models.
4. The deferral of Gomory cuts (Option C) was the correct, defensible engineering decision.
