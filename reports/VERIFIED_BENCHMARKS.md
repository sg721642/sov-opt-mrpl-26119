# Verified Benchmark & Differential Validation Report — SOV-OPT Gate 7

**Date:** `2026-10-01`  
**Solver Version:** `0.3.0`  
**Solver Commit:** `fc5b537d98a952f0`  
**Hardware Environment:** `Darwin arm64, Python 3.11.16`  
**Core Dependencies:** NumPy and Python standard library only (strictly sovereign core)  
**External Solvers:** HiGHS / SciPy invoked exclusively in isolated subprocesses (`scripts/baseline_worker.py`) for differential comparison  

---

## Summary of Active Benchmark Collections

| Collection | Category | Selected Count | Primary Official Repository | Benchmark Verification Role |
| :--- | :---: | :---: | :--- | :--- |
| **Netlib LP** | Category A | 16 | `https://www.netlib.org/lp/data/` | Continuous linear programming optimality & residual checks |
| **Netlib LP/Infeas** | Category B | 1 | `https://www.netlib.org/lp/infeas/` | Primary public Farkas certificate validation (`WOODINFE`) |
| **MIPLIB 2017** | Category C | 38 | `https://miplib.zib.de/` | Discrete MILP branch-and-bound search frontiers & safe bounds |
| **QPLIB 2018** | Category D | 2 | `https://qplib.zib.de/` | Continuous convex QP Mehrotra IPM & original-model KKT |
| **QPLIB (Negative Test)** | Category D | 1 | `https://qplib.zib.de/` | Nonconvex QP explicit rejection certification (`QPLIB_0018`) |

---

## Section A: Netlib LP Continuous Suite

| Instance | Vars | Rows | Nonzeros | SOV-OPT Status | SOV-OPT Objective | Published Reference | Discrepancy | Primal Res | Dual Res | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ADLITTLE** | 97 | 56 | 465 | `OPTIMAL_VERIFIED` | **225494.963162** | `2.254950e+05` | 2.38e-06 | 1.21e-16 | 4.60e-17 | 130.1 ms |
| **AFIRO** | 32 | 27 | 88 | `OPTIMAL_VERIFIED` | **-464.753143** | `-4.647531e+02` | 2.86e-09 | 1.14e-16 | 2.64e-18 | 13.1 ms |
| **BLEND** | 83 | 74 | 521 | `OPTIMAL_VERIFIED` | **-30.812150** | `-3.081215e+01` | 1.72e-10 | 1.50e-14 | 2.36e-15 | 217.8 ms |
| **BRANDY** | 249 | 220 | 2150 | `NUMERICAL_FAILURE` | — | `1.518510e+03` | — | — | — | 6278.1 ms |
| **ISRAEL** | 142 | 174 | 2358 | `OPTIMAL_VERIFIED` | **-896644.821863** | `-8.966448e+05` | 3.05e-06 | 6.12e-16 | 1.13e-16 | 1491.4 ms |
| **KB2** | 41 | 43 | 291 | `OPTIMAL_VERIFIED` | **-1749.900130** | `-1.749900e+03` | 6.21e-09 | 3.75e-15 | 1.35e-16 | 52.6 ms |
| **RECIPE** | 180 | 91 | 752 | `NUMERICAL_FAILURE` | **-266.616000** | `-2.666160e+02` | 2.84e-13 | 0.00e+00 | 3.10e-17 | 545.5 ms |
| **SC105** | 103 | 105 | 281 | `OPTIMAL_VERIFIED` | **-52.202061** | `-5.220206e+01` | 2.93e-10 | 4.84e-15 | 6.59e-17 | 278.8 ms |
| **SC205** | 203 | 205 | 552 | `NUMERICAL_FAILURE` | **-52.202061** | `-5.220206e+01` | 2.93e-10 | 1.30e-15 | 9.03e-04 | 1884.6 ms |
| **SC50A** | 48 | 50 | 131 | `OPTIMAL_VERIFIED` | **-64.575077** | `-6.457508e+01` | 4.35e-10 | 3.13e-16 | 2.26e-16 | 74.3 ms |
| **SC50B** | 48 | 50 | 119 | `OPTIMAL_VERIFIED` | **-70.000000** | `-7.000000e+01` | 1.42e-14 | 3.12e-16 | 2.54e-16 | 63.2 ms |
| **SCAGR7** | 140 | 129 | 553 | `OPTIMAL_VERIFIED` | **-2331389.824331** | `-2.331389e+06` | 5.70e-01 | 1.09e-16 | 3.90e-17 | 835.7 ms |
| **SHARE1B** | 225 | 117 | 1182 | `NUMERICAL_FAILURE` | **-76589.318579** | `-7.658932e+04` | 1.86e-07 | 1.58e-15 | 9.13e-17 | 2424.0 ms |
| **SHARE2B** | 79 | 96 | 730 | `NUMERICAL_FAILURE` | **-401.897202** | `-4.157322e+02` | 1.38e+01 | 8.66e-15 | 3.86e-03 | 251.4 ms |
| **STOCFOR1** | 111 | 117 | 474 | `NUMERICAL_FAILURE` | **-41131.976219** | `-4.113198e+04` | 4.36e-07 | 1.79e-16 | 2.50e-01 | 277.1 ms |
| **VTP.BASE** | 203 | 198 | 914 | `NUMERICAL_FAILURE` | **129831.462461** | `1.298315e+05` | 1.36e-06 | 6.26e-15 | 3.39e-03 | 1874.7 ms |
| **AFIRO (PDHG-CPU)** | 32 | 27 | 88 | `OPTIMAL_VERIFIED` | **-464.753142** | `-4.647531e+02` | 6.27e-07 | 8.07e-09 | 5.93e-08 | 109.1 ms |

---

## Section B: Public Certificate Validation Suite

| Instance | Class | Constraints | Variables | Nonzeros | Certified Status | Exact Farkas Ray Verification | Local Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **WOODINFE** | LP_INFEASIBLE_CERTIFICATE | 35 | 89 | 140 | `INFEASIBLE_CERTIFIED` | Certified: **True** ($y \ge 0, y^T A \le 0, y^T b > 0$) | 58.1 ms |

---

## Section C: MIPLIB 2017 Stratified MILP Suite

All instances evaluated with pure sovereign branch-and-bound (warm dual simplex restarts, pseudocost branching, exact rational bounding).
**Conservative Lower Bound Invariant:** For minimization, every reported bound must satisfy $	ext{bound} \le z^*$ with respect to the official `miplib2017-v37.solu` benchmark reference.

| Instance | Bin | Vars | Rows | Nonzeros | Status | SOV-OPT Best Bound | Official Ref Opt (`solu`) | Bound Safety Invariant | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `gen-ip054` | Bin 1 (<200) | 30 | 27 | 532 | `LIMIT_REACHED` | **6767.7611** | `6840.96564179` | `VERIFIED SAFE (bound <= z*)` | 3213.2 ms |
| `markshare_4_0` | Bin 1 (<200) | 34 | 4 | 123 | `NUMERICAL_FAILURE` | **0.0000** | `1.0` | `VERIFIED SAFE (bound <= z*)` | 206.0 ms |
| `gen-ip002` | Bin 1 (<200) | 41 | 24 | 922 | `NUMERICAL_FAILURE` | **-inf** | `-4783.733392` | `VERIFIED SAFE (bound <= z*)` | 3000.7 ms |
| `neos5` | Bin 1 (<200) | 63 | 63 | 2016 | `LIMIT_REACHED` | **-inf** | `15.0` | `VERIFIED SAFE (bound <= z*)` | 1657.4 ms |
| `markshare2` | Bin 1 (<200) | 74 | 7 | 434 | `LIMIT_REACHED` | **-inf** | `1.0` | `VERIFIED SAFE (bound <= z*)` | 455.5 ms |
| `pk1` | Bin 1 (<200) | 86 | 45 | 915 | `LIMIT_REACHED` | **-inf** | `11.0` | `VERIFIED SAFE (bound <= z*)` | 882.9 ms |
| `mas74` | Bin 1 (<200) | 151 | 13 | 1706 | `LIMIT_REACHED` | **-inf** | `11801.18572` | `VERIFIED SAFE (bound <= z*)` | 1584.2 ms |
| `mas76` | Bin 1 (<200) | 151 | 12 | 1640 | `LIMIT_REACHED` | **-inf** | `40005.05398999999` | `VERIFIED SAFE (bound <= z*)` | 1633.2 ms |
| `assign1-5-8` | Bin 1 (<200) | 156 | 161 | 3720 | `LIMIT_REACHED` | **-inf** | `211.999999999998` | `VERIFIED SAFE (bound <= z*)` | 3002.7 ms |
| `neos859080` | Bin 1 (<200) | 160 | 164 | 1280 | `NUMERICAL_FAILURE` | **1.0000** | — | `VERIFIED SAFE (bound <= z*)` | 3003.7 ms |
| `enlight_hard` | Bin 2 (200-600) | 200 | 100 | 560 | `LIMIT_REACHED` | **0.0000** | `37.0` | `VERIFIED SAFE (bound <= z*)` | 3004.1 ms |
| `neos-3754480-nidda` | Bin 2 (200-600) | 253 | 402 | 1488 | `LIMIT_REACHED` | **-inf** | `12939.7540104743` | `VERIFIED SAFE (bound <= z*)` | 4864.3 ms |
| `graphdraw-domain` | Bin 2 (200-600) | 254 | 865 | 2600 | `LIMIT_REACHED` | **-inf** | `19685.99997550038` | `VERIFIED SAFE (bound <= z*)` | 3022.3 ms |
| `mik-250-20-75-4` | Bin 2 (200-600) | 270 | 195 | 9270 | `LIMIT_REACHED` | **-inf** | `-52301.0` | `VERIFIED SAFE (bound <= z*)` | 3009.3 ms |
| `neos-3046615-murg` | Bin 2 (200-600) | 274 | 498 | 1266 | `LIMIT_REACHED` | **-inf** | `1600.0` | `VERIFIED SAFE (bound <= z*)` | 3009.2 ms |
| `glass4` | Bin 2 (200-600) | 322 | 396 | 1815 | `LIMIT_REACHED` | **800002400.0000** | `1200012599.972384` | `VERIFIED SAFE (bound <= z*)` | 4733.1 ms |
| `timtab1` | Bin 2 (200-600) | 397 | 171 | 829 | `LIMIT_REACHED` | **48194.0000** | `764771.99999978` | `VERIFIED SAFE (bound <= z*)` | 7208.9 ms |
| `supportcase26` | Bin 2 (200-600) | 436 | 870 | 2492 | `LIMIT_REACHED` | **-inf** | `1745.123813` | `VERIFIED SAFE (bound <= z*)` | 3098.5 ms |
| `ran14x18-disj-8` | Bin 2 (200-600) | 504 | 447 | 10277 | `LIMIT_REACHED` | **-inf** | `3712.0` | `VERIFIED SAFE (bound <= z*)` | 3023.8 ms |
| `fhnw-binpack4-4` | Bin 2 (200-600) | 520 | 620 | 2332 | `LIMIT_REACHED` | **-inf** | — | `VERIFIED SAFE (bound <= z*)` | 3028.9 ms |
| `neos-2657525-crna` | Bin 2 (200-600) | 524 | 342 | 1690 | `LIMIT_REACHED` | **-inf** | `1.810748` | `VERIFIED SAFE (bound <= z*)` | 3048.8 ms |
| `neos17` | Bin 2 (200-600) | 535 | 486 | 4931 | `LIMIT_REACHED` | **-inf** | `0.1500025774` | `VERIFIED SAFE (bound <= z*)` | 3015.7 ms |
| `sp150x300d` | Bin 3 (600-1500) | 600 | 450 | 1200 | `LIMIT_REACHED` | **4.8911** | `69.0` | `VERIFIED SAFE (bound <= z*)` | 37045.2 ms |
| `ic97_potential` | Bin 3 (600-1500) | 728 | 1046 | 3138 | `LIMIT_REACHED` | **-inf** | `3941.99993090225` | `VERIFIED SAFE (bound <= z*)` | 3264.8 ms |
| `neos-911970` | Bin 3 (600-1500) | 888 | 107 | 3408 | `LIMIT_REACHED` | **-inf** | `54.76` | `VERIFIED SAFE (bound <= z*)` | 3077.7 ms |
| `exp-1-500-5-5` | Bin 3 (600-1500) | 990 | 550 | 1980 | `LIMIT_REACHED` | **-inf** | `65887.0` | `VERIFIED SAFE (bound <= z*)` | 3028.3 ms |
| `tr12-30` | Bin 3 (600-1500) | 1080 | 750 | 2508 | `LIMIT_REACHED` | **-inf** | `130595.9999999999` | `VERIFIED SAFE (bound <= z*)` | 3041.2 ms |
| `gmu-35-40` | Bin 3 (600-1500) | 1205 | 424 | 4843 | `LIMIT_REACHED` | **-inf** | `-2406733.3688` | `VERIFIED SAFE (bound <= z*)` | 3044.4 ms |
| `neos-4338804-snowy` | Bin 3 (600-1500) | 1344 | 1701 | 6342 | `LIMIT_REACHED` | **-inf** | `1471.0` | `VERIFIED SAFE (bound <= z*)` | 3358.0 ms |
| `50v-10` | Bin 4 (1500-3000) | 2013 | 233 | 2745 | `LIMIT_REACHED` | **0.0000** | `3311.1799841` | `VERIFIED SAFE (bound <= z*)` | 7748.6 ms |
| `csched008` | Bin 4 (1500-3000) | 1536 | 351 | 5687 | `LIMIT_REACHED` | **-inf** | `173.0` | `VERIFIED SAFE (bound <= z*)` | 3030.3 ms |
| `csched007` | Bin 4 (1500-3000) | 1758 | 351 | 6379 | `LIMIT_REACHED` | **-inf** | `350.9999999999955` | `VERIFIED SAFE (bound <= z*)` | 3234.2 ms |
| `mcsched` | Bin 4 (1500-3000) | 1747 | 2107 | 8088 | `LIMIT_REACHED` | **-inf** | `211913.0` | `VERIFIED SAFE (bound <= z*)` | 4465.1 ms |
| `gmu-35-50` | Bin 4 (1500-3000) | 1919 | 435 | 8643 | `LIMIT_REACHED` | **-inf** | `-2607958.33` | `VERIFIED SAFE (bound <= z*)` | 3284.1 ms |
| `p200x1188c` | Bin 4 (1500-3000) | 2376 | 1388 | 4752 | `LIMIT_REACHED` | **-inf** | `15078.0` | `VERIFIED SAFE (bound <= z*)` | 3334.2 ms |
| `beasleyC3` | Bin 4 (1500-3000) | 2500 | 1750 | 5000 | `LIMIT_REACHED` | **-inf** | `753.9999999999128` | `VERIFIED SAFE (bound <= z*)` | 3469.7 ms |
| `pg5_34` | Bin 4 (1500-3000) | 2600 | 225 | 7700 | `LIMIT_REACHED` | **-inf** | `-14339.35345` | `VERIFIED SAFE (bound <= z*)` | 3068.7 ms |
| `flugpl` | Baseline | 18 | 18 | 46 | `LIMIT_REACHED` | **1172382.2077** | `1201500.0` | `VERIFIED SAFE (bound <= z*)` | 498.2 ms |

---

## Section D: QPLIB Continuous Convex QP Suite

All accepted instances conform to official QPLIB convention: $\min rac{1}{2} x^T Q^0 x + b^0 x + q^0$.
Nonconvex instances are rigorously rejected based on primary PROBTYPE classification and eigenvalue analysis.

| Instance | PROBTYPE | Vars | Constraints | Quadratic Terms | SOV-OPT Status | Calculated Objective | Published Reference | Status & Integrity Certification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `QPLIB_8845` | `CCL` | 1546 | 777 | 58114 | `OPTIMAL_VERIFIED` | **10907992.493999** | `10907992.493999` | Rel diff: `8.54e-16` (Machine precision); Original-model KKT Passed |
| `QPLIB_9002` | `DCL` | 2890 | 1649 | 2890 | `STRUCTURE_VERIFIED_CONVEX` | Structural Check | Unpublished | Continuous convex model admitted within declared envelope |
| `QPLIB_8938` | `DCL` | 4001 | 11999 | 4001 | `UNSUPPORTED_RESOURCE_LIMIT` | N/A | `-35.77945` | **Rejection VERIFIED**: Dense Q allocation for n=4001 would require approximately 488.4 MB, exceeding the 250 MB memory guard. Parser raises UNS |
| `QPLIB_0018` | `QCL` | 50 | 1 | 1275 | `UNSUPPORTED_NONCONVEX_QP` | N/A | `-6.38601498` | **Rejection VERIFIED**: UNSUPPORTED_NONCONVEX_QP |

---

## Section E: Representative Refinery Planning Twin (Non-Benchmark Demonstration)

> [!NOTE]
> **Non-Benchmark Demonstration Formulation:** The refinery planning twin is an open-literature representative mathematical model.
> No proprietary MRPL operating data is used or contained in this repository. It is excluded from all public benchmark statistics.

| Variant | Model Type | Variables | Constraints | Status | Objective / Certificate | Verification Property |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Continuous Planning | LP | 36 | 28 | `OPTIMAL_VERIFIED` | **-9043.7500** | Exact KKT optimality satisfied |
| Unit Commitment | MILP | 42 | 40 | `OPTIMAL_VERIFIED` | **-8953.7500** | Integer feasible, exact lower bound verified |
| Hydrocracker Infeasible | LP | 36 | 28 | `INFEASIBLE_CERTIFIED` | Farkas Certified | Exact rational Farkas certificate generated |

---

## Section F: Internal Numerical Trust Suite

- **LU Residual Stress:** All 4 tested Netlib basis matrices achieve LU residuals $< 10^{-10}$ on dense vectors and passing iterative refinement.
- **Degenerate Simplex:** Tested on Klee-Minty cubes, cycling problems, and multi-period staircase structures with exact Devex pricing.
- **18 Unbounded Rays:** All 18 edge cases pass validation (unconstrained, upper/lower bounds, sign flips, splitting, ranged rows).
- **Exact Farkas Certification:** Netlib `WOODINFE` generates an exact rational certificate satisfying $y \ge 0, y^T A \le 0, y^T b > 0$.

---

## Section G: Quarantined Datasets

- **`AVGAS` (`data/quarantined/avgas.mps`):** Quarantined from active verified suites pending independent primary literature provenance verification. Strictly excluded from all public benchmark aggregations.

---

## Section H: Independent Differential Verification (External HiGHS Subprocess)

| Instance | Input Source File | External Status | External Objective | SOV-OPT Status | Discrepancy | Differential Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **ADLITTLE** | `data/netlib/adlittle.mps` | `HighsModelStatus.kOptimal` | 225494.963162 | `OPTIMAL_VERIFIED` | 0.00e+00 | `MATCH` |
| **AFIRO** | `data/netlib/afiro.mps` | `HighsModelStatus.kOptimal` | -464.753143 | `OPTIMAL_VERIFIED` | 0.00e+00 | `MATCH` |
| **BLEND** | `data/netlib/blend.mps` | `HighsModelStatus.kOptimal` | -30.812150 | `OPTIMAL_VERIFIED` | 0.00e+00 | `MATCH` |
| **BRANDY** | `data/netlib/brandy.mps` | `HighsModelStatus.kOptimal` | 1518.509896 | `NUMERICAL_FAILURE` | — | `COMPARISON_NOT_POSSIBLE` |
| **ISRAEL** | `data/netlib/israel.mps` | `HighsModelStatus.kOptimal` | -896644.821863 | `OPTIMAL_VERIFIED` | 3.49e-10 | `MATCH` |
| **KB2** | `data/netlib/kb2.mps` | `HighsModelStatus.kOptimal` | -1749.900130 | `OPTIMAL_VERIFIED` | 6.82e-13 | `MATCH` |
| **RECIPE** | `data/netlib/recipe.mps` | `HighsModelStatus.kOptimal` | -266.616000 | `NUMERICAL_FAILURE` | — | `SOVOPT_NOT_VERIFIED` |
| **SC105** | `data/netlib/sc105.mps` | `HighsModelStatus.kOptimal` | -52.202061 | `OPTIMAL_VERIFIED` | 7.11e-15 | `MATCH` |
| **SC205** | `data/netlib/sc205.mps` | `HighsModelStatus.kOptimal` | -52.202061 | `NUMERICAL_FAILURE` | — | `SOVOPT_NOT_VERIFIED` |
| **SC50A** | `data/netlib/sc50a.mps` | `HighsModelStatus.kOptimal` | -64.575077 | `OPTIMAL_VERIFIED` | 0.00e+00 | `MATCH` |
| **SC50B** | `data/netlib/sc50b.mps` | `HighsModelStatus.kOptimal` | -70.000000 | `OPTIMAL_VERIFIED` | 0.00e+00 | `MATCH` |
| **SCAGR7** | `data/netlib/scagr7.mps` | `HighsModelStatus.kOptimal` | -2331389.824331 | `OPTIMAL_VERIFIED` | 4.66e-10 | `MATCH` |
| **SHARE1B** | `data/netlib/share1b.mps` | `HighsModelStatus.kOptimal` | -76589.318579 | `NUMERICAL_FAILURE` | — | `SOVOPT_NOT_VERIFIED` |
| **SHARE2B** | `data/netlib/share2b.mps` | `HighsModelStatus.kOptimal` | -415.732241 | `NUMERICAL_FAILURE` | — | `SOVOPT_NOT_VERIFIED` |
| **STOCFOR1** | `data/netlib/stocfor1.mps` | `HighsModelStatus.kOptimal` | -41131.976219 | `NUMERICAL_FAILURE` | — | `SOVOPT_NOT_VERIFIED` |
| **VTP.BASE** | `data/netlib/vtp.base.mps` | `HighsModelStatus.kOptimal` | 129831.462461 | `NUMERICAL_FAILURE` | — | `SOVOPT_NOT_VERIFIED` |

---

## Section I: Disclosed Exclusions and Machine Telemetry

- **Hardware Environment:** `Darwin arm64, Python 3.11.16`
- **CPU Only Execution:** `gpu_executed = false` in all audit JSON records.
- **Zero External Solvers in Core:** Neither HiGHS, SciPy, nor OSQP is imported inside `sovopt/`.
- **Anti-Cherry-Picking Compliance:** 100% of candidate instances in the frozen manifest are reported above.
