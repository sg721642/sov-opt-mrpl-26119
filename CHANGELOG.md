# Changelog — SOV-OPT MRPL PS 26119

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
