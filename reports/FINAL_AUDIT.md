# SOV-OPT Gate 7 Verification & Final Audit

**Date:** `2026-10-01`  
**Solver Version:** `0.3.0`  
**Commit:** `fc5b537d98a952f01183ae83aea0056e2f9c747f+dirty`  
**Status:** `GATE 7 COMPLETE — REAL QPLIB SUPPORT + EXPANDED PUBLIC BENCHMARK SUITE`  

## Summary of Gate 7 Deliverables

1. **Official QPLIB Mathematical Convention Implementation:**
   - Implemented exact formula min 0.5 * x^T Q0 x + b0^T x + q0 matching official `qplib.zib.de/doc.html`.
   - Symmetrization properly accounts for lower-triangular Q0 (Q_sym[i, j] = 0.5 * Q0[i, j] for i > j).
   - Validated against authentic `QPLIB_8845` published solution to machine precision (5.12e-16).

2. **Rigorous Classification & Negative Rejection:**
   - Allow-list for continuous convex QP (`CCL`, `DCL`, `CCB`, `DCB`, `LCL`).
   - Explicit rejection with descriptive error classes for integer/MIQP (`UNSUPPORTED_DISCRETE_VARIABLES`), quadratic constraints (`UNSUPPORTED_QUADRATIC_CONSTRAINTS`), and nonconvex objectives (`UNSUPPORTED_NONCONVEX_QP`).
   - Negative test `QPLIB_0018` verified: cleanly rejected without unsafe dense allocation.

3. **Frozen Public Benchmark Suites:**
   - Netlib LP: 16 candidate instances + WOODINFE certificate validation, frozen and verified with Bell Labs `emps` decompressor.
   - MIPLIB 2017: 38 instances stratified across 4 size bins from Benchmark Set v2, evaluated against `miplib2017-v37.solu`.
   - 100% of reported MILP bounds satisfy the conservative lower bound invariant bound <= z*.

4. **Complete Independence & Sovereignty:**
   - Core solver in `sovopt/` uses strictly NumPy and Python standard library.
   - Zero external solver dependencies inside `sovopt/` or `server.py`.
   - External solvers run only in separate subprocess worker processes (`scripts/baseline_worker.py`) for differential comparison.

## Integrity Signatures

- `data/manifest.json`: `d7c141daca173815e90980682f848b5e5172aec09d9c08e906116cc9de85fa80`
- `data/manifests/netlib_lp.json`: `de4db68d90ee077337c367e9d7e4ca29ce97f040e29ddbd5369a054a03ab8215`
- `data/manifests/miplib_milp.json`: `654daa4a0d06102dd6f175dc71daa4eb19151f15891e5c54061507942b7dc155`
- `data/manifests/qplib_convex_qp.json`: `8cfc7d44e71cef3543d825abdd1954f477f40b7839e1a3109d19511d5a18390c`
- `reports/FROZEN_BENCHMARK_SELECTION.md`: `2b73bbe399435b819ed6d1788183540a4c96c04d1a0e2cb81927dda13857bba7`
- `reports/VERIFIED_BENCHMARKS.md`: `d8849795ddace73f8194dc9499d8bfa2894a386cf4f5ac57544661636656ee90`
