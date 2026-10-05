# Gate 20 Final Evidence Sync — Public Surfaces Audit

**Repository**: `sov-opt-mrpl-26119`
**Problem Statement**: MRPL SIH 2026 PS 26119
**Core Freeze Main Commit**: `17e46f218f826dd58f5592aa8e75966753f76c32`
**Date**: 2026-10-05

---

## 1. Executive Summary

This audit catalogs every public-facing claim, statistic, version label, coverage entry, and benchmark presentation across `README.md`, `web/index.html`, `web/app.js`, `web/styles.css`, `server.py`, and `docs/`.

Prior to this pass, the repository solver core achieved all Gate 20 milestones (Gate 20A true sparse core, Gate 20B physical RTX 5050 validation, Gate 20C binary cover cuts, and Gate 20D intra-solve parallel branch-and-bound). However, public documentation and the frontend UI retained stale references to older gates (344 tests, 0.3.1 documentation references, un-synchronized PS coverage matrix claiming cutting planes and Mittelmann were not yet implemented, and legacy phrasing).

---

## 2. Inventory of Stale / Inconsistent Public Claims

### A. Test Suite Counts
1. **`README.md:221-222`**: Claimed `Ran 344 tests in 62.5s` and `330 passed, 14 skipped`.
   *Current Authoritative*: **368 tests run: 357 passed, 11 skipped, 0 failures, 0 errors**.
2. **`web/index.html:1938`**: Claimed `Run test suite (344 tests):`.
   *Correction*: Update to `Run test suite (368 tests):`.
3. **`web/app.js:814`**: Hindi localization dictionary mapped `Run test suite (344 tests):` to `परीक्षण सूट चलाएँ (344 परीक्षण):`.
   *Correction*: Update to 368 tests.
4. **`docs/REPRODUCE.md:72, 78`**: Claimed `344 tests` and `OK (skipped=14)`.
   *Correction*: Update to `368 tests` and `OK (skipped=11)`.

### B. Version & Freeze Commit Identity
1. **`web/index.html:1460`**: Trust Card displayed stale commit `v0.3.2 (899ff0a8)`.
   *Correction*: Update to canonical freeze identity: `SOV-OPT v0.3.2` with core freeze commit `17e46f2`.
2. **`docs/QPLIB_SUPPORT.md:6` & `docs/BENCHMARK_METHODOLOGY.md:4`**: Displayed `Solver Version: 0.3.1`.
   *Correction*: Update to `0.3.2`.

### C. Problem Statement Coverage Matrix (`web/index.html:1748-1790`)
1. **Multi-core CPU**: Displayed `PARTIAL: Process batch throughput (2.65x on 4 workers); intra-solve simplex/B&B remain serial`.
   *Correction*: Update status to **`INTRA-SOLVE PARALLEL B&B VALIDATED`**. Document the 1.94x speedup on 2 workers (97.0% efficiency) on identical 287-node search, while preserving historical 2.65x independent batch dispatch as a separate metric.
2. **Cutting planes**: Displayed `ROADMAP: Planned: Gomory cuts; not in current release`.
   *Correction*: Update status to **`VALIDATED BINARY COVER CUTS`**. Document 40–54.5% node reduction on knapsack/oracle MILPs; explicitly record that Gomory/GMI was deferred for safety.
3. **Mittelmann benchmark**: Displayed `NOT YET DEMONSTRATED: Instance acquisition not completed`.
   *Correction*: Update status to **`AUTHENTIC SUBSET EVIDENCE`**. Document 4 authentic Hans Mittelmann instances acquired (`qap15`, `brazil3`, `chromaticindex1024-7`, `supportcase10`) with `chromaticindex1024-7` reaching OPTIMAL_VERIFIED on physical RTX 5050 in 80.21s under numerical floating-point KKT verification.
4. **GPU acceleration**: Displayed `PARTIAL: RTX 5050 physical validation; CPU-only on Render; 1.07x aggregate`.
   *Correction*: Update to **`PHYSICAL HARDWARE VALIDATED`**: 5.81x end-to-end acceleration on 10K true-sparse PDHG workload; Render remains CPU-only.
5. **Sparse linear algebra**: Displayed `PARTIAL: Sparse LU; dense fallback...`.
   *Correction*: Update to **`IMPLEMENTED`**: Sovereign CSR/CSC sparse core, SpMV, and sparse solver path.
6. **Heuristics**: Displayed `ROADMAP`.
   *Correction*: Update to **`IMPLEMENTED`**: Safe rounding heuristic and conservative diving heuristic active.
7. **1M Scale**: Displayed `PARTIAL`.
   *Correction*: Update to **`REPRESENTATION/SPMV STRESS VALIDATED — NOT FULL OPTIMAL SOLVE`** (1M-variable x 500K-row true-sparse GPU representation with 2,999,993 nonzeros on physical RTX 5050; earlier Gate 20A CPU stress test evaluated 2,500,000 nonzeros).

### D. Benchmark Claims & Terminology
1. **GPU 5.81x**: Must be clearly phrased as end-to-end acceleration over CPU on a 10,000-variable true-sparse fixed-iteration PDHG workload (both backends ran 3000 iterations to identical objective); NOT a 5.81x faster optimal solve.
2. **GPU 448.3x**: Must be clearly labeled as a steady-state compute-loop microbenchmark ratio, NOT an end-to-end solver speedup.
3. **Parallel B&B 1.94x**: Primary multicore headline — 1.94x matched-engine solve-to-completion speedup using 2 workers while exploring the identical 287-node search tree, with 97.0% measured parallel efficiency.
4. **Parallel B&B 3.60x**: Secondary result — 16-var multiknapsack, clearly qualified as including concurrent search-order incumbent discovery and subtree pruning (59 nodes vs 321 nodes).
5. **MIPLIB 39x**: Strictly labeled as "fixed-budget node-progress ratio" under an equal 10.0s search budget; strictly NOT solve-to-completion speedup.
6. **Refinery Positioning**: Prominently disclose: "Demonstration model — representative open-literature refinery data; not actual MRPL operational data." All statements claiming "safe for production refinery dispatch" replaced with "numerically verified for the evaluated prototype model".
7. **Trust Passport**: Clarify that LP/QP OPTIMAL_VERIFIED is floating-point numerical KKT verification within declared tolerances; MILP is verified integer incumbent plus safe bound/tree-closure logic; SHA-256 fingerprints are integrity/reproducibility identifiers, not digital signatures or cryptographic certificates.
8. **HiGHS Comparison**: Ensure prominent, un-cherry-picked differential benchmark reporting with losses, LIMIT_REACHED, and numerical failures clearly presented.
