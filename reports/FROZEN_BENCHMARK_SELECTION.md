# Frozen Benchmark Suite Pre-Selection — SOV-OPT Gate 7

**Date Frozen:** `2026-10-02`  
**Base Solver Commit:** `fc5b537d98a952f01183ae83aea0056e2f9c747f`  
**Target Version:** `0.3.0`  
**Hardware Environment:** `Apple Silicon (M-series, arm64), 10 cores, macOS 26.6.2`  
**Runtime Dependencies:** `Python 3.11.16, NumPy 2.3.5` (stdlib + NumPy only)  

## Anti-Cherry-Picking Protocol

This document records the exact, deterministic selection rules established **BEFORE** running solver benchmarks.
Under the anti-cherry-picking requirements of Gate 7, every admitted instance is frozen with its primary source URL,
cryptographic SHA-256 digest, declared dimensions, and published reference objective.
No instance may be removed or replaced after observing solver outcomes.

---

## Summary of Frozen Benchmark Suites

| Benchmark Category | Official Collection | Version / Solufile | Selected Count | Selection Policy / Dimension Envelope |
| :--- | :--- | :--- | :---: | :--- |
| **Category A: Continuous LP** | Netlib LP | Netlib LP / MINOS 5.3 Library (Gay 1985) | **16** | Bounded dual simplex envelope: $n \le 250, m \le 250$, no RANGES |
| **Category B: Certificate Validation** | Netlib LP/Infeas | Chinneck (1993) | **1** | Primary public Farkas certificate benchmark (`WOODINFE`) |
| **Category C: Discrete MILP** | MIPLIB 2017 | MIPLIB 2017 Benchmark Set v2 (miplib2017-v37.solu) | **38** | Deterministic 4-bin stratification: $n \le 3000, m \le 3000, nnz \le 15000$ |
| **Category D: Continuous Convex QP** | QPLIB | QPLIB 2018 (Furini et al. 2018, updated 2026) | **3** | Continuous convex allow-list (`CCL`, `DCL`), $n \le 5000$, dense RAM $\le 250$ MB |
| **Category D (Negative Test)** | QPLIB | QPLIB 2018 (Furini et al. 2018, updated 2026) | **1** | Explicit nonconvex rejection test (`QPLIB_0018`, PROBTYPE `QCL`) |

---

## Category A & B: Netlib LP Candidates & Selected Suite

| Instance | Problem Class | Vars | Rows | Nonzeros | Published Reference Opt | Expected Status | SHA-256 (MPS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ADLITTLE` | LP | 97 | 56 | 465 | `2.254950e+05` | `OPTIMAL_VERIFIED` | `fec81e24fa91bc54...` |
| `AFIRO` | LP | 32 | 27 | 88 | `-4.647531e+02` | `OPTIMAL_VERIFIED` | `fd3562804ff19382...` |
| `BLEND` | LP | 83 | 74 | 521 | `-3.081215e+01` | `OPTIMAL_VERIFIED` | `c8bb193f8af5dcff...` |
| `BRANDY` | LP | 249 | 220 | 2150 | `1.518510e+03` | `NUMERICAL_FAILURE` | `53b17390ddb1831e...` |
| `ISRAEL` | LP | 142 | 174 | 2358 | `-8.966448e+05` | `OPTIMAL_VERIFIED` | `119a04d815f7db33...` |
| `KB2` | LP | 41 | 43 | 291 | `-1.749900e+03` | `OPTIMAL_VERIFIED` | `b8a3df09b7e76059...` |
| `RECIPE` | LP | 180 | 91 | 752 | `-2.666160e+02` | `NUMERICAL_FAILURE` | `f967ab6466e4e9ad...` |
| `SC105` | LP | 103 | 105 | 281 | `-5.220206e+01` | `OPTIMAL_VERIFIED` | `771da8cb34bf4128...` |
| `SC205` | LP | 203 | 205 | 552 | `-5.220206e+01` | `NUMERICAL_FAILURE` | `3fde67ec21ff86d7...` |
| `SC50A` | LP | 48 | 50 | 131 | `-6.457508e+01` | `OPTIMAL_VERIFIED` | `c4571004af37a0c7...` |
| `SC50B` | LP | 48 | 50 | 119 | `-7.000000e+01` | `OPTIMAL_VERIFIED` | `15c9d96e1d518ddd...` |
| `SCAGR7` | LP | 140 | 129 | 553 | `-2.331389e+06` | `OPTIMAL_VERIFIED` | `30cccee0e5adb619...` |
| `SHARE1B` | LP | 225 | 117 | 1182 | `-7.658932e+04` | `NUMERICAL_FAILURE` | `e31eb15e886236ff...` |
| `SHARE2B` | LP | 79 | 96 | 730 | `-4.157322e+02` | `NUMERICAL_FAILURE` | `b861a8d971195600...` |
| `STOCFOR1` | LP | 111 | 117 | 474 | `-4.113198e+04` | `NUMERICAL_FAILURE` | `a7996944d096c3cd...` |
| `VTP.BASE` | LP | 203 | 198 | 914 | `1.298315e+05` | `NUMERICAL_FAILURE` | `ab568fd861228875...` |
| `WOODINFE` | LP_INFEASIBLE_CERTIFICATE | 89 | 35 | 140 | N/A | `INFEASIBLE_CERTIFIED` | `26cb8633b4d9bb9d...` |

### Documented Netlib Exclusions
The following Netlib instances in the official collection were excluded based on predeclared objective criteria:
- **RANGES Section Excluded:** `BOEING1`, `BOEING2`, `CAPRI`, `DEGEN2`, `DEGEN3`, `ETAMACRO`, etc. (`PARSER_UNSUPPORTED_RANGES`).
- **Dimension Limit Excluded:** `25FV47` (1571 cols), `80BAU3B` (9799 cols), `BNL1` (1175 cols), `CYCLE` (2857 cols), `D2Q06C` (5167 cols), etc. (`RESOURCE_LIMIT: exceeds 250 variables/rows`).

---

## Category C: MIPLIB 2017 Stratified Suite

| Instance | Vars | Rows | Nonzeros | Binaries | General Int | Reference Opt (`miplib2017-v37.solu`) | SHA-256 (MPS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `gen-ip054` | 30 | 27 | 532 | 0 | 30 | `6840.96564179` | `8b71b70a6f92ea9b...` |
| `markshare_4_0` | 34 | 4 | 123 | 30 | 0 | `1.0` | `a05d1c8c1a1e0646...` |
| `gen-ip002` | 41 | 24 | 922 | 0 | 41 | `-4783.733392` | `30ed071e531beea5...` |
| `neos5` | 63 | 63 | 2016 | 53 | 0 | `15.0` | `6004edda3e48c0d2...` |
| `markshare2` | 74 | 7 | 434 | 60 | 0 | `1.0` | `35013a309b073f42...` |
| `pk1` | 86 | 45 | 915 | 55 | 0 | `11.0` | `13851ed426a2dfd7...` |
| `mas74` | 151 | 13 | 1706 | 150 | 0 | `11801.18572` | `181f02fd634306ad...` |
| `mas76` | 151 | 12 | 1640 | 150 | 0 | `40005.05398999999` | `114b73dbe17c1d1b...` |
| `assign1-5-8` | 156 | 161 | 3720 | 130 | 0 | `211.999999999998` | `cb63a8b3480eaca3...` |
| `neos859080` | 160 | 164 | 1280 | 80 | 80 | N/A | `127e8c4b5e67ac66...` |
| `enlight_hard` | 200 | 100 | 560 | 100 | 100 | `37.0` | `572ca23c17d0ad73...` |
| `neos-3754480-nidda` | 253 | 402 | 1488 | 50 | 0 | `12939.7540104743` | `f9b9bf4718a28ac7...` |
| `graphdraw-domain` | 254 | 865 | 2600 | 180 | 20 | `19685.99997550038` | `4e24709cf43956e4...` |
| `mik-250-20-75-4` | 270 | 195 | 9270 | 75 | 175 | `-52301.0` | `b29fe88b56bf3c92...` |
| `neos-3046615-murg` | 274 | 498 | 1266 | 240 | 16 | `1600.0` | `d8bfe7f051fdf60f...` |
| `glass4` | 322 | 396 | 1815 | 302 | 0 | `1200012599.972384` | `5878be05b45cb711...` |
| `timtab1` | 397 | 171 | 829 | 77 | 94 | `764771.99999978` | `bc196d8cba1f846a...` |
| `supportcase26` | 436 | 870 | 2492 | 396 | 0 | `1745.123813` | `1973ccac4667abab...` |
| `ran14x18-disj-8` | 504 | 447 | 10277 | 252 | 0 | `3712.0` | `42c8804fa44742cf...` |
| `fhnw-binpack4-4` | 520 | 620 | 2332 | 481 | 39 | N/A | `1d2dc402bd3e7575...` |
| `neos-2657525-crna` | 524 | 342 | 1690 | 146 | 378 | `1.810748` | `31a5a4880f97d384...` |
| `neos17` | 535 | 486 | 4931 | 300 | 0 | `0.1500025774` | `4ea347bc9061a49b...` |
| `sp150x300d` | 600 | 450 | 1200 | 300 | 0 | `69.0` | `339aa4411ef126df...` |
| `ic97_potential` | 728 | 1046 | 3138 | 450 | 73 | `3941.99993090225` | `4260f75027c7712b...` |
| `neos-911970` | 888 | 107 | 3408 | 840 | 0 | `54.76` | `31e8f835a9499de4...` |
| `exp-1-500-5-5` | 990 | 550 | 1980 | 250 | 0 | `65887.0` | `32bcb5e23d511b3e...` |
| `tr12-30` | 1080 | 750 | 2508 | 360 | 0 | `130595.9999999999` | `2a7983305400189a...` |
| `gmu-35-40` | 1205 | 424 | 4843 | 1200 | 0 | `-2406733.3688` | `c0ae69e1cddf6231...` |
| `neos-4338804-snowy` | 1344 | 1701 | 6342 | 1260 | 42 | `1471.0` | `867380141abb94f4...` |
| `50v-10` | 2013 | 233 | 2745 | 1464 | 183 | `3311.1799841` | `ab32c42d0b916c3b...` |
| `csched008` | 1536 | 351 | 5687 | 1284 | 0 | `173.0` | `cc1366afd23d38b0...` |
| `csched007` | 1758 | 351 | 6379 | 1457 | 0 | `350.9999999999955` | `9c78014447850a49...` |
| `mcsched` | 1747 | 2107 | 8088 | 1745 | 0 | `211913.0` | `39c18a78edecfde1...` |
| `gmu-35-50` | 1919 | 435 | 8643 | 1914 | 0 | `-2607958.33` | `b47c8c89fe140ea3...` |
| `p200x1188c` | 2376 | 1388 | 4752 | 1188 | 0 | `15078.0` | `52e616e7a1e0dc95...` |
| `beasleyC3` | 2500 | 1750 | 5000 | 1250 | 0 | `753.9999999999128` | `728c9616ca793393...` |
| `pg5_34` | 2600 | 225 | 7700 | 100 | 0 | `-14339.35345` | `308af9b3ba0703bd...` |
| `flugpl` | 18 | 18 | 46 | 0 | 11 | `1201500.0` | `a1f0cb79a9563945...` |

---

## Category D: QPLIB Continuous Convex QP Suite

| Instance | PROBTYPE | Vars | Rows | Nonzeros Q | Reference Opt | Classification | Selection Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `QPLIB_8845` | `CCL` | 1546 | 777 | 58114 | `10907992.493999` | `PUBLIC_OFFICIAL_BENCHMARK` | `SUPPORTED CONVEX` |
| `QPLIB_9002` | `DCL` | 2890 | 1649 | 2890 | N/A | `PUBLIC_OFFICIAL_BENCHMARK` | `SUPPORTED CONVEX` |
| `QPLIB_8938` | `DCL` | 4001 | 11999 | 4001 | `-35.779450` | `PUBLIC_OFFICIAL_BENCHMARK` | `SUPPORTED CONVEX` |
| `QPLIB_0018` | `QCL` | 50 | 1 | 1275 | `-6.386015` | `PUBLIC_OFFICIAL_BENCHMARK` | `REJECTED NONCONVEX TEST` |

### Documented QPLIB Exclusions (from official inventory of 134 continuous instances)
- **109 instances with quadratic constraints** (`qcons > 0`, PROBTYPE `*Q`, `*D`, `*C`): Rejected with `UNSUPPORTED_QUADRATIC_CONSTRAINTS`.
- **6 instances with general/nonconvex quadratic objectives** (PROBTYPE `Q*`): Rejected with `UNSUPPORTED_NONCONVEX_QP` (e.g. `QPLIB_0018`, `QPLIB_0343`, `QPLIB_2712`, `QPLIB_2761`).
- **16 instances with $n > 5000$ variables** (e.g. `QPLIB_8559`, `QPLIB_8567`, `QPLIB_8785`, `QPLIB_8616`, `QPLIB_8991`, `QPLIB_8792`, `QPLIB_8515`, `QPLIB_8495`, `QPLIB_8602`, `QPLIB_8790`, `QPLIB_10034`, `QPLIB_10038`, `QPLIB_8500`, `QPLIB_8547`, `QPLIB_9008`): Pre-classified before solving as `UNSUPPORTED_RESOURCE_LIMIT` (dense projection exceeds 250 MB MacBook RAM limit).

---

## Machine & Environment Verification

```json
{
  "hardware": "Apple Silicon (M-series, arm64)",
  "cores": 10,
  "os": "macOS 26.6.2",
  "python": "3.11.16",
  "numpy": "2.3.5",
  "max_dense_qp_vars": 5000,
  "max_dense_qp_memory_mb": 250,
  "max_milp_nodes": 50,
  "milp_timeout_sec": 10.0
}
```
