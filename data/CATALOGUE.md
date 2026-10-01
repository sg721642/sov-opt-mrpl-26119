# Dataset Catalogue & Provenance — SOV-OPT MRPL PS 26119

This catalogue records the complete provenance, mathematical classification, source URLs,
cryptographic hashes, dimensions, reference objectives, and validation status for
all optimization datasets associated with this repository.

All models in the active verified suite (`data/verified/`) are genuine benchmark instances
from authoritative sources (Netlib LP, MIPLIB). No synthetic models or fictional refinery
parameters are presented as measured evidence.

---

## Suite Summary

| Dataset | Problem Class | Provenance Category | Status | Reference Objective / Bound |
|:---|:---:|:---:|:---:|:---|
| **AFIRO** | LP | Netlib application benchmark (Stanford SOL) | **Active Verified** | -464.75314286 (MINOS 5.3) |
| **SC50A** | LP | Netlib staircase production model | **Active Verified** | -64.575077059 (MINOS 5.3) |
| **SC50B** | LP | Netlib staircase production model | **Active Verified** | -70.000000000 (MINOS 5.3) |
| **BLEND** | LP | Netlib petroleum refinery blending model (Murtagh) | **Active Verified** | -30.812149846 (MINOS 5.3) |
| **FLUGPL** | MILP | MIPLIB airline fleet allocation model (Wagner et al.) | **Active Verified** | 1201500.0 (integer optimum) |
| **AVGAS** | LP | HiGHS test suite instance (Symonds / Charnes attribution) | **Quarantined** | -7.75 (literature claim; unverified) |
| **MRPL Data** | LP/MILP | Proprietary refinery operations data | **Empty State** | None (trade secret; not public) |
| **Industrial QP** | QP | Industrial convex quadratic program | **Empty State** | None (no authentic public dataset verified) |

---

## Active Verified Datasets

### 1. AFIRO — Systems Optimization Laboratory Resource Allocation LP

- **Instance Name:** AFIRO
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Small industrial production and resource allocation linear program from the Systems Optimization Laboratory (SOL) at Stanford University, contributed by Michael Saunders.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/afiro
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `fd3562804ff19382a9cd8bcb22ec81bffd24a4143a2290783831d8c64516a24b`
- **SHA-256 (Normalized JSON):** `a25c15dc594247565406b47ff0fe368943d67b09bf94f9b8c04ec47915570be0`
- **Format:** Fixed-column standard MPS (`data/verified/afiro.mps`) and canonical JSON (`examples/afiro.json`).
- **Licence / Redistribution:** Public open benchmark collection (Netlib, free for research and education).
- **Dimensions:** 32 decision variables, 27 constraint rows, 83 constraint matrix nonzeros (88 total MPS nonzeros including 5 cost coefficients).
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `X05`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-4.6475314286E+02` (Netlib README, 11 significant digits from MINOS 5.3 report).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-464.753142857143` (exact IEEE 754: `-464.75314285714285`)
  - Discrepancy vs Netlib reference: `~2.857e-9` (due to 11-digit precision of published MINOS 5.3 reference `-464.75314286` vs full-precision solution; agreement with independent HiGHS solve is `0.0`)
  - Primal residual: `1.42e-14`
  - Dual residual: `1.72e-17`
  - KKT passed: `true`
  - Backends: `cpu` (primal revised simplex) and `pdhg-cpu` (first-order PDHG)

---

### 2. SC50A — Staircase Structure Dynamic Production LP

- **Instance Name:** SC50A
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Multi-period dynamic production planning model with staircase constraint structure from the Netlib collection.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/sc50a
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `c4571004af37a0c7d49099f8fcc513885401784d32f712bf44e014e40348c521`
- **SHA-256 (Normalized JSON):** `761fa6d0f9485bbd1f95c10fa83c34537651a56644fcfc01e5d71c4c8108a737`
- **Format:** Fixed-column standard MPS (`data/verified/sc50a.mps`) and canonical JSON (`examples/sc50a.json`).
- **Licence / Redistribution:** Public open benchmark collection (Netlib).
- **Dimensions:** 48 decision variables, 50 constraint rows, 130 constraint matrix nonzeros (131 total MPS nonzeros).
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-6.4575077059E+01` (Netlib README, MINOS 5.3 report).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-64.5750770585645`
  - Discrepancy vs Netlib reference: `~4.355e-10` (due to 11-digit precision of published MINOS 5.3 reference `-64.575077059` vs full-precision solution; agreement with independent HiGHS solve is `0.0`)
  - Primal residual: `5.37e-16`
  - Dual residual: `4.09e-17`
  - KKT passed: `true`

---

### 3. SC50B — Staircase Structure Dynamic Production LP

- **Instance Name:** SC50B
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Staircase economic/production planning model from Netlib.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/sc50b
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `15c9d96e1d518dddc197e8e107febce590d0ae94594c676ff0d135b5642c1be5`
- **SHA-256 (Normalized JSON):** `2db1680d908ff95f4007d4c2b92e7d7a18bb722a843e9c5aa1c29665bc7f035d`
- **Format:** Fixed-column standard MPS (`data/verified/sc50b.mps`) and canonical JSON (`examples/sc50b.json`).
- **Licence / Redistribution:** Public open benchmark collection (Netlib).
- **Dimensions:** 48 decision variables, 50 constraint rows, 118 constraint matrix nonzeros (119 total MPS nonzeros).
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-7.0000000000E+01` (Netlib README, MINOS 5.3 report).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-70.000000000000`
  - Discrepancy vs Netlib reference: `0.0`
  - Primal residual: `0.0`
  - Dual residual: `0.0`
  - KKT passed: `true`

---

### 4. BLEND — Petroleum Refinery Blending LP

- **Instance Name:** BLEND
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Classic petroleum refinery blending problem formulation contributed to Netlib by Bruce Murtagh.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/blend
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `c8bb193f8af5dcff735a3b8db62077db93625e93cfb26e2b01f83ca3039cbf7d`
- **SHA-256 (Normalized JSON):** `67b2d2f70b4be934c9794cb5c8ce2b62d3a77197b0a94488db9a1029c0d35eef`
- **Format:** Fixed-column standard MPS (`data/verified/blend.mps`) and canonical JSON (`examples/blend.json`).
- **Licence / Redistribution:** Public open benchmark collection (Netlib).
- **Dimensions:** 83 decision variables, 74 constraint rows, 491 constraint matrix nonzeros (521 total MPS nonzeros).
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `R0000000`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-3.0812149846E+01` (Netlib README, MINOS 5.3 report).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-30.812149845828237`
  - Primal residual: `1.78e-15`
  - Dual residual: `1.23e-16`
  - KKT passed: `true`
  - Comparison Note: SOV-OPT and HiGHS both compute `-30.812149845828237`, confirming agreement between independent implementations on this file. The Netlib README reference has 11 significant digits (`-3.0812149846E+01`), differing by `~1.72e-10`.

---

### 5. FLUGPL — Airline Fleet Assignment & Route Allocation MILP

- **Instance Name:** FLUGPL
- **Problem Class:** Mixed-Integer Linear Program (MILP)
- **Category:** Documented application benchmark
- **Application / Domain:** Commercial airline flight schedule and aircraft fleet allocation problem formulated by Harvey Wagner, Gregory, and Boyd. Sourced from MIPLIB 1.0 / 2017.
- **Original Source URL:** https://miplib.zib.de/instance_details_flugpl.html
- **Direct File URL:** https://miplib.zib.de/WebData/instances/flugpl.mps.gz
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `a1f0cb79a95639450dd984473a00efca24365457153d7fcb859c6581ddab4c2c`
- **SHA-256 (Normalized JSON):** `481232822a16d56d7df15a9ae639d67761005ca7732a3bf2a3d0ec42217f5647`
- **Format:** Fixed/free standard MPS (`data/verified/flugpl.mps`) and canonical JSON (`examples/flugpl.json`).
- **Licence / Redistribution:** Public open benchmark under ZIB MIPLIB license.
- **Dimensions:** 18 decision variables, 18 constraint rows, 46 matrix nonzeros.
- **Integer Variables:** 11 general integer variables.
- **Objective Sense:** MINIMIZE (cost row `KOSTEN`).
- **Published Reference Objective:** `1201500` (optimal integer solution); LP relaxation root bound = 769500.0.
- **SOV-OPT Measured Result:**
  - Status: `LIMIT_REACHED` (at 50-node limit)
  - Conservative Rational Lower Bound: `1173644.9999999998` (floating-point display of exact rational bound computed from exact rational basis duals)
  - Incumbent: None found within 50 nodes
  - Pruning: Infeasible branch relaxations verified via exact binary-rational Farkas certificates

---

## Quarantined Datasets

### AVGAS — Aviation Gasoline Blending LP (Quarantined)

- **Location:** `data/quarantined/avgas.mps`, `data/quarantined/avgas.json`
- **Source:** HiGHS public test suite repository (`check/instances/avgas.mps`)
- **MPS SHA-256:** `10d0e68381321ee9b6a22a53a33d07f7740070b0a077a78ef742a9e88eca8213`
- **Claimed Attribution:** Charnes, Cooper, and Mellon (1952) / Symonds (1955)
- **Reason for Quarantine:** While the file source and SHA-256 are verified, the correspondence of the 8-variable matrix to primary literature text has not been independently confirmed in this project. Quarantined outside active runtime paths; not included in the verified benchmark suite.

---

## Disclosed Exclusions & Empty States

### 1. Proprietary MRPL Refinery Production Data (Empty State)
- Confidential operational LP models (crude assays, distillation cuts, unit yield vectors) are trade secrets not in the public domain.
- Fictional refinery numbers are prohibited. Netlib refinery benchmark `BLEND` is provided instead.
- Formal disclosure: *"No authorized MRPL dataset is available in this project."*

### 2. Industrial Convex QP Data (Empty State)
- No authentic public industrial convex QP dataset is currently admitted. Toy models have been removed.
- The sovereign QP interior-point solver (`sovopt/qp.py`) is verified mathematically using KKT residual verification. Industrial QP benchmarks will be admitted when authentic public datasets are verified.
