# Instructions to paste into Antigravity

I am developing MRPL SIH PS 26119. This folder is a runnable reference prototype, not a complete industrial solver. Read README.md, docs/02_ARCHITECTURE_AND_MATH.md, docs/04_IMPLEMENTATION_PLAN.md and reports/VALIDATION.md before editing.

First inspect the actual code, create the Python environment, run `python -m unittest discover -s tests -v`, run all shipped examples, and start the dashboard with `python server.py`. Report any failure with a reproducible model. Do not replace the optimizer with scipy.optimize, HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX or cuOpt. Existing solvers may only run in isolated external benchmark processes.

Preserve independent original-model verification, honest statuses, input fingerprints, exact rational bounds, and all failure records. Never fabricate accuracy, speedups, benchmark results, commercial-level scale or completed roadmap features. Do not rename primal simplex as dual simplex or label the CPU route GPU-accelerated. The refinery examples are synthetic. CUDA remains unvalidated until a real device run passes.

Work on one gate at a time in docs/04_IMPLEMENTATION_PLAN.md. Before changing an algorithm, state its mathematical invariants and acceptance tests. Add tests that can detect wrong objectives, unsafe pruning, lost nodes, invalid certificates and inaccurate postsolve recovery. Keep unsupported input rejection until the whole relevant path is implemented.

For the first development increment after baseline validation, propose a reversible canonical transformation design for infinite/free variable bounds and full MPS coverage, with tests. Explain how the finite-box safe-bound implementation changes when bounds become infinite. Do not simply replace infinity with a large constant.

Keep the dashboard connected to real solver outputs. Do not remove verification, hardcode green badges, or prefill fake benchmark charts. Keep Python dependencies minimal and benchmark-only imports outside sovopt/. Preserve offline operation and no telemetry. At each gate report exactly what changed, what passed, remaining limitations, and which claims are now justified.
