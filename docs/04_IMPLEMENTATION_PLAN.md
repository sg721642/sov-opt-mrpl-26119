# Implementation plan from runnable prototype to research submission

The runnable code covers an early reference milestone. The attached PDF describes a much larger solver engineering project. Do not mark its entire competition-critical list completed simply because this demo runs. Work in the following dependency order, and keep the reference solver available for differential tests.

## Gate 0 — Establish a reproducible starting point

**Do now:** follow the setup guide, run all tests, solve each example, and retain the result JSON files. Initialize your own Git repository only after reviewing the package, commit the baseline, and record the commit hash in future benchmark metadata. Keep generated virtual environments and proprietary datasets out of Git.

**Pass:** all 17 tests pass on the development machine; example hashes and outcomes match; no solver import brings in HiGHS/SCIP/CBC/cuOpt; the editor can run the server and CLI.

## Gate 1 — Broaden mathematical coverage

**Next tasks:** add model support for free variables and one-sided infinite bounds using reversible transformations. Add full fixed/free MPS parsing, objective offsets and RANGES with parser fixtures. Implement a QPLIB parser only for continuous convex QP with linear constraints. Reject all other QPLIB classes.

**Files:** extend `model.py`, `mps.py`, add `transforms.py`, `qplib.py`, parser fixture directories and round-trip tests.

**Pass:** solve tiny analytical examples for every transformation; verify recovered primal and dual solutions against the original model; prove unsupported inputs are rejected. Do not remove current finite-bound restrictions before the relevant algorithms and safe-bound logic handle infinity correctly.

## Gate 2 — Build real sparse numerical infrastructure

**Tasks:** introduce CSR/CSC canonical storage without dense materialization. Implement sparse LU with threshold/Markowitz pivoting; test FTRAN/BTRAN, singular detection and iterative refinement. Add product-form eta updates and refactorization triggers. Keep full refactorization as a trusted fallback.

**Files:** add `sparse_matrix`, `sparse_lu`, `basis`, and a focused numerical test suite. A C++17 or Rust core becomes appropriate when performance profiling justifies the rewrite; this Python release has no C ABI.

**Pass:** residual checks across sparse matrices with row permutations, near-singular pivots and controlled scaling; measured memory remains proportional to sparse factors rather than a dense basis; randomized comparisons against the reference algebra occur outside the sovereign optimization boundary when using external libraries.

## Gate 3 — Implement robust dual simplex

**Tasks:** bounded-variable revised dual simplex, dual Phase I, Devex pricing, two-pass Harris ratio tests, bound flips, degeneracy handling and numerical recovery. Add warm-startable basis objects. Do not rename the existing primal method to satisfy the roadmap.

**Pass:** primal/dual objective agreement and original-model residual checks on a frozen small LP suite; warm starts yield the same answer as cold starts; failure paths preserve honest statuses.

## Gate 4 — Add reversible presolve and scaling

**Tasks:** fixed-variable elimination, empty rows, singleton rows, safe bound tightening and explicit transformations. Keep a postsolve stack restoring variables and multipliers in reverse order. Add column scaling only with correct objective/Q/bound transformations.

**Pass:** every reduction has primal/dual recovery tests; scaling and presolve on/off agree on objectives; original-model checks pass, including when presolve proves infeasibility. The current release has only row scaling and variable shifting.

## Gate 5 — Improve MILP without weakening bounds

**Tasks:** reuse dual-simplex bases, pseudocost branching, limited strong-branching initialization, rounding/repair/diving heuristics and a checked tree log. Replace expensive Fraction loops with rigorously outward-rounded interval bounds only after validating them against the rational reference.

**Pass:** exhaustive small integer cases; valid lower bounds for arbitrary dual estimates; interruption preserves all unresolved nodes; incumbent rounding never implies optimality by itself. Add a replayable proof artifact if you want to claim independently reproducible tree certification.

## Gate 6 — Harden convex QP

**Tasks:** sparse augmented KKT systems, regularization safeguards and inertia/convexity handling; robust equality elimination; infeasibility mechanisms. Validate more than diagonal Q matrices, including PSD matrices with rank deficiency and near-dependent equalities.

**Pass:** original KKT residuals and reference objectives on a frozen supported QPLIB subset, with unsupported/nonconvex problems separately counted. Do not turn a small negative eigenvalue into a PSD claim merely by using a loose tolerance.

## Gate 7 — Validate actual GPU execution

**Tasks:** run the included CUDA CSR kernels on an NVIDIA machine; check CPU/GPU SpMV elementwise and final residuals; add device/memory/error handling. Move canonical input to sparse storage. Improve restart policies, step adaptation and dispatch only after profiling.

**Pass:** identical input hashes, comparable accepted accuracy, cold/warm timing separation, CPU verification and transfer costs included, repeated medians, and failure records. Only then state a measured speedup on the tested suite. A small GPU slowdown is an acceptable observation.

## Gate 8 — Introduce cuts cautiously

**Tasks:** GMI/MIR generation, coefficient-growth filters, exact/interval validity checks and provenance per cut. Retain a cut-free baseline.

**Pass:** no valid integer points removed in exhaustive small tests; no false infeasibility or improved-but-invalid optimum; cut-on/off comparisons and numerical safeguards recorded. Cuts are absent from this release.

## Gate 9 — Freeze benchmark evidence

**Tasks:** record instance hashes and official provenance, supported feature filter, reference solution versions, seeds, time limits, machine, compiler/Python, dependency versions, solver commit, thread counts and all failures. Split development/held-out problems before tuning. Compare with an external baseline at matched accuracy.

**Pass:** a judge can reproduce results from source and manifest. Do not promise 95% Netlib success, 2× GPU acceleration or million-variable solves until measured.

## Gate 10 — Deliver the competition story

**Tasks:** connect the verified core to a realistic cited refinery model family; keep the UI secondary; package an offline CLI, API, model provenance, audit records and a concise demo video. Show a valid solve, an infeasible model, an integer gap and a numerical stress case.

**Pass:** every slide claim maps to source code or a saved experiment. Clearly separate implemented, tested on hardware, and planned features.

## Suggested sixteen-week sequence

| Weeks | Focus | Review evidence |
|---|---|---|
| 1–2 | Reproducible reference, canonical model and parsers | Fixtures and original-model verifier |
| 3–4 | Sparse algebra and basis updates | Linear-system residual and memory tests |
| 5–6 | Dual simplex and numerical recovery | Frozen LP correctness suite |
| 7 | Presolve/postsolve and scaling | Transformation round trips and ablations |
| 8–9 | MILP warm starts, branching, heuristics | Exhaustive small problems and valid bounds |
| 10 | QP hardening | Supported convex-QP suite |
| 11–12 | GPU sparse PDHG and dispatch | Hardware-tested end-to-end comparisons |
| 13 | Safe cuts if prior gates pass | Validity checks and cut ablation |
| 14 | Refinery case and API | Provenance and industrial-model review |
| 15 | Frozen public benchmarks | Complete results including failures |
| 16 | Hardening, packaging, demo | Reproduction on a second machine |

This is an engineering schedule, not a guarantee. If time is short, demonstrate the tested subset and remove feature claims; do not remove verification to preserve them.
