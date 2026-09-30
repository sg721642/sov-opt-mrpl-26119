# Changelog — SOV-OPT MRPL PS 26119

## [0.1.2] - 2026-10-01

### Added
- **Reversible Variable Transformations (`sovopt/transforms.py`):** Canonical standard-form transformations handling lower-bounded, box-bounded, upper-only, free, and fixed variables with mathematically rigorous primal and dual postsolve recovery.
- **Machine-Readable Manifest (`data/manifest.json`):** Cryptographic SHA-256 hashes, source URLs, dimensions, nonzeros, published references, and honest disclosures of empty states for MRPL and Convex QP.
- **Exact Rational Farkas Certificate Engine (`sovopt/simplex.py`, `sovopt/verify.py`):** Exact rational basis solve fallback and exact Fraction dual mapping ensuring branch-and-bound prunes infeasible nodes with mathematical rigor.

### Changed
- **Real-Data-Only Test Suite (`tests/test_solver.py`):** Eliminated all handmade/synthetic optimization fixtures (`test_box_and_unconstrained`, `test_nonconvex_and_miqp_rejected`). Labeled `test_bad_candidate_validation` as verifier unit test probes challenging `verify.py` with perturbed candidate vectors on the real AVGAS model. All 12 active tests pass deterministically.
- **Transformation Validation (`sovopt/transforms.py`, `sovopt/simplex.py`):** Validated invertible affine change of variables ($x = D \tilde{x} + s$ with $D > 0$) on real Netlib AFIRO with machine-precision recovery ($2.22 \times 10^{-16}$ primal, $2.11 \times 10^{-17}$ dual residual). Fixed all-fixed ($n_{\text{trans}} = 0$) array shape and row constraint evaluation (`OPTIMAL_VERIFIED` or `INFEASIBLE_CERTIFIED`), and ensured strictly feasible base points within $[l, u]$ for recession rays in unconstrained systems ($m_{\text{total}} = 0$).
- **MILP Bound Accounting (`sovopt/milp.py`):** Removed `[rootlb]` pinning bug from `all_bounds`. Incorporated `model.obj_offset` in exact rational arithmetic (`Fraction`) prior to conservative downward rounding (`downward_float`). Updated FLUGPL bounds test to accept verified improvements while enforcing bounds and limits.
- **Objective Conventions & Verification Rigor (`sovopt/qp.py`, `sovopt/mps.py`, `sovopt/verify.py`):** Unified canonical minimization convention (negated $Q$ on `MAX` in QPS parser, eliminated double negation in `solve_qp`). Removed `model.obj_offset` from KKT relative denominators in `verify.py` for shift-invariance. Documented numerical PSD eigenvalue checks. Added lossless exact Farkas JSON export/reload and re-verification.
- **Independent Provenance & Honest Disclosures (`data/CATALOGUE.md`, `data/manifest.json`, `web/index.html`):** Recorded exact Netlib BLEND discrepancy ($+1.72 \times 10^{-10}$) against 11-digit Netlib README reference. Explicitly stated "No authorized MRPL dataset is available in this project" across docs and UI. Added standalone MPS parser to `scripts/baseline_worker.py` independent of `sovopt`.
- **HTTP Server Test Robustness (`tests/test_server.py`):** Added direct HTTP Handler invocation fallback for environments with loopback TCP socket restrictions.
- **Simplex Standard-Form Representation (`sovopt/simplex.py`):** Direct standard-form equality row handling and unscaled fallback for equilibration, resolving Netlib `BLEND` to machine precision (`OPTIMAL_VERIFIED`, objective `-30.812149845828237`, 555 iterations).

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
