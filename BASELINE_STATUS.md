# SOV-OPT Baseline Status
**Date:** 2026-10-01  
**Task:** Gate 0 — Establish reproducible starting point (MRPL SIH PS 26119)

---

## Environment

| Item | Value |
|------|-------|
| Machine | Apple Silicon (arm64) macOS (Darwin) |
| Python version | 3.11.16 (Homebrew `/opt/homebrew/bin/python3.11`) |
| Python 3.12 | Not installed; 3.11 is within supported range (3.11+) |
| NumPy version | 2.3.5 (from `requirements.txt`; arm64 wheel) |
| Virtual environment | `.venv/` created with `python3.11 -m venv .venv` |
| Solver version | 0.1.0 |
| No external solvers | Confirmed: `sovopt` imports only NumPy and stdlib |

> Python 3.12 is not installed on this Mac. Python 3.13.9 is the system Python.
> Python 3.11.16 from Homebrew is the correct native ARM64 interpreter used throughout.

---

## Test Results

```
.venv/bin/python -m unittest discover -s tests -v
```

**All 17 tests passed. Duration: ~4.6 s. No changes to source or tests.**

| Test | Result |
|------|--------|
| test_server.ServerTests.test_http_invalid | ok |
| test_server.ServerTests.test_http_page_and_examples | ok |
| test_server.ServerTests.test_http_solve | ok |
| test_solver.SolverTests.test_bad_candidate | ok |
| test_solver.SolverTests.test_box_and_fixed | ok |
| test_solver.SolverTests.test_degenerate_scaled | ok |
| test_solver.SolverTests.test_fraction_bound_for_any_multiplier | ok |
| test_solver.SolverTests.test_infeasible_certificate | ok |
| test_solver.SolverTests.test_known_random_lp_kkt | ok (50 LP cases) |
| test_solver.SolverTests.test_limits | ok |
| test_solver.SolverTests.test_lu_pivot_refinement | ok |
| test_solver.SolverTests.test_mps | ok |
| test_solver.SolverTests.test_nonconvex_and_miqp_rejected | ok |
| test_solver.SolverTests.test_pdhg | ok |
| test_solver.SolverTests.test_random_integer_exhaustive | ok (25 MILP cases) |
| test_solver.SolverTests.test_random_qp_known_kkt | ok (20 QP cases) |
| test_solver.SolverTests.test_refinery | ok |

No tests were modified, deleted, or weakened. No tolerances were relaxed.

---

## Model Solve Results

Results saved under `reports/local_validation/2026-10-01T0116/`.

### Refinery LP (examples/refinery_lp.json)
- Status: OPTIMAL_VERIFIED
- Objective: 4865.0  [PASS: matches expected 4865]
- Algorithm: Two-phase primal revised simplex
- Iterations: 5
- x = [45.0, 15.0, 17.5, 32.5]
- Primal residual: 0.0, Dual residual: 0.0
- Complementarity: 2.67e-18, Duality gap: 2.67e-18
- KKT passed: true, Elapsed: ~2.8 ms

### Refinery MILP (examples/refinery_milp.json)
- Status: OPTIMAL_VERIFIED
- Objective: 4985.0  [PASS: matches expected 4985]
- Algorithm: Rational-bound branch-and-bound, 3 nodes
- x = [45.0, 15.0, 17.5, 32.5, 1.0] — high_feed_enabled = 1
- Best bound: 4984.999999999999, Relative gap: 2.85e-17
- Open nodes: 0 (tree fully closed)
- NOTE: kkt_passed=false in verification is expected for integer solutions;
  OPTIMAL_VERIFIED is established by B&B tree closure + rational lower bounds.

### Refinery Convex QP (examples/refinery_qp.json)
- Status: OPTIMAL_VERIFIED
- Objective: 5009.500002267  [PASS: expected ~5009.5, KKT verified]
- Algorithm: Primal-dual predictor-corrector QP, 10 iterations
- Primal residual: 1.22e-09, Dual residual: 1.27e-10
- Complementarity: 5.81e-10, Duality gap: 2.02e-09
- KKT passed: true, Elapsed: ~2.2 ms

### Infeasible (examples/infeasible.json)
- Status: INFEASIBLE_CERTIFIED  [PASS]
- Certificate: [1.0, 1.0, -0.0, 0.0]
- Exact Farkas check: passed (rational arithmetic on binary64 input)
- Conflict: variable must simultaneously be >= 8 AND <= 3

### Tiny MPS (examples/tiny.mps)
- Status: OPTIMAL_VERIFIED
- Objective: -11.0  [PASS: matches expected -11]
- Algorithm: Two-phase primal revised simplex, 2 iterations
- Primal residual: 0.0, KKT passed: true

---

## PDHG-CPU Backend (Refinery LP)

Run: .venv/bin/python -m sovopt examples/refinery_lp.json --backend pdhg-cpu

- Status: OPTIMAL_VERIFIED
- Objective: 4864.999999998742 (approx 4865)
- Algorithm: Diagonal PDHG with periodic averaging restart
- Iterations: 200 (converged within max_iter=50000)
- Primal residual: 1.10e-12, Dual residual: 3.84e-12
- Duality gap: 2.58e-13
- gpu_executed: FALSE — CPU-only NumPy execution
- Setup time: 5.76e-05 s, Compute time: 1.46e-03 s

CUDA unavailable on Apple Silicon. The pdhg-cuda backend requires CuPy and an NVIDIA
GPU. No GPU execution occurred and no GPU execution was claimed. The CUDA RawKernel
source exists in sovopt/pdhg.py but was not compiled or run.

---

## API Endpoint Checks

Server started: .venv/bin/python server.py --port 8000 (running in background)

- GET /health  -> {"status": "ok", "version": "0.1.0"}  PASS
- GET /api/examples  -> returns refinery_lp, refinery_qp, refinery_milp, infeasible  PASS
- POST /api/solve (refinery_lp, cpu)  -> OPTIMAL_VERIFIED, objective 4865.0  PASS

Browser/visual UI interaction was NOT checked — no browser automation tools are
available in this environment. The underlying HTTP API was confirmed working via curl.

---

## Code Changes Made

NONE. The source was not modified. All 17 tests passed on the original unmodified
code on the first run. No fixes were required.

---

## Known Limitations

- Dense only: no sparse LU, no Markowitz pivoting
- Primal simplex only: no dual simplex, no Devex, no Harris ratio
- Variable bounds must be finite: infinite variable bounds not supported
- No free variables
- No presolve (only row scaling and variable shifting)
- No cuts in MILP (no GMI/MIR)
- Size caps: 250 variables / 1000 rows (CLI); 30 variables / 80 rows (web)
- QP: normal equations; conditioning may limit reliability on non-diagonal Q
- No MIQP support
- No homogeneous self-dual embedding (QP infeasibility may hit NUMERICAL_FAILURE)
- CUDA unavailable on Apple Silicon
- MPS parser covers basic subset only (no RANGES, no free rows)
- OPTIMAL_VERIFIED is a numerical tolerance claim, not a formal exact certificate
- Synthetic 4-variable refinery models only; no MRPL production data

---

## Local Dashboard URL

http://127.0.0.1:8000

Server is running (started with .venv/bin/python server.py --port 8000).
Open in Chrome or Safari. To stop: Ctrl+C in the terminal running server.py.

---

## Summary

| Check | Outcome |
|-------|---------|
| Python 3.11.16 venv + NumPy 2.3.5 installed | PASS |
| 17/17 unit tests pass | PASS |
| Refinery LP objective = 4865 | PASS |
| Refinery MILP objective = 4985 | PASS |
| Refinery QP objective ~5009.5, KKT verified | PASS |
| Infeasible: exact Farkas certificate accepted | PASS |
| Tiny MPS objective = -11 | PASS |
| PDHG-CPU: LP solved, gpu_executed=false | PASS |
| /health, /api/examples, POST /api/solve | PASS |
| Browser UI visual interaction | NOT CHECKED |
| CUDA/GPU execution | BLOCKED (Apple Silicon) |
| Source changes required | NONE |
