# Dataset Catalogue & Provenance — SOV-OPT MRPL PS 26119

This catalogue records the complete provenance, mathematical classification, source URLs,
cryptographic hashes, dimensions, reference objectives, and validation status for
all optimization datasets associated with this repository.

No synthetic or team-invented model is used as public benchmark, performance evidence,
accuracy evidence, or industrial-data evidence. Small handcrafted models are used only as
isolated mathematical unit tests.

All models in the active performance suite (`data/verified/`) are genuine benchmark instances
from authoritative sources (Netlib LP, MIPLIB).

---

## Suite Summary: Five Distinct Model Categories

| Category | Count | Instances / Models | Purpose & Classification | Provenance Source |
|:---|:---:|:---|:---|:---|
| **A. Public Performance Benchmark** | 5 | AFIRO, SC50A, SC50B, BLEND, FLUGPL | Active runtime performance & optimality benchmarking | Netlib LP (MINOS 5.3) & MIPLIB 2017 |
| **B. Public Certificate-Validation Dataset** | 1 | WOODINFE | Infeasibility Farkas certificate validation (not runtime speed) | Netlib LP/Infeas (Chinneck 1993, Greenberg 1993) |
| **C. Representative Refinery Formulation** | 1 (4 variants) | MRPL Refinery Planning Twin (`lp`, `milp`, `qp`, `infeasible`) | End-to-end refinery digital twin operational validation | Open literature (Gary & Handwerk; Meyers) |
| **D. Internal Mathematical Unit Fixture** | 18 | `TestUnboundedCertificateHardening` (tests 01–18) | Isolated unit tests for ray & certificate edge cases | Handcrafted mathematical fixtures (`tests/test_solver.py`) |
| **E. Quarantined Dataset** | 1 | AVGAS | Retained for reference; excluded from active evidence | HiGHS test suite (Charnes/Symonds unverified) |

### Disclosed Exclusions & Empty States

| Exclusion / Empty State | Status | Disclosure Rationale |
|:---|:---:|:---|
| **Proprietary MRPL Operations Data** | **Empty State** | Trade secret; confidential refinery telemetry and commercial assays are not public. |
| **Industrial Convex QP Benchmark** | **Empty State** | No authentic public industrial convex QP instance is currently verified in the active suite. |
| **Public Unbounded Certificate Benchmark** | **Not Yet Available** | No suitable provenance-verified public unbounded LP instance was identified in the Netlib and HiGHS collections searched during this audit (search date: 2026-10-01). |

---

## Category A: Active Public Performance Benchmarks (5 instances)

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

## Category B: Public Certificate-Validation Datasets (1 instance)

### 1. WOODINFE — Netlib Infeasible LP Certificate Benchmark

- **Instance Name:** WOODINFE
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Public certificate-validation dataset (infeasible LP)
- **Primary Upstream Collection:** Netlib LP / Infeasible collection (`https://www.netlib.org/lp/infeas/`)
- **Primary Curator:** John W. Chinneck (Carleton University), November 3, 1993
- **Contributor:** Harvey J. Greenberg (University of Colorado at Denver)
- **Literature Attribution:** Network forestry model analyzed in detail in Greenberg, H.J. (1993), "How to Analyze the Results of Linear Programs - Part 3: Infeasibility Diagnosis", *Annals of Mathematics and Artificial Intelligence*.
- **Primary Source URL:** https://www.netlib.org/lp/infeas/
- **Reference Mirror:** HiGHS public test suite repository (`check/instances/woodinfe.mps`, commit `ccbcccdf`, MIT License).
- **Reference Mirror URL:** https://raw.githubusercontent.com/ERGO-Code/HiGHS/master/check/instances/woodinfe.mps
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `26cb8633b4d9bb9dcbd60b04534ef7b9b0709a67b0ba62c0a95481a8ea71181f`
- **Location:** `data/certificate_validation/woodinfe.mps`
- **Format:** Fixed-column standard MPS.
- **Licence / Redistribution:** Open research collection (Netlib).
- **Dimensions:** 89 decision variables, 35 constraint rows (36 including cost row `COST`), 209 matrix nonzeros, 0 integer variables.
- **Objective Sense:** MINIMIZE (cost row `COST`).
- **Expected Status:** `INFEASIBLE_CERTIFIED`
- **Certificate Type:** Exact binary-rational Farkas certificate ($y \ge 0, y^T A \le 0, y^T b > 0$).
- **SOV-OPT Measured Result:**
  - Status: `INFEASIBLE_CERTIFIED`
  - Certificate: Exact binary-rational Farkas certificate verified (`verification.farkas_verified = True`)
  - Algorithm: Two-phase revised simplex (Phase I artificial sum > 0)
- **Role & Separation:** Evaluated strictly for mathematical Farkas certificate correctness. Excluded from runtime performance benchmarking and performance leaderboards.

---

## Category C: Representative Refinery Formulations (1 model, 4 operational variants)

### MRPL Refinery Planning Digital Twin

- **Model Name:** MRPL Refinery Planning Digital Twin (`sovopt.refinery_twin`)
- **Problem Class:** Parameterised multi-period refinery planning formulation
- **Category:** Representative engineering digital twin
- **Domain:** Downstream petroleum refining (Mangalore Refinery and Petrochemicals Limited topology)
- **Literature Reference:** Formulated from open petroleum refining literature (Gary & Handwerk 2001; Meyers 2004) covering CDU/VDU crude distillation, FCC secondary conversion, CCR catalytic reforming, intermediate tankage inventories, and BS-VI gasoline / Euro-VI diesel product blending specs.
- **Implementation:** `sovopt/refinery_twin.py`, demonstrated via `scripts/demonstrate_refinery_twin.py`
- **Operational Variants:**
  1. **`lp` (Continuous Economic Plan):** 28 variables, 28 constraints, continuous optimal profit dispatch.
  2. **`milp` (Discrete Operational Plan):** 32 variables, 32 constraints, 4 binary unit commitment indicators ($z \in \{0, 1\}$) with minimum turndown throughput limits.
  3. **`qp` (Smooth Operational Dispatch):** 28 variables, 28 constraints, positive semi-definite quadratic throughput-flutter penalty ($\frac{1}{2} \Delta u^T Q \Delta u$).
  4. **`infeasible` (Diagnostic Scenario):** Impossible production commitments verifying exact Farkas certificate generation ($y \ge 0, y^T A \le 0, y^T b > 0$).
- **Disclosure:** Formulation is an original parameterised engineering model based on public domain literature. It does not contain confidential MRPL production data, actual commercial contracts, or proprietary crude assays.

---

## Category D: Internal Mathematical Unit Fixtures (18 fixtures)

### TestUnboundedCertificateHardening Edge-Case Suite

- **Location:** `tests/test_solver.py` under `TestUnboundedCertificateHardening` (tests 01–18)
- **Problem Class:** Continuous LP edge cases (unbounded rays, recession directions, affine shifts)
- **Category:** Internal mathematical unit fixtures
- **Label:** `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA`
- **Coverage:**
  1. Unconstrained minimization unbounded ray
  2. Constrained minimization unbounded ray
  3. Constrained maximization unbounded ray
  4. Lower-bounded variable recession direction
  5. Upper-bounded variable recession direction
  6. Free variable unbounded ray
  7. Shifted-variable transformation recession direction
  8. Sign-flipped upper bound transformation
  9. Free-variable split transformation
  10. Equality-constrained recession direction
  11. Ranged-row recession direction
  12. Finite lower+upper box non-unbounded preservation
  13. Invalid objective direction rejection ($c^T d \ge 0$)
  14. Invalid row recession rejection
  15. Invalid bound direction rejection
  16. Infeasible base-point rejection ($x_0$ not feasible)
  17. Transformed direction postsolve ($d_x = D d_t$, shifts $s$ not added)
  18. Non-finite / dimension mismatch certificate rejection
- **Separation:** Strictly isolated unit test fixtures used to test `verify_unbounded_certificate()` and ray reconstruction. Excluded from public dataset counts, performance reports, and benchmark tables.

---

## Category E: Quarantined Datasets (1 instance)

### AVGAS — Aviation Gasoline Blending LP (Quarantined)

- **Location:** `data/quarantined/avgas.mps`, `data/quarantined/avgas.json`
- **Source:** HiGHS public test suite repository (`check/instances/avgas.mps`)
- **MPS SHA-256:** `10d0e68381321ee9b6a22a53a33d07f7740070b0a077a78ef742a9e88eca8213`
- **Claimed Attribution:** Charnes, Cooper, and Mellon (1952) / Symonds (1955)
- **Reason for Quarantine:** While the file source and SHA-256 are verified, the correspondence of the 8-variable matrix to primary literature text has not been independently confirmed in this project. Quarantined outside active runtime paths; not included in the active verified benchmark suite.

---

## Disclosed Exclusions & Empty States

### 1. Proprietary MRPL Refinery Production Data (Empty State)
- Confidential operational LP models (crude assays, distillation cuts, unit yield vectors) are trade secrets not in the public domain.
- Fictional refinery numbers are prohibited. Netlib refinery benchmark `BLEND` is provided instead.
- Formal disclosure: *"No authorized MRPL dataset is available in this project."*

### 2. Industrial Convex QP Data (Empty State)
- No authentic public industrial convex QP dataset is currently admitted. Toy models have been removed.
- The sovereign QP interior-point solver (`sovopt/qp.py`) is verified mathematically using KKT residual verification. Industrial QP benchmarks will be admitted when authentic public datasets are verified.

### 3. Public Unbounded Certificate Benchmark (Not Yet Available)
- **PUBLIC UNBOUNDED CERTIFICATE BENCHMARK: NOT YET AVAILABLE**
- No suitable provenance-verified public unbounded LP instance was identified in the Netlib and HiGHS collections searched during this audit (search date: 2026-10-01).
- Handcrafted test instances in `tests/test_solver.py` are strictly labeled:
  `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA`
  They are explicitly excluded from public dataset counts, performance reports, and benchmark tables.
