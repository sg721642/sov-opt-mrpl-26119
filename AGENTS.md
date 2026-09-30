# Agent and Contributor Workflow — SOV-OPT MRPL PS 26119

This document records the dataset integrity, Git workflow, and validation requirements
that apply to every change in this repository. Preserve these instructions; do not
delete or weaken them.

## Repository purpose

SOV-OPT is an original numerical optimization research prototype for MRPL SIH Problem
Statement 26119. The solver core (sovopt/) is sovereign: it must not import or depend
on HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX, cuOpt, or any other
existing optimization solver. NumPy and Python stdlib are the only dependencies for
the core solver.

External solvers are permitted only in separate subprocess/benchmark worker processes
(scripts/baseline_worker.py) for differential comparison. They must never be called
from sovopt/ or from server.py to produce the application's own solutions.

## Dataset integrity requirements

### Prohibited content

- Synthetically generated optimization instances used as evidence of real-world
  performance or MRPL production data.
- Fictional refinery parameters, fabricated business scenarios, or placeholder numbers
  presented as measured results.
- Results from external solvers presented as results from sovopt/.
- GPU execution results presented as CPU results, or vice versa.
- Claimed accuracy percentages, speedups, or commercial-solver comparisons without
  reproducible measured evidence.

### Required provenance for every dataset

Every dataset file in data/verified/ or tests/fixtures/ must have a corresponding
entry in data/CATALOGUE.md recording:
- Instance name and problem class (LP, MILP, convex QP)
- Original source URL and direct file URL
- Retrieval date (ISO 8601) and SHA-256 of the original file
- Application/domain and provenance evidence (real application, anonymized, academic
  benchmark, or synthetic — be explicit)
- Licence or redistribution conditions
- Dimensions (rows, columns, nonzeros, integer variables)
- Objective sense and any objective offset
- Published reference objective/status with source and precision
- Current solver support status and rejection reason where applicable

### Synthetic content

The original shipped examples (examples/refinery_*.json, examples/infeasible.json,
examples/tiny.mps) are explicitly synthetic. They were used to establish the delivery
baseline. They must remain in historical Git commits but must not be presented as:
- Evidence of real-world accuracy
- Validated MRPL production results
- Current benchmark suite entries

They are archived under data/legacy_synthetic/ with a clear provenance disclaimer.

## Git workflow

### Before every commit

1. Review the diff (git diff --staged) and confirm no secrets, credentials, or
   virtual environment files are staged.
2. Run the relevant subset of tests: .venv/bin/python -m unittest discover -s tests -v
3. Confirm all tests that were previously passing still pass. A new test failure is a
   defect to fix before committing, not to work around.
4. Update CHANGELOG.md with a brief entry for the change.
5. Stage only specific reviewed files.

### Commit message format

<type>(<scope>): <imperative description>

Types: feat, fix, test, docs, chore, refactor
Examples:
  chore: preserve legacy synthetic reference baseline
  feat: add verified dataset provenance manifest
  fix: preserve MPS objective sense and offsets
  test: validate original-model recovery on AFIRO

### Push rules

- Never force-push to main.
- Never delete remote history.
- Never publish secrets or credentials.
- Verify the remote SHA after every push.

## Algorithm implementation rules

### What must be preserved

- All existing numerical verification logic (verify.py, exact_farkas, safe_lower_bound)
- Honest failure statuses: NUMERICAL_FAILURE, LIMIT_REACHED, INFEASIBLE_CERTIFIED
- Original-model recovery and verification for all transformations
- Conservative MILP lower bounds using exact rational arithmetic
- The MPS parser's refusal to invent big-M bounds or drop constraints

### What must not be done without explicit gates

- Removing dense-size limits before sparse infrastructure is implemented and tested
- Renaming primal simplex as dual simplex
- Calling np.linalg.solve or any external factorization in the core solver
- Treating an unsupported model as INFEASIBLE or as SOLVED
- Loosening numerical tolerances to make a previously failing test pass
- Hardcoding expected outputs in tests
- Deleting tests to eliminate failures

### MPS parser extensions

When extending the MPS parser (mps.py), each new bound/section type requires:
- A test fixture (real MPS file excerpt in tests/fixtures/)
- A round-trip test: parse → solve → verify against original model
- Documentation of which Netlib/MIPLIB instances are now compatible

### Transformation requirements

Every reversible model transformation (shifting, scaling, bound handling) requires:
- A postsolve function that recovers the original x and dual variables
- A test that checks recovered primal and dual values against the original model
- No transformation that changes the feasible set or optimal value

## Testing requirements

### Test categories that must remain covered

1. LU residuals and iterative refinement
2. Simplex correctness (LP KKT, multiple problem families)
3. QP KKT verification (diagonal and general PSD Q)
4. MILP exhaustive small cases + rational bound validity
5. Infeasibility: Farkas certificate acceptance and rejection
6. MPS parsing: supported subset, rejection of unsupported features
7. PDHG convergence on small LP
8. HTTP API: health, examples, solve, error handling
9. Honest failure paths: NUMERICAL_FAILURE, LIMIT_REACHED, INVALID_MODEL

### Adding real-data tests

When a real dataset is added to tests/fixtures/:
1. Parse it and record the parsed dimensions.
2. Attempt to solve and record the actual status, objective, and residuals.
3. If the solver cannot handle it (e.g., size limit, free variables), record
   UNSUPPORTED with the exact reason. Do not invent a workaround.
4. Compare against published reference objectives only when available.
5. Store results in tests/expected/<instance>.json as a checked-in reference.

## Dashboard requirements

- The dashboard must not display synthetic data as if it were real-world evidence.
- Every displayed result must show: solve timestamp, input hash, solver commit/version.
- Saved results must be clearly distinguished from live solve results.
- The feed-cost multiplier slider applies only to models that genuinely support it;
  remove it when real dataset models are the sole content.
- An empty state is correct and honest when no verified dataset is loaded.
- Browser interaction results must be reported honestly; do not claim visual testing
  occurred if only the HTTP API was tested.

## CUDA / GPU rules

- gpu_executed must be false for all CPU runs.
- The pdhg-cuda backend must not be presented as working on Apple Silicon.
- No GPU speedup claim without measured evidence on NVIDIA hardware.
- CPU PDHG is a first-order method; it may be slower than simplex on small problems.
  Report that honestly.

## Reporting requirements

After completing a development phase, update docs/IMPLEMENTATION_STATUS.md with:
- Which gates from docs/04_IMPLEMENTATION_PLAN.md are satisfied
- What was tested and what the test results were
- What remains unsupported or unimplemented
- Any synthetic content that was removed and where it now lives in history

Do not mark a gate as complete if:
- Tests were deleted rather than replaced
- Tolerances were loosened to pass
- An external solver was used to produce sovopt's own results
- A real-data test was omitted because the instance is unsupported (record UNSUPPORTED)
