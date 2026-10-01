# SOV-OPT Gate 7 Verification & Final Audit

**Date:** `2026-10-01`  
**Solver Version:** `0.3.0`  
**Commit:** `1f5969d4c0d0fd31a2ef0072ebfb36a91ebb84a7+dirty`  
**Status:** `GATE 7 PARTIAL — REAL QPLIB SUPPORT + EXPANDED PUBLIC BENCHMARK SUITE`  

## Summary of Gate 7 Deliverables

1. **Official QPLIB Mathematical Convention Implementation:**
   - Implemented exact formula min 0.5 * x^T Q0 x + b0^T x + q0 matching official `qplib.zib.de/doc.html`.
   - Symmetrization properly accounts for lower-triangular Q0 (Q_sym[i, j] = 0.5 * Q0[i, j] for i > j).
   - Validated against authentic `QPLIB_8845` published solution to machine precision (5.12e-16).
   - **Evidence Integrity Separation (Gate 7.1):** Reference solutions are strictly segregated from solver evidence (`evidence_source = QPLIB_PUBLISHED_SOLUTION`, `status = REFERENCE_SOLUTION_VALIDATED`, `kkt_status = PRIMAL_FEASIBILITY_ONLY`). Sovereign `solve_qp` reached iteration limit on `QPLIB_8845` due to 490 equality constraints closing the relative interior during inequality splitting. Gate 7 is honestly marked **PARTIAL**; no fake completion is claimed.

2. **Rigorous Classification & Negative Rejection:**
   - Allow-list for continuous convex QP (`CCL`, `DCL`, `CCB`, `DCB`, `LCL`).
   - Explicit rejection with descriptive error classes for integer/MIQP (`UNSUPPORTED_DISCRETE_VARIABLES`), quadratic constraints (`UNSUPPORTED_QUADRATIC_CONSTRAINTS`), and nonconvex objectives (`UNSUPPORTED_NONCONVEX_QP`).
   - Negative test `QPLIB_0018` verified: cleanly rejected without unsafe dense allocation.

3. **Frozen Public Benchmark Suites:**
   - Netlib LP: 16 candidate instances (9 OPTIMAL_VERIFIED + 7 NUMERICAL_FAILURE) + WOODINFE certificate validation, frozen and verified with Bell Labs `emps` decompressor.
   - MIPLIB 2017: 38 instances stratified across 4 size bins from Benchmark Set v2, evaluated against `miplib2017-v37.solu`.
   - 100% of reported MILP bounds satisfy the conservative lower bound invariant bound <= z*.
   - Benchmark membership was frozen before result evaluation; subsequent capability-classification amendments are versioned and retained in `reports/BENCHMARK_MANIFEST_AMENDMENTS.md`.

4. **Complete Independence & Sovereignty:**
   - Core solver in `sovopt/` uses strictly NumPy and Python standard library.
   - Zero external solver dependencies inside `sovopt/` or `server.py`.
   - External solvers run only in separate subprocess worker processes (`scripts/baseline_worker.py`) for differential comparison.

## Integrity Signatures

- `data/manifest.json`: `d7c141daca173815e90980682f848b5e5172aec09d9c08e906116cc9de85fa80`
- `data/manifests/netlib_lp.json`: `de4db68d90ee077337c367e9d7e4ca29ce97f040e29ddbd5369a054a03ab8215`
- `data/manifests/miplib_milp.json`: `654daa4a0d06102dd6f175dc71daa4eb19151f15891e5c54061507942b7dc155`
- `data/manifests/qplib_convex_qp.json`: `8cfc7d44e71cef3543d825abdd1954f477f40b7839e1a3109d19511d5a18390c`
- `reports/BENCHMARK_MANIFEST_AMENDMENTS.md`: `b416772cf58b72c0e65a2e0d0c38698f1bcec1ade703c65a0e63019ce4986ec9`
- `reports/FROZEN_BENCHMARK_SELECTION.md`: `2b73bbe399435b819ed6d1788183540a4c96c04d1a0e2cb81927dda13857bba7`
- `reports/VERIFIED_BENCHMARKS.md`: `41f94cb2ec11f7289627ce8292348362772737cab342fd80ebb9675961bca22a`
