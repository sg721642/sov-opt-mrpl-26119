# Changelog — SOV-OPT MRPL PS 26119

## [0.1.5] - 2026-10-01

### MRPL Refinery Planning Digital Twin & Demonstration
- Implemented parameterised refinery digital twin (`sovopt/refinery_twin.py`) representing MRPL Mangalore operations across 4 operational variants:
  - `lp`: Continuous multi-period economic planning with crude blending, unit yields, and quality specs.
  - `milp`: Discrete operational unit commitment binaries ($z \in \{0, 1\}$) and physical minimum turndown limits.
  - `qp`: Smooth operational dispatch with positive semidefinite quadratic penalties damping throughput swings ($\frac{1}{2} \Delta u^T Q \Delta u$).
  - `infeasible`: Diagnostic scenario certifying infeasibility via an exact Farkas certificate ($y \ge 0, y^T A \le 0, y^T b > 0$).
- Added standalone 5-step mathematical verification demonstration script `scripts/demonstrate_refinery_twin.py`.
- Added provenance disclaimer: engineering formulation based on public refining literature (Gary & Handwerk; Meyers), not proprietary MRPL production telemetry.

### Automatic Algorithm Dispatcher & CLI Numerical Trust Report
- Implemented `sovopt/dispatcher.py`: inspects dimensions ($m, n$), nonzeros ($nnz$), integrality, dynamic range, and quadratic structure ($Q$) to route models automatically to simplex, branch-and-bound, or interior-point QP.
- Extended CLI entrypoint (`sovopt/__main__.py`): supports `--method {auto, simplex, ipm, bb, pdhg-cpu, pdhg-gpu}`, `--refinery-twin {lp, milp, qp, infeasible}`, and formatted Numerical Trust Report output (`--report`) displaying $r_p, r_d, r_I$, gap, and certificate status.

### Branch-and-Bound Integer Node Fathoming Hardening
- Hardened integer leaf fathoming in `sovopt/milp.py`: when all integer variables evaluate to integers, the node is verified for primal feasibility, records new incumbents, and fathoms the branch with conservative lower bounds without halting on inherited bound comparisons.

### Checksum Generation & Verification Tooling
- Repaired `SHA256SUMS.json` parsing failure: removed trailing literal backslash-n defect, ensuring valid JSON decoding with standard newline.
- Created `scripts/verify_checksums.py`: provides CLI verification (`scripts/verify_checksums.py`) and generation (`--update`), excluding the checksum file itself and covering all tracked repository files (including newly added docs, scripts, and quarantined files).
- Integrated automated checksum manifest synchronization into `scripts/generate_reports.py` so later report generation cannot silently leave `SHA256SUMS.json` stale.

### Web Dashboard & Model Viewer
- Made `#editor` in `web/index.html` explicitly read-only with styled appearance and added a clear provenance banner (`Verified dataset specification (read-only to preserve dataset provenance and prevent synthetic modification)`).
- Removed input event listener on editor to ensure submitted solves remain strictly identical to verified dataset definitions.

### Farkas Certificate Rendering & Schema Alignment
- Aligned schema across solver (`sovopt/simplex.py`), server, and dashboard UI: set `farkas_certificate` and `verification.farkas_verified` strictly when original-model certification succeeds.
- Displayed exact rational Farkas certificate in UI trust table only when verified against the original model, and rendered non-zero exact multiplier Fractions in solution summary.
- Preserved lossless exact certificate Fractions in downloaded audit JSON records.

### Hardened Differential Verification
- Enforced strict criteria for external solver comparison: required successful termination (`exit_code == 0`), optimal status (`kOptimal`), and verified SOV-OPT status (`OPTIMAL_VERIFIED` with valid KKT) before labelling `MATCH`.
- Required successful external solve with explicitly optimal terminal status before reporting a bound validated against an external optimum, refusing to describe feasible suboptimal objectives as optimum.
- Distinguished internally certified bounds (`BOUND_INTERNALLY_CERTIFIED`) from externally checked bounds when external validation was not run, failed, or lacked a finite objective.
- Distinguished incomplete solves with incumbents from those without, formulating correct comparison notes for both minimization and maximization.
- Validated native-parsed dimensions (`variables`, `constraints`, `integers`) between SOV-OPT and external solver.
- Implemented bound direction validation for minimization ($B \le z^* + \epsilon$) and maximization ($B \ge z^* - \epsilon$).
- Clarified that `BOUND_ONLY` denotes incomplete SOV-OPT evidence (search tree halted at node limit without full tree closure).

### Version Synchronization & Test Suite
- Synchronized version `0.1.5` across runtime, packaging, server, tests, and documentation (`pyproject.toml`, `sovopt/__init__.py`, `server.py`, `tests/test_server.py`, `data/manifest.json`, `web/index.html`, and `START_HERE.html`).
- Added unit test suite `TestDifferentialComparisonLogic` in `tests/test_solver.py` verifying comparison logic across optimal, non-optimal, failed, missing-objective, and direction-validity cases using real benchmark metadata.

### Documentation & Catalogue Synchronization
- Corrected `data/CATALOGUE.md` discrepancy values against published references: AFIRO (`~2.857e-9` vs 11-digit Netlib MINOS 5.3 reference `-464.75314286`) and SC50A (`~4.355e-10` vs 11-digit reference `-64.575077059`), reflecting measured values from run records.

## [0.1.4] - 2026-10-01

### Documentation Consolidation
- Consolidated all documentation into a concise, professional structure:
  - `README.md`: Concise project overview, quick-start commands, algorithm descriptions, and honest limitation disclosures.
  - `docs/ARCHITECTURE.md`: Complete mathematical specifications, module boundaries, objective conventions, trust semantics, and roadmap implementation gates.
  - `docs/VALIDATION.md`: Reproducible validation procedures, test suite structure, external benchmark guide, evidence locations, and coverage gap disclosures.
  - `data/CATALOGUE.md`: Comprehensive dataset provenance, cryptographic hashes, source links, and empty state declarations.
  - `CHANGELOG.md`: Factual release and development history.
  - `AGENTS.md`: Maintained contributor and repository integrity instructions.
- Removed 12 redundant and narrative documents after consolidating unique technical content:
  - `docs/ANTIGRAVITY_PROMPT.md`, `BASELINE_STATUS.md`, `reports/FINAL_AUDIT.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/01_SETUP.md`, `docs/02_ARCHITECTURE_AND_MATH.md`, `docs/03_MODEL_AND_REFINERY.md`, `docs/04_IMPLEMENTATION_PLAN.md`, `docs/05_GPU_AND_DEPLOYMENT.md`, `docs/06_BENCHMARKS.md`, `docs/07_REFERENCES.md`, and `reports/VALIDATION.md`.
- Updated all internal links and documentation references in `START_HERE.html` and `AGENTS.md`.

### Dataset Provenance & Quarantining
- Quarantined `AVGAS` (`avgas.mps`, `avgas.json`) under `data/quarantined/` with explicit explanation: while the file source (HiGHS repository) and SHA-256 are verified, historical attribution to Charnes et al. (1952) / Symonds (1955) has not been verified against primary literature. Excluded from the active verified benchmark suite and default demonstrations.
- Active verified benchmark suite confirmed as: Netlib LP (`AFIRO`, `SC50A`, `SC50B`, `BLEND`) and MIPLIB MILP (`FLUGPL`).
- Made `AFIRO` the default demonstration model across the dashboard, tests, and CLI.

### Test Suite Corrections
- Removed synthetic `replace(m, integer=(0,))` modification on AVGAS.
- Explicitly disclosed the MILP `OPTIMAL_VERIFIED` coverage gap: no admitted original MILP benchmark solves to full tree closure within short automated test timeouts on this machine.
- Updated `test_flugpl_honest_metadata` to enforce mathematical invariants (bounds, node limit, termination state, incumbent feasibility) without requiring fixed status.
- Evaluated `safe_lower_bound` on FLUGPL LP relaxation node using exact rational basis duals.
- Separated `test_server.py` into `HandlerUnitTests` (in-process handler testing) and `ServerIntegrationTests` (loopback socket testing with honest skip when sandbox limits sockets).

### External Differential Validation
- Created `scripts/create_benchmark_env.sh` to provision an isolated virtual environment (`.venv-benchmark`) with `highspy` (1.15.1) and `scipy` (1.17.1).
- Implemented dynamic solver version and dimension detection in `scripts/baseline_worker.py`.
- Updated `scripts/generate_reports.py` to support `SOVOPT_BENCHMARK_PYTHON` environment variable and dynamically iterate over active manifest instances.
- Successfully executed differential comparisons against native HiGHS across all active instances (`MATCH` on LP instances, `BOUND_ONLY` on FLUGPL).

### Web Dashboard & Server
- Completed stale-response UI fix: added `AbortController` to cancel in-flight requests, incremented `currentSolveId` on dataset, backend, and editor input changes to discard late responses, restored button states, and tied displayed model name and backend strictly to returned model metadata.
- Replaced invented zero gap on continuous LP/QP with `— (LP/QP KKT)`. Displayed mantissa precision as `Unknown` when not available.

### Fixed
- **`scripts/generate_reports.py`:** Replaced hardcoded `EXTERNAL_HIGHS_RESULTS` dict with a real subprocess invocation of `baseline_worker.py`. Tries multiple Python interpreters (system, conda, venv). Records `NOT_RUN` or `FAILED` with actual error when highspy/scipy is unavailable; never manufactures a successful comparison. Removes instance-specific hardcoded discrepancies.
- **`sovopt/milp.py`:** Removed misleading "exact integer optimum verified" language from `gap == 0.0` path. A floating-point gap of exactly 0.0 is not an exact rational optimality certificate; the new message explicitly acknowledges the floating-point nature of the gap check and that feasibility is verified numerically only.
- **`web/index.html`:** Removed `includes('VERIFIED')` fallback from status rendering — unknown statuses now display as red `UNKNOWN: <raw_status>` instead of silently green. Added `UNBOUNDED_CERTIFIED` to `STATUS_MAP`. Added `clearResult()` function called on dataset/backend change to invalidate stale results. Fixed `gap === 0.0` display from "0.00% (proven)" to "0.00% (float)".
- **`docs/01_SETUP.md`:** Steps 7–10 no longer reference synthetic results (4865, 4985, 5009.5) or synthetic refinery model names. Updated to describe actual real-source instances (AVGAS, AFIRO, FLUGPL) with correct expected statuses and objective values.
- **`START_HERE.html`:** Steps 7–9 updated to reference authentic verified datasets. FLUGPL description corrected: bound is `1173644.9999999998`, no incumbent found in 50 nodes, status is `LIMIT_REACHED`.
- **`data/CATALOGUE.md` / `reports/FINAL_AUDIT.md` / `reports/VERIFIED_BENCHMARKS.md`:** FLUGPL bound corrected from `1173645.0` to `1173644.9999999998` (exact floating-point display). BLEND truncation-as-sole-cause assertion removed — agreement between SOV-OPT and HiGHS is documented without claiming it proves the cause of the README discrepancy. AVGAS historical attribution marked as plausible-unverified against primary sources.
- **`tests/test_solver.py`:** Added `test_milp_optimality_basis_language` (regression for corrected MILP gap language) and `test_flugpl_honest_metadata` (regression for FLUGPL LIMIT_REACHED status, correct bound range, and no spurious OPTIMAL_VERIFIED). Total tests: 14 (all pass).


### Added
- **Reversible Variable Transformations (`sovopt/transforms.py`):** Canonical standard-form transformations handling lower-bounded, box-bounded, upper-only, free, and fixed variables with mathematically rigorous primal and dual postsolve recovery.
- **Machine-Readable Manifest (`data/manifest.json`):** Cryptographic SHA-256 hashes, source URLs, dimensions, nonzeros, published references, and honest disclosures of empty states for MRPL and Convex QP.
- **Exact Rational Farkas Certificate Engine (`sovopt/simplex.py`, `sovopt/verify.py`):** Exact rational basis solve fallback and exact Fraction dual mapping ensuring branch-and-bound prunes infeasible nodes with mathematical rigor.

- **Exact Rational Basis Dual Engine (`sovopt/simplex.py`, `sovopt/milp.py`):** Added `_exact_dual_from_basis` using `_exact_solve_BT` in exact rational arithmetic (`Fraction`), eliminating IEEE 754 floating-point rounding traps (e.g. $-3.33 \times 10^{-14}$ residual on infinite upper bound variable). Enabled `safe_lower_bound` to evaluate losslessly on every node of MIPLIB FLUGPL, advancing the verified conservative lower bound from root to **1173645.0** at 50 nodes.
- **Invertible Ray Transformation (`sovopt/transforms.py`):** Added `postsolve_ray` to recover recession rays directly through linear transformations without catastrophic cancellation from subtracting shifted primal points.
- **Enhanced Model Validation (`sovopt/model.py`):** Enforced finite `obj_offset`, strictly rejected positive infinity on lower bounds and negative infinity on upper bounds, and validated unique variable names matching dimension $n$. Documented canonical JSON schema.
- **Web Dashboard & Server Stabilization (`web/index.html`, `server.py`):** Implemented explicit `STATUS_MAP` (marking `LIMIT_REACHED` honestly as an amber/incomplete status), separate incumbent/bound/gap display, snapshotting of model/backend, and `currentSolveId` to prevent race conditions on fast dataset switching.
- **Independent Differential Verification (`scripts/baseline_worker.py`, `reports/external_validation.json`):** Integrated native C++ HiGHS 1.15.1 execution mode in external worker, verified full precision agreement on all 6 verified benchmark instances, and proved BLEND discrepancy is due to 11-digit text truncation in 1988 Netlib documentation.
- **Automated Report Generator (`scripts/generate_reports.py`):** Built end-to-end report generator regenerating test records, external validation JSON, and benchmark tables with UTC timestamps and git revision tracking.
- **Documentation Audit & Cleanup:** Fully updated `README.md`, `START_HERE.html`, `docs/01_SETUP.md`, `docs/03_MODEL_AND_REFINERY.md`, `docs/05_GPU_AND_DEPLOYMENT.md`, `docs/06_BENCHMARKS.md`, `docs/IMPLEMENTATION_STATUS.md`, and `data/CATALOGUE.md`, removing all residual synthetic model references.

### Removed
- Removed legacy synthetic models (`data/legacy_synthetic/`), synthetic generator (`scripts/make_examples.py`), stale synthetic reports, and toy QP example (`qp_example.qps`, `qp_example.json`) from active git tracking (preserved in git history).
- Removed synthetic optimization fixtures (`test_box_and_unconstrained`, `test_nonconvex_and_miqp_rejected`) from the active test suite.

## [0.1.1] - 2026-10-01

### Added
- **Verified Dataset Suite:** Added genuine public optimization instances from Netlib LP, MIPLIB, and published literature to `data/verified/`:
  - `avgas.mps`: Aviation gasoline refinery blending LP (Symonds 1955 / Charnes et al. 1952).
  - `afiro.mps`: Netlib LP from Stanford Systems Optimization Laboratory (Michael Saunders).
  - `sc50a.mps`, `sc50b.mps`: Netlib LP staircase economic models.
  - `qp_example.qps`: Convex Quadratic Program with `QUADOBJ`.
  - `flugpl.mps`: MIPLIB airline fleet allocation model (Harvey Wagner / Cray Research).
  - `blend.mps`: Netlib blending LP (evaluating dense basis behavior).
- **Extended MPS / QPS Parser (`sovopt/mps.py`):**
  - Support for `QUADOBJ` Hessian specification in QPS files.
  - Support for `FR`, `MI`, `PL`, `BV`, `FX`, `LO`, `UP` bound types.
  - Support for unbounded variables ($x \ge 0, x \le \infty$).
  - Support for `MAX` and `MIN` objective senses via `OBJSENSE` and negation.
  - Support for objective constant offsets in RHS $N$-row.
  - Support for whitespace-flexible fixed and free MPS continuation lines.
- **Model & Algebra Enhancements (`sovopt/model.py`, `sovopt/simplex.py`, `sovopt/qp.py`, `sovopt/verify.py`):**
  - Infinite/unbounded variable bound support in `Model` and `inequalities()`.
  - Label-aware dual and Farkas certificate reconstruction in revised simplex.
  - Nonzero objective offset recovery in `verify.py`.
  - Infinite-bound initial point handling in QP predictor-corrector.
- **Verified Dataset Catalogue (`data/CATALOGUE.md`):** Complete provenance, URLs, SHA256 hashes, and published reference values.
- **Agent Workflow Guide (`AGENTS.md`):** Comprehensive rules for dataset integrity, git workflow, and mathematical verification.
- **Implementation Status (`docs/IMPLEMENTATION_STATUS.md`):** Roadmap gate tracking against 16-week plan.
- **Verified Benchmarks Report (`reports/VERIFIED_BENCHMARKS.md`):** Measured CPU runtime and precision metrics.

### Changed
- **Active Demo Dashboard (`web/index.html`):**
  - Replaced synthetic refinery demo with verified real-dataset evidence lab.
  - Removed synthetic feed-cost multiplier slider.
  - Added live solve badge and provenance metadata display.
- **Demo Server (`server.py`):**
  - Updated web solver capacity to 100 variables / 150 rows.
  - Exposed verified datasets through `/api/examples`.
- **Test Suite (`tests/`):**
  - Replaced synthetic refinery test with `test_verified_real_instances`.
  - Added `test_honest_failure_statuses` covering FLUGPL and BLEND.
  - All 18 tests passing.

### Retired
- Synthetic refinery models (`examples/refinery_*.json`, `examples/infeasible.json`, `examples/tiny.mps`) retired from active suite and preserved under `data/legacy_synthetic/` with `PROVENANCE.md`.

## [0.1.0] - 2026-10-01
- Initial legacy synthetic reference baseline commit (commit `31f8de8`).
