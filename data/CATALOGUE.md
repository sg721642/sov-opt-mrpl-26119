# Verified Dataset Catalogue — SOV-OPT MRPL PS 26119

This catalogue records the complete provenance, mathematical classification, source URLs,
cryptographic hashes, and validation status for every optimization dataset in this repository.

All models in `data/verified/` are genuine public benchmark problems from authoritative
sources (Netlib LP, MIPLIB, published operations research literature). No synthetic models,
fabricated refinery parameters, or invented benchmarks are included in the active suite.

---

## Active Verified Datasets

### 1. AVGAS — Aviation Gasoline Refinery Blending LP

- **Instance Name:** AVGAS
- **Problem Class:** Continuous Linear Program (LP)
- **Application / Domain:** Petroleum refinery aviation gasoline blending. Blending alkylate, catalytic cracked gasoline, straight run gasoline, and isopentane into 100/130 aviation gasoline subject to octane number and vapor pressure specifications.
- **Provenance Evidence:** Genuine published industrial case study from Charnes, Cooper, and Mellon (1952), "Blending Aviation Gasolines — A Study in Programming Interdependent Activities", *Econometrica* 20(2): 135–159; and Symonds (1955), *Linear Programming in the Petroleum Industry*, F. J. Maingot.
- **Original Source URL:** https://github.com/ERGO-Code/HiGHS/blob/master/check/instances/avgas.mps
- **Direct File URL:** https://raw.githubusercontent.com/ERGO-Code/HiGHS/master/check/instances/avgas.mps
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (MPS):** `10d0e68381321ee9b6a22a53a33d07f7740070b0a077a78ef742a9e88eca8213`
- **SHA-256 (Normalized JSON):** `cc2c254d20c2e24053db2ab74d56ba847f099159c749d0013fb1f0843a939c52`
- **Format:** Fixed/free MPS format (`data/verified/avgas.mps`) and canonical JSON (`data/verified/avgas.json`).
- **Licence / Redistribution:** Public open benchmark under MIT / Apache 2.0.
- **Dimensions:** 8 decision variables, 10 constraint rows, 38 nonzeros.
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
- **Application / Domain:** Small econometric / industrial resource allocation model.
- **Provenance Evidence:** Netlib LP library. Provided to Netlib by Michael Saunders, Systems Optimization Laboratory (SOL), Stanford University.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/afiro (decompressed via standard Netlib `emps` decoder)
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (Raw Netlib compressed):** `964d9df9579e2d16a025693b64057910ba99f1ec6bafe40ef0098319e40b28ba`
- **SHA-256 (Decompressed MPS):** `fd3562804ff19382a9cd8bcb22ec81bffd24a4143a2290783831d8c64516a24b`
- **SHA-256 (Normalized JSON):** `39229289a664e30ec1223365837406a91ba3469b2dcb9f71ceec7785ca1946cd`
- **Licence / Redistribution:** Netlib open access research distribution.
- **Dimensions:** 32 decision variables, 27 constraint rows (10 equality, 17 inequality), 88 nonzeros.
- **Integer Variables:** 0 (pure continuous LP).
- **Objective Sense:** MINIMIZE (cost row `COST`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-4.6475314286E+02` (MINOS 5.3 on VAX, Netlib README).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-464.75314285714285` (exact match to reference)
  - Iterations: 20 (primal revised simplex)
  - Primal residual: `5.68e-14`
  - Dual residual: `1.92e-17`
  - Complementarity: `4.47e-17`
  - KKT passed: `true`

---

### 3. SC50A — Staircase Dynamic Production LP

- **Instance Name:** SC50A
- **Problem Class:** Continuous Linear Program (LP)
- **Application / Domain:** Dynamic multi-period economic planning with staircase constraint structure.
- **Provenance Evidence:** Netlib LP benchmark library (originally formulated as maximization; cost negated by Netlib for standard minimization).
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/sc50a (decompressed via Netlib `emps`)
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (Raw Netlib compressed):** `f6eb22f39b9978bba1ed5de3bba0b63ce70a058ef5e77a6dc7f06901edfd9ef8`
- **SHA-256 (Decompressed MPS):** `c4571004af37a0c7d49099f8fcc513885401784d32f712bf44e014e40348c521`
- **SHA-256 (Normalized JSON):** `b551aaa7900b50635f4766918ae159be3137da283169f55b1821d23f045e937b`
- **Licence / Redistribution:** Netlib open access.
- **Dimensions:** 48 decision variables, 50 constraint rows, 131 nonzeros.
- **Integer Variables:** 0.
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-6.4575077059E+01` (MINOS 5.3, Netlib README).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-64.5750770585645`
  - Iterations: 56
  - Primal residual: `1.23e-16`
  - Dual residual: `2.61e-16`
  - KKT passed: `true`

---

### 4. SC50B — Staircase Dynamic Production LP

- **Instance Name:** SC50B
- **Problem Class:** Continuous Linear Program (LP)
- **Application / Domain:** Staircase economic planning structure.
- **Provenance Evidence:** Netlib LP benchmark library.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/sc50b (decompressed via Netlib `emps`)
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (Raw Netlib compressed):** `830f16f59525f09fadde86144ed9a317bb19129c4c4c9fe05620807ac89f3968`
- **SHA-256 (Decompressed MPS):** `15c9d96e1d518dddc197e8e107febce590d0ae94594c676ff0d135b5642c1be5`
- **SHA-256 (Normalized JSON):** `ab3adb824a044ef339828c3374a096c769dd4b0375978ba94b05cb33702c5fa6`
- **Licence / Redistribution:** Netlib open access.
- **Dimensions:** 48 decision variables, 50 constraint rows, 119 nonzeros.
- **Integer Variables:** 0.
- **Objective Sense:** MINIMIZE (cost row `R00`).
- **Objective Offset:** 0.0.
- **Published Reference Objective:** `-7.0000000000E+01` (MINOS 5.3, Netlib README).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `-70.000000`
  - Iterations: 54
  - Primal residual: `2.49e-16`
  - Dual residual: `2.61e-16`
  - KKT passed: `true`

---

### 5. QP_EXAMPLE — Convex Quadratic Program with QUADOBJ

- **Instance Name:** QPexample
- **Problem Class:** Strictly Convex Quadratic Program (QP)
- **Application / Domain:** Quadratic cost optimization subject to linear demand constraints.
- **Provenance Evidence:** Standard QPS reference benchmark from QPSReader test suite (JuliaSmoothOptimizers).
- **Original Source URL:** https://github.com/JuliaSmoothOptimizers/QPSReader.jl/tree/master/test/dat
- **Direct File URL:** https://raw.githubusercontent.com/JuliaSmoothOptimizers/QPSReader.jl/master/test/dat/qp-example.qps
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (QPS):** `0d154c80a55fe79b724f78aa4c2e6f7126344fb483d60e896a66800740a463bd`
- **SHA-256 (Normalized JSON):** `eef40bc29801c26fac4b53bd9d90d9fc71b72a76c9a41fe33ca089e83df87643`
- **Licence / Redistribution:** MIT Licence.
- **Dimensions:** 2 decision variables, 2 constraint rows, 4 constraint nonzeros, 4 Hessian nonzeros ($Q \succ 0$).
- **Objective Sense:** MINIMIZE (linear $c = [1.5, -2.0]$, quadratic $Q = [[8, 2], [2, 10]]$, offset $= 4.0$).
- **Published Reference Objective:** `8.371875` (exact analytical optimum: $c_1 = 30.5/40 = 0.7625$, $c_2 = 0.475$).
- **SOV-OPT Measured Result:**
  - Status: `OPTIMAL_VERIFIED`
  - Objective: `8.3718750036`
  - Primal solution $x$: `[0.7625000003, 0.4750000001]`
  - Iterations: 6 (Mehrotra predictor-corrector QP)
  - Primal residual: `0.0`
  - Dual residual: `1.70e-10`
  - KKT passed: `true`

---

## Documented Evaluated Instances (Honest Status Reporting)

### 6. FLUGPL — Airline Fleet Allocation MILP

- **Instance Name:** FLUGPL
- **Problem Class:** Mixed-Integer Linear Program (MILP)
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
- **Published Reference Objective:** `1201500` (optimal integer solution); LP relaxation $= 1167185.73$.
- **SOV-OPT Measured Result:**
  - Status: `NUMERICAL_FAILURE` (after 30 branch-and-bound nodes)
  - Conservative Rational Lower Bound: `769500.0`
  - Reason: An infeasible subproblem branch could not establish an exact rational Farkas certificate within the strict tolerance. Under SOV-OPT sovereignty rules, the branch-and-bound engine refuses to prune infeasible subproblems without verified mathematical certificates.

---

### 7. BLEND — Petroleum Blending Problem LP

- **Instance Name:** BLEND
- **Problem Class:** Continuous Linear Program (LP)
- **Application / Domain:** Refinery blending optimization problem.
- **Provenance Evidence:** Netlib LP benchmark library. Contributed by Bruce A. Murtagh.
- **Original Source URL:** https://www.netlib.org/lp/data/
- **Direct File URL:** https://www.netlib.org/lp/data/blend
- **Retrieval Date:** 2026-10-01 (ISO 8601)
- **SHA-256 (Raw Netlib compressed):** `68ae6dc918140675881d6b640d7acac9e5e903ac063476e5767ebfee54f4172d`
- **SHA-256 (Decompressed MPS):** `c8bb193f8af5dcff735a3b8db62077db93625e93cfb26e2b01f83ca3039cbf7d`
- **SHA-256 (Normalized JSON):** `d08bca8f2afded6f44620935c23d429d3d1d405d313e7d37beb4556a31d7a2c1`
- **Licence / Redistribution:** Netlib open access.
- **Dimensions:** 83 decision variables, 74 constraint rows, 521 nonzeros.
- **Integer Variables:** 0.
- **Published Reference Objective:** `-30.812149846` (MINOS 5.3).
- **SOV-OPT Measured Result:**
  - Status: `NUMERICAL_FAILURE`
  - Reason: `Singular or unsafe pivot` in dense LU factorization during Phase I simplex. The basis matrix becomes ill-conditioned / rank deficient without Markowitz sparse pivoting or dynamic threshold pivoting. Reported honestly as required by AGENTS.md.

---

## Missing Refinery Data Disclosure

MRPL (Mangalore Refinery and Petrochemicals Limited) production linear programming models:
- Operational crude assay data, blend fraction limits, tray yields, and economic transfer prices are proprietary internal refinery data.
- No authorized public release of MRPL operational LP matrices exists in public domains.
- Rather than fabricating fictional refinery numbers, SOV-OPT provides the published historical petroleum industry LP benchmark `AVGAS` (Symonds 1955 / Charnes et al. 1952), which has fully reproducible mathematical specifications.
