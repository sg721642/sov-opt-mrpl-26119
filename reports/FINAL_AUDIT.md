# SOV-OPT Gate 7 Verification & Final Audit

**Date:** `2026-10-01`  
**Solver Version:** `0.3.1`  
**Commit:** `a0ae370dd23cb93ab2b6faeeb38e6d808388993b+dirty`  
**Status:** `GATE 7 COMPLETE — EQUALITY-AWARE CONVEX QP INTERIOR-POINT HARDENING`  

## Summary of Gate 7 Deliverables

1. **Equality-Aware Convex QP Interior-Point Solver (Gate 7.2):**
   - Native equality-aware Mehrotra predictor-corrector architecture handles equality constraints directly in the saddle-point KKT system.
   - Eliminates artificial inequality-slack duplication that previously destroyed the relative interior.
   - Infeasible-start IPM initialization with strictly internal starting point; zero external solver or reference vector usage in solver.
   - Independently solved authentic public convex continuous instance `QPLIB_8845` (1546 vars, 777 rows) to `OPTIMAL_VERIFIED`.
   - Full original-model KKT verification passed at tol=1e-7 (primal_res=4.26e-11, dual_res=1.03e-10, comp=1.48e-12).
   - Evaluated `QPLIB_9002` (2890 vars, 1649 rows) to `OPTIMAL_VERIFIED` within declared resource limits.
   - Discrepancy against published official QPLIB reference objective on `QPLIB_8845`: 1.59e-10 relative error.
   - QPLIB reference `.sol` vectors are segregated to external differential comparison blocks only and never influence solver execution.
   - Gate 7 is marked **COMPLETE**.

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

- `data/manifest.json`: `a9c377f8a196ac50a3e59edcba79b6e924ced11afee0299becac4b7ff9337a48`
- `data/manifests/netlib_lp.json`: `de4db68d90ee077337c367e9d7e4ca29ce97f040e29ddbd5369a054a03ab8215`
- `data/manifests/miplib_milp.json`: `654daa4a0d06102dd6f175dc71daa4eb19151f15891e5c54061507942b7dc155`
- `data/manifests/qplib_convex_qp.json`: `8cfc7d44e71cef3543d825abdd1954f477f40b7839e1a3109d19511d5a18390c`
- `reports/BENCHMARK_MANIFEST_AMENDMENTS.md`: `b416772cf58b72c0e65a2e0d0c38698f1bcec1ade703c65a0e63019ce4986ec9`
- `reports/FROZEN_BENCHMARK_SELECTION.md`: `2b73bbe399435b819ed6d1788183540a4c96c04d1a0e2cb81927dda13857bba7`
- `reports/VERIFIED_BENCHMARKS.md`: `19718ab0057df2f37e93d825136e7eec9ad56c268a3faf6ed5066a350acff1df`
