# Verified Dataset Catalogue — SOV-OPT MRPL PS 26119

This catalogue records the complete provenance, mathematical classification, source URLs,
cryptographic hashes, dimensions, reference objectives, and measured validation status for
every optimization dataset in this repository.

All models in `data/verified/` are genuine public benchmark problems from authoritative
sources (Netlib LP, MIPLIB, published operations research literature). No synthetic models,
fabricated refinery parameters, or invented benchmarks are included in the active suite.

---

## Suite Summary & Empty State Disclosures

| Domain / Problem Class | Status | Verified Instances | Notes |
|:---|:---|:---|:---|
| **Academic Solver Benchmark LP** | Verified | AVGAS | Symonds (1955) aviation gasoline blending LP formulation |
| **Documented Application Benchmark LP** | Verified | AFIRO, SC50A, SC50B, BLEND | Authoritative Netlib benchmark instances |
| **Documented Application Benchmark MILP** | Verified | FLUGPL | MIPLIB airline fleet allocation problem |
| **Proprietary MRPL Refinery Production LP** | **Empty State** | *None* | No authorized MRPL dataset is available in this project. Fictional refinery parameters are prohibited. |
| **Industrial Convex Quadratic Program (QP)** | **Empty State** | *None* | No verified real-world industrial QP benchmark is currently active. Synthetic toy QP instances (e.g. `qp_example.qps` from QPSReader test suite) are excluded. |

---

## Active Verified Datasets

### 1. AVGAS — Aviation Gasoline Refinery Blending LP

- **Instance Name:** AVGAS
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Academic solver benchmark
- **Application / Domain:** Historical petroleum refinery aviation gasoline blending formulation. Blending alkylate, catalytic cracked gasoline, straight run gasoline, and isopentane into aviation gasoline subject to octane number and vapor pressure specifications.
- **Provenance Evidence:** Published academic formulation from Charnes, Cooper, and Mellon (1952), "Blending Aviation Gasolines — A Study in Programming Interdependent Activities", *Econometrica* 20(2): 135–159; and Symonds (1955), *Linear Programming in the Petroleum Industry*, F. J. Maingot.
- **Original Source URL:** https://github.com/ERGO-Code/HiGHS/blob/master/check/instances/avgas.mps
- **Direct File URL:** https://raw.githubusercontent.com/ERGO-Code/HiGHS/master/check/instances/avgas.mps
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `10d0e68381321ee9b6a22a53a33d07f7740070b0a077a78ef742a9e88eca8213`
- **SHA-256 (Normalized JSON):** `cc2c254d20c2e24053db2ab74d56ba847f099159c749d0013fb1f0843a939c52`
- **Format:** Fixed/free MPS format (`data/verified/avgas.mps`) and canonical JSON (`examples/avgas.json`).
- **Licence / Redistribution:** Public open benchmark under MIT / Apache 2.0.
- **Dimensions:** 8 decision variables, 10 constraint rows, 30 constraint matrix nonzeros (38 total MPS nonzeros including 8 cost coefficients).
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `COST`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-7.75` (exact mathematical optimum).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-7.750000`
  - Iterations: 9 (primal revised simplex)
  - Primal residual: `6.06e-17`
  - Dual residual: `0.0`
  - KKT passed: `true`
  - Backend: `cpu` (simplex) and `pdhg-cpu` (first-order PDHG)

---

### 2. AFIRO — Systems Optimization Laboratory Resource Allocation LP

- **Instance Name:** AFIRO
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Econometric / industrial resource allocation model.
- **Provenance Evidence:** Netlib LP library. Provided to Netlib by Michael Saunders, Systems Optimization Laboratory (SOL), Stanford University.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/afiro (decompressed via standard Netlib `emps` decoder)
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `fd3562804ff19382a9cd8bcb22ec81bffd24a4143a2290783831d8c64516a24b`
- **SHA-256 (Normalized JSON):** `39229289a664e30ec1223365837406a91ba3469b2dcb9f71ceec7785ca1946cd`
- **Licence / Redistribution:** Netlib open access research distribution.
- **Dimensions:** 32 decision variables, 27 constraint rows (10 equality, 17 inequality), 83 constraint matrix nonzeros (88 total Netlib nonzeros including 5 cost coefficients).
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `COST`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-4.6475314286E+02` (MINOS 5.3, Netlib README).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-464.75314285714285` (exact match to reference)
  - Iterations: 55 (two-phase primal revised simplex)
  - Primal residual: `1.42e-14`
  - Dual residual: `1.72e-17`
  - Complementarity: `1.48e-17`
  - Relative duality gap: `3.13e-17`
  - KKT passed: `true`

---

### 3. SC50A — Staircase Dynamic Production LP

- **Instance Name:** SC50A
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Dynamic multi-period economic planning model with staircase constraint structure.
- **Provenance Evidence:** Netlib LP benchmark library.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/sc50a (decompressed via Netlib `emps`)
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `c4571004af37a0c7d49099f8fcc513885401784d32f712bf44e014e40348c521`
- **SHA-256 (Normalized JSON):** `b551aaa7900b50635f4766918ae159be3137da283169f55b1821d23f045e937b`
- **Licence / Redistribution:** Netlib open access.
- **Dimensions:** 48 decision variables, 50 constraint rows, 130 constraint matrix nonzeros (131 total Netlib nonzeros including 1 cost coefficient).
- **Integer Variables:** 0.
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-6.4575077059E+01` (MINOS 5.3, Netlib README).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-64.5750770585645`
  - Iterations: 56
  - Primal residual: `5.37e-16`
  - Dual residual: `4.09e-17`
  - Complementarity: `6.74e-17`
  - Relative duality gap: `1.07e-16`
  - KKT passed: `true`

---

### 4. SC50B — Staircase Dynamic Production LP

- **Instance Name:** SC50B
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Dynamic multi-period economic planning model with staircase constraint structure.
- **Provenance Evidence:** Netlib LP benchmark library.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/sc50b (decompressed via Netlib `emps`)
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `15c9d96e1d518dddc197e8e107febce590d0ae94594c676ff0d135b5642c1be5`
- **SHA-256 (Normalized JSON):** `ab3adb824a044ef339828c3374a096c769dd4b0375978ba94b05cb33702c5fa6`
- **Licence / Redistribution:** Netlib open access.
- **Dimensions:** 48 decision variables, 50 constraint rows, 118 constraint matrix nonzeros (119 total Netlib nonzeros including 1 cost coefficient).
- **Integer Variables:** 0.
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-7.0000000000E+01` (MINOS 5.3, Netlib README).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-70.000000`
  - Iterations: 50
  - Primal residual: `2.49e-16`
  - Dual residual: `3.97e-17`
  - Complementarity: `9.01e-17`
  - Relative duality gap: `1.47e-16`
  - KKT passed: `true`

---

### 5. BLEND — Petroleum Refinery Blending LP

- **Instance Name:** BLEND
- **Problem Class:** Continuous Linear Program (LP)
- **Category:** Documented application benchmark
- **Application / Domain:** Refinery blending optimization problem.
- **Provenance Evidence:** Netlib LP benchmark library. Contributed by Bruce A. Murtagh.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/blend
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `c8bb193f8af5dcff735a3b8db62077db93625e93cfb26e2b01f83ca3039cbf7d`
- **SHA-256 (Normalized JSON):** `d08bca8f2afded6f44620935c23d429d3d1d405d313e7d37beb4556a31d7a2c1`
- **Licence / Redistribution:** Netlib open access.
- **Dimensions:** 83 decision variables, 74 constraint rows (43 equality rows, 31 inequality rows), 491 constraint matrix nonzeros (521 total Netlib nonzeros including 30 cost coefficients).
- **Integer Variables:** 0.
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-3.0812149846E+01` (MINOS 5.3, Netlib README, 11 significant digits).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-30.812149845828237` (differs from 11-digit published reference `-30.812149846` by approximately 1.72e-10)
  - Iterations: 555 (two-phase primal revised simplex)
  - Primal residual: `1.78e-15`
  - Dual residual: `1.23e-16`
  - Complementarity: `2.84e-16`
  - Relative duality gap: `1.97e-16`
  - KKT passed: `true`
  - Architectural Note: Solved by direct standard-form equality row handling (avoiding opposing degenerate slack pairs that cycle) and unscaled fallback for ill-conditioned equilibration.

---

### 6. FLUGPL — Airline Fleet Allocation MILP

- **Instance Name:** FLUGPL
- **Problem Class:** Mixed-Integer Linear Program (MILP)
- **Category:** Documented application benchmark
- **Application / Domain:** Airline aircraft assignment and route allocation.
- **Provenance Evidence:** MIPLIB 1.0, MIPLIB 2017 benchmark library. Formulated by Harvey M. Wagner (author of *Principles of Operations Research*), John W. Gregory (Cray Research), E. Andrew Boyd (Rice University).
- **Original Source URL:** https://miplib.zib.de/instance_details_flugpl.html
- **Direct File URL:** https://miplib.zib.de/WebData/instances/flugpl.mps.gz
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `a1f0cb79a95639450dd984473a00efca24365457153d7fcb859c6581ddab4c2c`
- **SHA-256 (Normalized JSON):** `d154782edbb89f569e52e8a24db02c2995d99c17a47993fe9ff60a8fe2c5e1ae`
- **Licence / Redistribution:** MIPLIB open academic benchmark collection.
- **Dimensions:** 18 decision variables, 18 constraint rows, 46 nonzeros.
- **Integer Variables:** 11 general integer variables (not binary).
- **Objective Sense:** MINIMIZE (cost row `KOSTEN`).
- **Published Reference Objective:** `1201500` (optimal integer solution); LP relaxation root bound = 769500.0 (with published variable bounds).
- **SOV-OPT Measured Result:**
  - Status: `LIMIT_REACHED` (at configured node limit, e.g. 50 nodes)
  - Conservative Rational Lower Bound: `1173645.0` (exact rational basis duals advance bound from LP relaxation root 769500.0)
  - Open Nodes: Explored cleanly without numerical divergence.
  - Architectural Note: Infeasible branch relaxations are rigorously verified with exact binary-rational Farkas certificates ($G^T z = 0, h^T z < 0, z \ge 0$), permitting safe branch-and-bound pruning.

---

## Disclosed Exclusions & Empty State Rationale

### 1. Proprietary MRPL Refinery Production Data (Empty State)

MRPL (Mangalore Refinery and Petrochemicals Limited) production linear programming models:
- Operational crude assay data, blend fraction limits, tray yields, and economic transfer prices are proprietary internal refinery trade secrets.
- No authorized MRPL dataset is available in this project.
- Synthetically invented refinery parameters (e.g. made-up distillation yields or fabricated business constraints) are strictly prohibited by SOV-OPT repository integrity guidelines.
- Instead, the repository provides the documented historical petroleum industry LP benchmark `AVGAS` (Symonds 1955 / Charnes et al. 1952) and the Netlib refinery benchmark `BLEND` (Murtagh).

### 2. Industrial Convex Quadratic Programming Data (Empty State)

- A previous version included `qp_example.qps` from the `QPSReader.jl` unit test repository (a 2-variable toy example with quadratic objective).
- In accordance with instructions to exclude synthetic or toy test instances from real-world verification claims, `qp_example.qps` has been removed from the active suite.
- The quadratic programming engine (`sovopt/qp.py`) implements a Mehrotra predictor-corrector interior point method with floating-point numerical positive-semidefiniteness inspection (not an exact rational PSD certificate) and unconstrained separable box support. Real-world industrial QP benchmarks will be admitted once authentic public datasets meeting all provenance criteria are verified.
