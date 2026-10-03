# Changelog — SOV-OPT MRPL PS 26119

## [0.3.10] - 2026-10-03

### Gate 14: Final Accessibility Hotfix + Full Hindi Localization

- **fix(web): Complete font scaling and exhaustive Hindi localization:**
  - Enforced CSS typography scaling with `calc(... * var(--accessibility-font-scale, 1.0)) !important` across masthead, hero carousel, slide titles, slide subtitles, navigation items, buttons, cards, forms, inputs, labels, and table cells, strictly satisfying `size(0.9) < size(1.0) < size(1.1)` in headless CDP verification.
  - Implemented exhaustive DOM-wide Hindi localization engine in `web/app.js` with comprehensive `TRANSLATION_MAP` (900+ entries), whitespace-normalized lookup, and automatic translation across text nodes and attributes (`placeholder`, `title`, `aria-label`).
  - Integrated dynamic re-translation on tab switching, PFD flowsheet rendering, scenario comparison metrics, solver variable tables, convergence chart placeholders, and unit inspectors.
  - Preserved allowlisted technical terms, personal names, official institutional mastheads, and benchmark dataset identifiers in English.
  - Validated 100% full coverage across all 11 portal views with automated CDP visible-text audit, achieving exactly 0 untranslated non-allowlisted English phrases.
  - Checksum manifest updated in `SHA256SUMS.json`; 0 diff in `sovopt/`, `data/`, and `reports/`.

## [0.3.9] - 2026-10-03

### Gate 13: Accessibility Controls and Solve Loading State Hotfix

- **fix(web): Resolve accessibility controls and solve loading state:**
  - Implemented real bidirectional English/Hindi UI language toggle with centralized `I18N` dictionary, `data-i18n` attributes, and `localStorage` persistence (`sovopt-language`). Preserved all technical identifiers (SOV-OPT, MRPL, LP, MILP, QP, PDHG, KKT, SHA-256, CUDA, RTX 5050, OPTIMAL_VERIFIED, INFEASIBLE_CERTIFIED, VarunNetra, 177365, personal names) and institutional masthead strings verbatim.
  - Implemented bounded accessibility font scaling controls (A- = 90%, A = 100%, A+ = 110%) with `--accessibility-font-scale` root property, active state indicators, and `localStorage` persistence (`sovopt-font-scale`).
  - Resolved Run Optimization button infinite loading defect by implementing a robust `try / finally` async lifecycle, guaranteeing that the button always resets to an enabled state on every exit path (optimal solve, infeasible certified, numerical failure, limit reached, HTTP error, timeout, JSON parse error). Allowed brief 900ms success confirmation state before restoring the enabled "Run Optimization" action.
  - Synchronized navbar quick-action solve button (`btn-header-solve`) with operations console solve button (`btn-run-solve`).
  - Added duplicate solve execution protection during active request processing.
  - Zero solver mathematics changes; zero benchmark evidence alterations.

## [0.3.8] - 2026-10-03

### Gate 12: MRPL-Style SIH Portal UI Freeze

- **feat(web): Freeze MRPL-style SIH portal experience:**
  - MRPL-branded institutional masthead (logo, title, subtitle, green rule) matching official MRPL design language.
  - MRPL horizontal green navigation bar; About Us placed directly after Home in both desktop and mobile drawer.
  - SIH Team Identity pill strip: `Smart India Hackathon 2026 | TEAM NAME VarunNetra | TEAM ID 177365`.
  - Animated Latest Updates ticker (6 factual messages, CSS keyframe loop, pause on hover/focus/tab-hidden, `prefers-reduced-motion` fallback).
  - Six-slide hero carousel with 5000ms auto-advance, 750ms transitions, subtle artwork zoom, RAF progress bar, and solver-driven process-flow animation.
  - Authentic team portraits for all 6 members; strict order: Khagesh (Leader), Satyam (#2), Sudipto, Ayush, Shivanshu, Muskan.
  - About Us and Contact Us pages with verified RGIPT email and LinkedIn links.
  - Truthful initial Trust Passport state: `Not executed` / `Run solver to verify` / `—`.
  - Solver button spinner and one-time check animation; IntersectionObserver section reveals (60ms stagger).
  - Hardened `server.py` static file router: strips query strings via `urlsplit`, adds `.webp` MIME type, serves `Cache-Control: no-store`.
  - Added `tests/test_server.py` coverage for static asset serving with query parameters.
  - Removed prohibited student prototype disclaimer from all visible UI.
  - Committed 7 authentic image assets (`web/assets/MRPL_logo.jpg` + 6 team portraits).
  - Added `docs/DEPLOYMENT.md` with truthful server configuration, environment variables, and security safeguards.
  - Checksum manifest updated: 303 entries, all 81 public benchmark raw-mode hashes unchanged.
  - Full test suite: 340 tests, 326 passed, 14 skipped, 0 failures, 0 errors.

## [0.3.7] - 2026-10-03


### Gate 11: Final System Audit, Dashboard Integrity & Provenance Documentation

- **chore(audit): Eliminate fabricated metrics, enforce honest empty states, and synchronize documentation:**
  - Removed static fabricated `'Residual 1.42 × 10⁻¹⁵'` string from overview KKT verification widget in `web/app.js`, replacing it with honest `'Run solver to verify'` placeholder when viewing un-executed scenario presets.
  - Eliminated hardcoded fabricated solver metrics (`iterations: 109`, `elapsed_seconds: 0.0482`, `primal_residual: 1.42e-15`, `dual_residual: 2.84e-14`) from `exportAuditJSON` in `web/app.js` when no live solve has occurred, outputting explicit `status: 'NOT_EXECUTED'` and null metrics instead.
  - Made live solve provenance pill dynamically display backend `solver_version`.
  - Updated `docs/ARCHITECTURE.md` roadmap gate table to accurately record completed Gates 8 (GPU PDHG physical validation on RTX 5050), 9 (fused RawKernels and 1.81× aggregate CUDA implementation improvement [Gate 9 CUDA vs Gate 8 CUDA]; 1.07× same-machine CPU/CUDA ratio; ≥2× same-machine acceleration not demonstrated), 10 (editorial dashboard), 10.1 (graph correctness), and 11 (system audit), removing outdated planned cutting-planes entry.
  - Synchronized test counts in `docs/VALIDATION.md` to reflect 299 tests across 15 modules (286 passing, 13 skipped in restricted sandbox).
  - Verified 100% test suite pass rate (299 tests, 0 failures, 13 skipped) and 100% SHA-256 integrity match across all 292 entries in `SHA256SUMS.json`.

### Gate 10.1: Dashboard Graph Data-Correctness and State Synchronization

- **fix(dashboard): Make solver graphs data-correct and state-synchronized:**
  - Connected convergence chart renderer directly to solver iteration/node arrays (`history`, `convergence_history`).
  - Added support across all mathematical problem classes: LP simplex objective progression, MILP B&B dual bound and incumbent trajectories, and QP/PDHG log-scale KKT residual contraction.
  - Synchronized state with `STATE.isStale` flag and `solveGen` race-condition fencing to prevent stale-data display during input adjustments.

## [0.3.6] - 2026-10-02

### Gate 10: Editorial Refinery Workstation UI, Functional QA & Responsive Layout

- **feat(ui): Complete high-end industrial editorial redesign and interaction polish:**
  - Redesigned UI architecture from dark generic SaaS theme into a refined warm editorial refinery workstation.
  - Resolved table clipping and viewport horizontal overflow on standard laptops (1366px, 1440px, 1512px) by decoupling `.overview-tables-layout`, eliminating global `white-space: nowrap` on descriptive table cells, and establishing strict viewport boundary constraints (`overflow-x: hidden`).
  - Segregated execution platforms in the header: explicitly distinguished local CPU execution (`CPU · Sovereign`) from benchmark evidence node (`RTX 5050`).
  - Added hardware notice banner and truthful auto-fallback for `pdhg-cuda` on Apple Silicon.
  - Implemented dynamic stale state tracking across all parameter sliders and selectors, alerting users when inputs are modified pending optimization.
  - Implemented mathematical infeasibility handling: certified rational Farkas proof display, primal vector nullification, zeroed stream flows on the interactive PFD, and explicit status communication.
  - Bound all 8 views, interactive PFD components, scenario delta matrix, telemetry strips, and JSON/CSV export actions to live API responses.
  - Parameterized `sovopt/refinery_twin.py` and `server.py` to support real-time user overrides for crude costs and fuel demand quotas.
  - Passed all 299 repository unit tests and verified 0 missing DOM element IDs or unhandled JS exceptions.

## [0.3.5] - 2026-10-02

### Gate 9.1: Cross-Platform Checksum Portability Hardening

- **fix(integrity): Make checksum verification cross-platform via dual-mode policy:**
  - Upgraded `scripts/verify_checksums.py` to support explicit dual-mode verification:
    - `mode: "raw"`: Verifies raw disk bytes without modification. Applied to all optimization model files (`*.mps`, `*.qplib`, `*.sol`, `*.solu`, `*.lp`), benchmark datasets (`data/netlib/*`, `data/miplib/*`, etc.), and primary provenance manifests (`data/manifests/*.json`).
    - `mode: "text-lf"`: Verifies canonical text with CRLF normalized to LF (`\r\n` -> `\n`). Applied to source code, documentation, scripts, tests, web files, and repository bookkeeping files subject to OS Git checkout EOL conversions.
  - Upgraded `SHA256SUMS.json` schema to explicit dictionary entries (`{"sha256": "...", "mode": "raw" | "text-lf"}`), with full backward compatibility for legacy string-only hashes.
  - Enhanced `.gitattributes` to explicitly mark all benchmark directories (`data/quarantined/*`, `data/raw/*`, `data/refinery/*`, `data/miplib2017-v37.solu`) with `-text`, guaranteeing byte immutability across Windows and POSIX systems.
  - Guaranteed 100% preservation of all 81 public benchmark provenance SHA-256 digests across Netlib, MIPLIB, and QPLIB manifests without alteration.
  - Added unit test suite `tests/test_checksum_portability.py` with 8 comprehensive cross-platform regression tests.
  - Authored `docs/INTEGRITY.md` detailing the dual-mode checksum architecture, EOL normalization rationale, and provenance invariants.

## [0.3.4] - 2026-10-02

### Gate 9: GPU Performance Engineering for Restarted PDHG

- **perf(gpu): Reduce PDHG CUDA execution overhead via fused RawKernels and zero-allocation pipeline:**
  - Implemented fused sovereign CUDA RawKernels in `sovopt/cuda_backend.py`:
    - `spmv`: grid-stride CSR matrix-vector product with `const __restrict__` pointers, `#pragma unroll 4`, and direct writing to destination buffer.
    - `dual_step_fused`: single-launch dual proximal projection and running ergodic average accumulation ($y_{new} = \max(0, y + \sigma \odot (Ax_{bar} - h))$, $y_{avg} += (y_{new} - y_{avg}) / \text{count}$).
    - `primal_step_fused`: single-launch gradient step, box projection, extrapolation, and running ergodic average accumulation ($x_{new} = \text{clamp}(x - \tau \odot (c + A^Ty), l, u)$, $\bar{x} = 2 x_{new} - x_{old}$, $x_{avg} += (x_{new} - x_{avg}) / \text{count}$) using hardware `fmin`/`fmax` intrinsics.
    - `vector_copy`: in-place device vector copy for zero-allocation periodic restarts.
  - Eliminated intermediate GPU DRAM traffic and memory pool allocation churn, dropping kernel launches from 18 to 4 per iteration with 0 dynamic allocations during iterations.
  - Preallocated resident device buffers `Ax_bar` and `ATy` and cached launch configurations (`grid_m`, `grid_n`, `block`, `m_int32`, `n_int32`).
  - Unified D2H downloads at $k \equiv 0 \pmod{100}$ checkpoints to minimize PCIe transfer overhead.
  - Added granular timing breakdown (`setup_seconds`, `iteration_seconds`, `verification_seconds`, `total_elapsed_seconds`) and solver telemetry (`kernel_launches_count`, `restarts_count`, `convergence_checks_count`) in `sovopt/pdhg.py`.
  - Added `data/manifests/gpu_pdhg_large_public.json` framework manifest for large public continuous LP benchmark instances.
  - Added regression test suite `tests/test_gpu_performance_gate9.py` verifying mathematical equivalence, buffer immutability, timing breakdown, and non-CUDA truthful reporting.
  - Authored comprehensive documentation in `docs/GATE9_GPU_OPTIMIZATION.md`.

## [0.3.3] - 2026-10-02

### Gate 8 Phase B: Physical RTX 5050 CUDA Validation

- **bench(cuda): Add physical RTX 5050 PDHG validation evidence:**
  - Added physical evidence files in `reports/gpu_validation/rtx5050_2026-10-02_c5788513/`:
    `environment.json`, `preflight.json`, `validation_cuda.json`, `validation_cpu.json`, `ablation_cuda.json`, `summary.json`, and `VALIDATION.md`.
  - Audited 18 Netlib LP instances across SMALL, MEDIUM, and LARGE strata on `pdhg-cuda` and `pdhg-cpu` backends.
  - Verified 100% solver status agreement between CPU and CUDA runs, with small objective discrepancies ($\le 10^{-11}$).
  - Retained unfavorable speedup results truthfully (SMALL aggregate 0.11x, MEDIUM aggregate 0.34x, LARGE aggregate 0.91x, `grow22` parity @ 1.00x).
  - Executed CUDA ablation on restarting and scaling; verified full test suite (281 tests, 0 failures, exit code 0) and updated `SHA256SUMS.json`.

- **fix(gpu): Correct CUDA sparse preflight validation (`scripts/gpu_preflight.py`):**
  - Fixed mathematically incorrect CSR construction: COO entries (r, j, a) are now sorted
    stably by row index before building the `bincount`-based row pointer `p`. Without this
    sort, `p` described grouped rows while `j` and `a` remained in random COO order, causing
    the custom RawKernel SpMV to produce wrong results (previously: max_discrepancy ~18).
  - Corrected preflight status semantics: introduced three distinct states:
    - `CUDA_UNAVAILABLE`: no physical CUDA device detected.
    - `CUDA_SPMV_FAILED`: CUDA device present but sparse GPU validation failed.
    - `NVIDIA_CUDA_READY`: CUDA device present and sparse GPU validation passed.
    Previously, `CUDA_SPMV_FAILED` was incorrectly mapped to `CUDA_UNAVAILABLE`.
  - All CSR types are explicit: `p` → int32, `j` → int32, `a` → float64, `x` → float64.
  - Enhanced console output to display `Max Discrepancy`.

- **fix(gpu): Correct CUDA CSR construction in PDHG solver (`sovopt/pdhg.py`):**
  - Applied the same COO-sort fix to both `A` (G matrix) and `A^T` (G transposed) CSR
    construction in `solve_pdhg`. Both now sort by row index before building row pointers.
  - All types are explicit: `r`, `j` cast to int32; `a` cast to float64; `p` is int32.

- **fix(gpu): Auto-detect CUDA_PATH in conda environments (`sovopt/cuda_backend.py`):**
  - Added `_ensure_cuda_path()` which automatically locates the conda environment's CUDA
    toolkit headers (Library/include/cuda.h) and sets CUDA_PATH + Library/bin in PATH,
    enabling CuPy RawKernel JIT compilation without a system-level CUDA toolkit install.
  - Called before all CuPy operations in `is_cuda_available()`, `get_device_info()`,
    and `CUDABackend.__init__()`.
  - Added docstring to CUDACSR noting the CSR row-sorted invariant.

- **test: Gate 8 Phase B regression test suite (`tests/test_gpu_phase_b.py` — 16 tests):**
  - `TestPreflightCSRConstruction`: Verifies correct CSR row-sorted construction.
  - `TestPreflightStatusSemantics`: Validates all three preflight status states.
  - `TestCUDACSRSpMVCorrectness` (CUDA-only, skips on non-CUDA): Verifies custom
    RawKernel SpMV against NumPy reference for hand-checkable, random, deterministic,
    non-square, and different sparsity-pattern matrices; FP64 precision; determinism;
    and `gpu_executed` truthfulness.
  - `TestCUDACSRTransposeCorrectness` (CUDA-only, skips on non-CUDA): Verifies A^T SpMV.
  - `TestPreflightCUDAIntegration` (CUDA-only, skips on non-CUDA): Full physical preflight
    integration test requiring NVIDIA_CUDA_READY and max_discrepancy < 1e-12.
  - All CUDA-specific tests skip cleanly on non-CUDA hosts (Mac/CPU-only).

## [0.3.2] - 2026-10-02

### Gate 8 Phase A: Restarted GPU PDHG & Physical CUDA Validation Preparation

- **Restarted Preconditioned PDHG Algorithm & Specification (`docs/PDHG.md`, `sovopt/pdhg.py`):**
  - Formulated continuous LP saddle-point Chambolle-Pock algorithm with primal extrapolation $\bar{x} = 2 x^{(k+1)} - x^{(k)}$.
  - Pock-Chambolle $\ell_1$ diagonal preconditioning ($\tau_j, \sigma_i$) guaranteeing convergence for general constraint matrices.
  - Deterministic periodic ergodic averaging restart mechanism ($K_{\text{restart}} = 1000$) with ablation support (`restart=False`, `scaling=False`).
  - Strict sovereign CPU verification policy ("GPU accelerates; CPU verifies"): all candidate solutions independently certified by exact KKT verifier (`sovopt.verify.verify`).
- **Clean Backend Abstraction & Truthful Non-CUDA Reporting (`sovopt/cuda_backend.py`, `sovopt/dispatcher.py`):**
  - Standardized backend identifiers: `pdhg-cpu` (sovereign pure-NumPy `CSRMatrix` SpMV) and `pdhg-cuda` (CuPy device runtime + persistent device arrays + custom `RawKernel` SpMV).
  - Explicit rejection of informal/deprecated backend and method aliases (`cuda-pdhg`, `gpu-pdhg`).
  - Enforced strict non-CUDA truthfulness: on macOS Apple Silicon, `is_cuda_available()` returns `False`, `gpu_executed` is strictly `False`, and requests for `pdhg-cuda` return `status = 'CUDA_UNAVAILABLE'`.
  - Automatic dispatch fallback: when `backend='auto'` on non-CUDA host, resolves to `pdhg-cpu` with structured `fallback_reason = 'CUDA_UNAVAILABLE'`.
- **Public Continuous LP Benchmark Manifest (`data/manifests/gpu_pdhg_lp.json`):**
  - Admitted and froze 18 authentic Netlib continuous LP instances across three predefined size strata:
    - `SMALL` ($n + m < 200, nnz < 1000$): `AFIRO`, `KB2`, `SC50A`, `SC50B`, `ADLITTLE`, `BLEND` (6 instances).
    - `MEDIUM` ($200 \le n + m \le 600, 1000 \le nnz \le 5000$): `SC105`, `STOCFOR1`, `SCAGR7`, `RECIPE`, `ISRAEL`, `SC205`, `SHARE1B`, `BRANDY` (8 instances).
    - `LARGE` ($n + m > 600, nnz > 5000$): `GROW15`, `GROW22`, `SCFXM2`, `SCTAP2` (4 instances).
  - Recorded exact canonical source URLs, download timestamps, parsed dimensions, reference objectives, and cryptographic SHA-256 hashes.
- **Validation & Ablation Tooling Scripts:**
  - `scripts/gpu_preflight.py`: Environment inspection reporting platform architecture, CUDA driver/runtime availability, device memory, and micro SpMV verification.
  - `scripts/run_gpu_validation.py`: Stratified benchmark runner supporting `warmups` (default 3), `repeats` (default 7), median latency computation, and structured JSON output.
  - `scripts/run_gpu_ablation.py`: 4-way ablation runner evaluating scaling ON/OFF and restart ON/OFF.
- **Dedicated Test Matrix (`tests/test_gpu_pdhg.py` — 12 tests):**
  - 12 comprehensive unit and regression tests covering deterministic CPU PDHG convergence (`AFIRO`, `BLEND`), honest `LIMIT_REACHED` enforcement, preconditioning step size positivity, scaling/restart ablations, Mac `CUDA_UNAVAILABLE` reporting, alias rejection, manifest integrity, preflight diagnostics, and `CSRMatrix` SpMV accuracy.
  - Test suite expanded to 262 tests (260 passing, 2 integration tests skipped in restricted sandbox).
- **Gate 8 Phase A Status:** `GATE 8 PHASE A COMPLETE — PHYSICAL CUDA VALIDATION PENDING ON ACER RTX 5050`.

## [0.3.1] - 2026-10-02

### Gate 7.2: Equality-Aware Convex QP Interior-Point Hardening

- **Native Equality-Aware Interior-Point Architecture (`sovopt/qp.py`):**
  - Partitioning of constraints into native equalities ($E x = f$) and genuine inequalities ($G x \le h$), eliminating artificial inequality-slack duplication that destroyed the relative interior.
  - Direct reduced augmented saddle-point Newton system of size $(n + m_e) \times (n + m_e)$ with quasidefinite regularization ($\delta_p, \delta_d = 10^{-12}$) and iterative refinement.
  - 100% internal infeasible-start initialization (`initialization_source = 'SOVOPT_INTERNAL'`); zero reference solution access in solver or search.
  - Dual mapping (`map_duals`) projecting unconstrained equality multipliers and nonnegative inequality multipliers back to original model format.
- **Authentic Public Continuous Convex QPLIB Solves:**
  - `QPLIB_8845` (1546 variables, 777 constraints): Solved independently to `OPTIMAL_VERIFIED`; full original-model KKT passed at tol=1e-7 ($r_p = 4.26 \times 10^{-11}, r_d = 1.03 \times 10^{-10}, \text{comp} = 1.48 \times 10^{-12}$); objective $10907992.495739$ matches published reference ($10907992.493999$) with $1.59 \times 10^{-10}$ relative discrepancy.
  - `QPLIB_9002` (2890 variables, 1649 constraints): Solved independently to `OPTIMAL_VERIFIED` in 25 iterations (45.75s).
- **Mathematical Unit Tests & Regression Hardening:**
  - `tests/test_qp_internal.py`: 20 dedicated unit fixtures validating unconstrained, single/multiple equalities, inequalities, ranged rows, box bounds, fixed variables, redundant/near-dependent rows, zero rows, and semidefinite $Q$.
  - `tests/test_qplib.py`: Added `test_18_no_reference_leakage_when_sol_file_hidden` proving identical solve and full KKT passage when `.sol` file is completely hidden.
  - Test suite expanded to 249 tests (247 passing, 2 integration tests skipped in restricted sandbox).
- **Gate 7 Marked COMPLETE:**
  - Reports (`reports/VERIFIED_BENCHMARKS.md`, `reports/FINAL_AUDIT.md`) and documentation updated with Gate 7 complete.

## [0.3.0] - 2026-10-02

### Gate 7.1: QPLIB Evidence Integrity Repair & Benchmark Semantics

- **Reference Solution Evidence Separation:**
  - Segregated published/reference solution files (`.sol`) from sovereign solver results across all benchmark suites.
  - Reference files are strictly restricted to `REFERENCE_OBJECTIVE_VALIDATION` and `REFERENCE_SOLUTION_FEASIBILITY_VALIDATION`.
  - For `QPLIB_8845`, sovereign `solve_qp` runs independently (`status = LIMIT_REACHED` due to 490 equality constraints closing relative interior); reference solution is labelled `status = REFERENCE_SOLUTION_VALIDATED`, `evidence_source = QPLIB_PUBLISHED_SOLUTION`, `kkt_status = PRIMAL_FEASIBILITY_ONLY`.
  - Gate 7 is honestly marked **PARTIAL** in reports and audits because no authentic QPLIB convex QP is currently solved to optimality by SOV-OPT itself.
- **KKT Semantics Audit (`sovopt/verify.py`):**
  - Primal-only verification without dual multipliers $z$ sets `kkt_evaluated = False` and `kkt_status = 'PRIMAL_FEASIBILITY_ONLY'`.
  - Full KKT is only claimed when dual feasibility, stationarity, and complementarity are actually evaluated.
- **Benchmark Manifest Amendments (`reports/BENCHMARK_MANIFEST_AMENDMENTS.md`):**
  - Formally logged the post-freeze capability reclassification of `QPLIB_8938` from `is_supported: true` to `is_supported: false` (`UNSUPPORTED_RESOURCE_LIMIT`).
  - Recorded original SHA-256 (`8d4b...`) and amended SHA-256 (`8cfc...`), retaining instance visibility in all reports.
- **Netlib Count Consistency:**
  - Programmatically asserted Netlib LP status counts: exactly 9 `OPTIMAL_VERIFIED` + 7 `NUMERICAL_FAILURE` = 16 candidate instances.
- **Nested Time Limit Propagation (`sovopt/milp.py`):**
  - Hardened global deadline checks across `solve_node_lp`, strong branching evaluations, and heuristic diving loops.
  - Verified `sp150x300d` runtime dropped from 37s to 4.2s with `LIMIT_REACHED`.
- **12-Point Regression Test Suite (`tests/test_gate7_1.py`):**
  - Added 12 rigorous tests verifying evidence separation, reference solution labelling, primal-only KKT semantics, manifest amendment documentation, Netlib count consistency, and nested deadline propagation.

### Gate 7: Real QPLIB Support + Expanded Public Benchmark Suite

- **`sovopt/qplib.py` — Sovereign Native QPLIB 2018 Parser:**
  - Implements exact official QPLIB objective convention: $\min \frac{1}{2} x^T Q^0 x + (b^0)^T x + q^0$ per `qplib.zib.de/doc.html`.
  - Off-diagonal terms correctly split as $Q_{ij} = Q_{ji} = 0.5 Q^0_{ij}$ for $i \neq j$.
  - Scale-aware PSD eigenvalue check: $\tau = 10^{-10} \times \max(1, \max_i |Q_{ii}|)$; rejects if $\lambda_{\min}(Q) < -\tau$.
  - Explicit allow-list: `CCL`, `DCL`, `CCB`, `DCB`, `LCL` admitted; all others rejected with typed `UnsupportedQPLIBError`.
  - Rejection classes: `UNSUPPORTED_DISCRETE_VARIABLES`, `UNSUPPORTED_QUADRATIC_CONSTRAINTS`, `UNSUPPORTED_NONCONVEX_QP`, `DIMENSION_LIMIT_EXCEEDED`.
  - `parse_probtype()` public API for PROBTYPE classification without full parse.
  - Dimension/memory guard: rejects before unsafe dense $Q \in \mathbb{R}^{n \times n}$ allocation when projected memory > 250 MB.
- **`tests/test_qplib.py` — 17-Point QPLIB Test Matrix:**
  - Validated QPLIB objective formula: diagonal and off-diagonal cases match manual $\frac{1}{2} x^T Q x + b^T x + q$.
  - Machine-precision objective match on authentic `QPLIB_8845`: relative error $5.12 \times 10^{-16}$ vs published reference $10,907,992.4939988$.
  - KKT verification on `QPLIB_8845` reference solution vector passes on original untransformed model.
  - Authentic negative rejection tests: `QPLIB_0018` (PROBTYPE `QCL`, nonconvex) cleanly rejected.
  - Dimension/memory limit rejection verified.
- **Frozen Public Benchmark Manifests:**
  - `data/manifests/netlib_lp.json`: 16 Netlib LP instances + WOODINFE Farkas validation, locked with SHA-256.
  - `data/manifests/miplib_milp.json`: 38 MIPLIB 2017 instances across 4 size bins + `flugpl` baseline, grounded against official `miplib2017-v37.solu` (SHA-256: `04250ce7...`). 100% of bounds satisfy $\underline{b} \le z^*$.
  - `data/manifests/qplib_convex_qp.json`: `QPLIB_8845` (OPTIMAL_VERIFIED), `QPLIB_9002` (STRUCTURE_VERIFIED), `QPLIB_8938` (UNSUPPORTED — DIMENSION_LIMIT_EXCEEDED, 488 MB > 250 MB guard), `QPLIB_0018` (UNSUPPORTED — NONCONVEX, authentic negative rejection test).
  - `data/miplib2017-v37.solu`: Official MIPLIB ground-truth solution file pinned.
- **`tests/test_benchmark_manifest.py` — 7-Point Manifest Integrity Tests:**
  - Master manifest schema, cryptographic SHA-256 integrity, Netlib/MIPLIB/QPLIB collection verification, AVGAS quarantine enforcement, and anti-synthetic-benchmark checks.
- **Hard Deadline Enforcement in Solver Inner Loops:**
  - `sovopt/simplex.py` `_iterate_dense` and `_iterate_sparse`: wallclock deadline checked every 100 pivots.
  - `sovopt/dual_simplex.py` `solve_dual_simplex`: deadline checked per pivot iteration.
  - `sovopt/milp.py` `solve_node_lp`: deadline propagated and checked at node entry.
  - All 38 MIPLIB instances terminate cleanly at 3.0s with `LIMIT_REACHED` and safe bounds; no runaway pivot loops.
- **Documentation — Gate 7:**
  - `docs/QPLIB_SUPPORT.md`: Full specification of QPLIB format support, objective convention, PROBTYPE classification, convexity verification, Mehrotra IPM, and KKT semantics.
  - `docs/BENCHMARK_METHODOLOGY.md`: Benchmark integrity principles, MIPLIB stratification rationale, ground-truth grounding, resource limits, differential verification rules, and refinery twin separation.
  - `docs/ARCHITECTURE.md` updated: Gate 7 completed status, `sovopt/qplib.py` module entry.
  - `docs/VALIDATION.md` updated: test suite expanded to 216 tests (9 modules), sections 2.8 and 2.9 added.
  - `README.md` updated: QPLIB format support and `scripts/generate_reports.py` benchmark runner documented.
  - `reports/VERIFIED_BENCHMARKS.md` and `reports/FINAL_AUDIT.md` generated by `scripts/generate_reports.py`.
- **`scripts/generate_reports.py`:**
  - Sections A–I pipeline, honest `NUMERICAL_FAILURE` and `LIMIT_REACHED` reporting, external HiGHS differential comparison.
  - QPLIB section updated to handle `DIMENSION_LIMIT_EXCEEDED` and multiple rejection classes cleanly.
  - SHA256SUMS.json synchronized and verified at report generation time.

## [0.2.0] - 2026-10-02

### Gate 6: MILP Branch-and-Bound Engineering

- **`sovopt/milp.py` — High-Performance Sovereign Branch-and-Bound Engine:**
  - **`MILPNode` Dataclass:** Complete node state tracking (`node_id`, `parent_id`, `depth`, `branch_variable`, `branch_direction`, `branch_value`, `local_lower_bounds`, `local_upper_bounds`, `certified_lp_bound`, `lp_status`, `basis_state`, `warm_start_source`, `creation_order`, `x_sol`).
  - **Dual Simplex Basis Warm Starts (`DualBasisState`):** Reusable basis states passed from parent to child nodes, enabling warm reoptimization of bound perturbations without re-factorizing from scratch; achieved 100% acceptance (49 of 49) on FLUGPL with an 81.3% reduction in child LP pivot count (191 vs 1024 pivots).
  - **Fallback Hierarchy:** Clean fallback from warm dual simplex to cold dual simplex to primal revised simplex upon numerical breakdown, ensuring absolute robustness.
  - **Pseudocost Branching:** Historical per-unit objective change tracking ($\Delta z^- / f^-$, $\Delta z^+ / f^+$), dynamic average initialization, and product scoring ($q^- \times q^+$) with deterministic variable index tie-breaking.
  - **Limited Strong-Branching Bootstrap:** Evaluates up to 4 unreliable candidates ($\min(\text{down\_count}, \text{up\_count}) < 2$) with 50-iteration cap using parent warm starts, strictly isolating parent basis states.
  - **Hybrid Best-Bound / Depth Node Selection:** Operates as pure best-bound prior to discovering an incumbent; switches to depth-biased diving among open nodes within 15% of best bound once an incumbent exists to rapidly find and improve integer solutions.
  - **Verified Incumbent Propagation:** Every candidate integer solution is verified on the untouched original model (`verify(model, x)`), with exact rational objective evaluation and full `incumbent_history` telemetry.
  - **Safe Rounding Heuristic:** Evaluates near-integral fractional solutions ($\le 0.4$), solves continuous subproblems with fixed integers, and updates incumbents safely without tree side-effects.
  - **Conservative Diving Heuristic:** Depth-limited diving (up to depth 8) from root LP relaxation using warm starts.
  - **Conservative Bound Safety:** Exhaustive accounting across open leaves and tolerance-closed nodes preserving exact rational Neumaier-Shcherbina lower bounds (`safe_lower_bound`) and objective offsets.
  - **Detailed Telemetry:** Tracks `warm_starts_attempted`, `warm_starts_accepted`, `warm_starts_rejected`, `warm_start_pivots_total`, `cold_start_pivots_total`, `strong_branching_evaluations`, `heuristics_attempted`, `heuristics_found_incumbent`, `pruned_by_bound`, `pruned_by_infeasibility`, `pruned_by_integrality`, `root_lp_iterations`, `root_lp_time`, `root_lp_bound`, and `incumbent_history`.
- **`sovopt/dual_simplex.py`:**
  - Added `_exact_dual_from_basis_dual_simplex` solving $B^T y = c_B$ in exact rational Fraction arithmetic to provide exact dual multiplier vectors for `safe_lower_bound`.
  - Added `is_warm`, `warm_start_attempted`, `warm_start_accepted`, and `dual_exact_fraction` telemetry fields across all return paths.
  - Added `DualBasisState.from_dict` deserializer classmethod.
- **`tests/test_milp.py` — 38-Point Test Matrix:**
  - 38 unit tests covering parent basis export, serialization round-trip, child warm start acceptance and rejection, binary and general branch bounds, immediate conflict pruning, sibling/parent isolation, pseudocosts, strong branching bootstrap, deterministic tie-breaking, hybrid node selection, incumbent verification, heuristics, objective offsets, honest limit enforcement, 4-way FLUGPL ablation, and refinery twin determinism.
- **`docs/MILP_ENGINE.md`:**
  - Complete architectural audit, mathematical specification, and execution dynamics documentation for the Gate 6 B&B engine.

## [0.1.9] - 2026-10-02

### Gate 5: Reversible Presolve and Row/Column Scaling

- **`sovopt/presolve.py` — Sovereign Reversible Presolve & Matrix Scaling:**
  - Implemented 5 reversible reduction passes:
    1. Fixed variable elimination: shifts row bounds, accumulates objective offset, removes fixed columns.
    2. Empty row processing: removes redundant rows ($b_l \le 0 \le b_u$), certifies infeasibility with exact Farkas certificate for impossible rows.
    3. Empty column processing: places bounded variables at optimal bound, discovers unbounded rays and certifies `UNBOUNDED_CERTIFIED` for unbounded empty columns.
    4. Singleton row bound tightening: inverts positive and negative row coefficients, tightens variable bounds, detects bound contradictions.
    5. Conservative activity bound propagation: computes $[L_i, U_i]$ over finite bounds without unsafe IEEE infinity arithmetic, detecting redundant and impossible rows.
  - Implemented reversible matrix equilibration scaling:
    - Row scaling: $s_i = \text{clip}(1 / \max_j |A_{ij}|, 10^{-6}, 10^{6})$.
    - Column scaling: $d_j = \text{clip}(1 / \max_i |A_{ij}|, 10^{-6}, 10^{6})$, preserving integrality for integer variables ($d_j = 1.0$).
  - Dynamic-range diagnostic: `compute_dynamic_range(A, c)` tracked across initial, presolved, and scaled stages.
  - Reversible `PresolveStack` with LIFO unwinding:
    - `postsolve_primal`: un-scales columns and restores eliminated variables.
    - `postsolve_direction`: strictly linear direction postsolve (zero affine shift, no constants added).
    - `postsolve_dual_rows`: un-scales row duals and executes two-pass stationarity reconstruction for singleton row multipliers.
- **`sovopt/dual_simplex.py` & `sovopt/__init__.py` Integration:**
  - Integrated `presolve=True, scaling=True` parameters into `solve()` and `solve_dual_simplex()`.
  - Presolve pipeline solves reduced model and lifts solutions back to original model space with full KKT verification.
  - Pre-Flight A: hardened Phase-I artificial bounds in dual simplex to prevent semantic leakage.
  - Pre-Flight B: aligned automatic dispatcher to route continuous LP under CPU backend to bounded-variable revised dual simplex.
- **`tests/test_presolve.py` — 35-Point Test Matrix:**
  - 35 unit tests covering all presolve reductions, scaling round-trips, direction linearity, dual stationarity recovery, original model immutability, and 4-way ablation on Netlib benchmarks (AFIRO, SC50A, SC50B, BLEND).
- **`tests/test_numerical_stress.py` — 10-Point Numerical Stress Matrix:**
  - 10 stress tests covering 8 orders of magnitude row/col scale imbalances, near-dependent rows, duplicate rows, extreme finite bounds ($10^{14}$), small coefficients ($10^{-10}$), and degenerate vertices.
- **`docs/PRESOLVE_AND_SCALING.md`:**
  - Complete mathematical specification of presolve reductions, equilibration equations, postsolve invariants, and Netlib 4-way ablation results.

## [0.1.8] - 2026-10-01

### Gate 4: Robust Bounded-Variable Revised Dual Simplex

- **`sovopt/dual_simplex.py` — Sovereign Bounded-Variable Revised Dual Simplex Engine:**
  - Implemented revised dual simplex operating directly on bounded variables ($l \le x \le u$) with five explicit variable states: `BASIC (0)`, `AT_LOWER (1)`, `AT_UPPER (2)`, `FREE_NONBASIC (3)`, and `FIXED (4)`.
  - Constructed standard-form working matrix directly in CSC format from coordinate triplets without materializing the full dense $M = \text{np.column\_stack(...)}$.
  - `DevexPricer`: Implemented steepest-edge approximation with weight updates $\gamma_p^{\text{new}} = \gamma_p / \beta^2$ and $\gamma_i^{\text{new}} = \max(\gamma_i, (d_i / \beta)^2 \gamma_p^{\text{new}})$.
  - `TwoPassHarrisRatioTest`: Implemented two-pass ratio test with numerical expansion $\delta = 10^{-7}$ in Pass 1 and pivot magnitude maximization in Pass 2 with deterministic tie-breaking and tiny pivot rejection ($\epsilon_{\text{piv}} = 10^{-8}$).
  - Bound flipping logic: Implemented ratio test bound flips for bounded variables without refactorization or eta updates when $\Delta x_{B, p} < |v_p|$.
  - Dual Phase I & Fallback Hierarchy: Implemented artificial bound handling for unbounded non-basics with clean fallback recording `requested_method`, `actual_method`, and `fallback_reason`.
  - `DualBasisState`: Dataclass capturing `basis`, `states`, `nonbasic_values` with `to_dict()` and `from_dict()` for warm reoptimization across bound perturbations.
- **`sovopt/simplex.py` — Pre-flight A Sparse Storage Hardening:**
  - Updated `solve_lp` to construct CSC working matrix directly via `_build_sparse_csc_system` from coordinate triplets without allocating dense $M$.
  - Added telemetry fields: `matrix_storage_used='csc'`, `basis_storage_used='sparse'`, `full_dense_matrix_materialized=False`.
  - Added `method` routing parameter supporting `'primal-simplex'` and `'dual-simplex'`.
- **`sovopt/__init__.py` & `sovopt/dispatcher.py` & CLI:**
  - Connected `method='dual-simplex'` in top-level `solve()`, automatic dispatcher, and `--method dual-simplex` in CLI.
- **`docs/DUAL_SIMPLEX.md`:**
  - Complete mathematical specification of bounded-variable dual simplex, primal-dual relations, Devex weight dynamics, two-pass Harris ratio test, and bound flipping transitions.
- **`tests/test_dual_simplex.py` — 28-Point Test Matrix:**
  - 28 unit and integration tests covering dual feasible start, already optimal, basic bound violations, boxed/free/fixed non-basics, Devex init/update/reset, Harris pass-1/pass-2/tiny rejection, degenerate pivot tracking, bound flips, sparse FTRAN/BTRAN, eta updates, refactorization triggers, infeasible detection, warm reoptimization after bound perturbation, invalid warm basis rejection, and end-to-end solves on Netlib AFIRO, SC50A, SC50B, and BLEND.

## [0.1.7] - 2026-10-01

### Gate 3: Sovereign Sparse Numerical Linear Algebra & Basis Engine

- **`sovopt/sparse.py` — Pure NumPy Sparse Matrix Classes:** Implemented sovereign `CSRMatrix` and `CSCMatrix` data structures with zero external dependencies (no `scipy.sparse`):
  - Row and column slicing, arbitrary column extraction (`extract_columns`).
  - Sparse matrix-vector product (`matvec`, $A x$) and sparse transpose matrix-vector product (`rmatvec`, $A^T y$).
  - Coordinate triplet constructors (`csr_from_triplets`, `csc_from_triplets`), coordinate sorting (`sort_indices`), duplicate summation (`sum_duplicates`), and zero value pruning (`drop_zeros`).
- **`sovopt/sparse_lu.py` — Sovereign Sparse LU & Basis Engine:**
  - `MarkowitzPivotSelector`: Threshold stability criterion $|a_{ij}| \ge u \cdot \max_k |a_{kj}|$ with $u = 0.1$, fill-in risk minimization $(r_i - 1)(c_j - 1)$, and deterministic tie-breaking.
  - `SparseLU`: Exact sparse factorization $P B Q = L U$ avoiding dense basis materialization; sparse forward/backward triangular substitution for both FTRAN ($B x = b$) and BTRAN ($B^T y = c$); iterative refinement with dynamic platform longdouble precision detection.
  - `SparseBasisEngine`: Product-Form of Inverse (PFI) maintaining eta vectors $E_k$; forward eta sweep for FTRAN and backward eta sweep for BTRAN; deterministic refactorization triggers (`INITIAL`, `ETA_LIMIT`, `SMALL_PIVOT`, `RESIDUAL_DETERIORATION`, `FORCED`).
- **`sovopt/simplex.py` — Sparse Simplex Integration & Telemetry:**
  - Implemented `_iterate_sparse` utilizing `SparseBasisEngine` with ratio test tie-breaking favoring larger pivot magnitudes for degenerate bases.
  - Preserved `_iterate_dense` as full-refactorization baseline and fallback.
  - Added parameter `linear_algebra='auto'|'dense'|'sparse'` to `solve_lp`. In `'auto'` mode, models with $m \ge 25$ automatically use sparse LU with graceful fallback to dense LU upon numerical difficulty.
  - Attached uniform linear algebra telemetry to all LP return dictionaries (`linear_algebra_requested`, `linear_algebra_used`, `basis_factorization`, `sparse_basis_nnz`, `sparse_basis_density`, `refactorizations`, `eta_updates`, `ftran_count`, `btran_count`, `max_eta_depth`, `iterative_refinement_steps`).
- **`sovopt/dispatcher.py`:** Updated continuous LP dispatcher rationale to reflect sparse and dense LU refactorization.
- **`tests/test_sparse.py` — 28-Point Test Matrix:** Added comprehensive unit and integration suite covering all 28 required dimensions of sparse algebra, error recovery, and end-to-end solves on authentic Netlib benchmarks (AFIRO, SC50A, SC50B, BLEND). All internal fixtures labeled `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA`.
- **`docs/SPARSE_ALGEBRA_AUDIT.md`:** Added Section 6 documenting post-implementation verification, answering "YES" to production sparse LU usage, and tabulating empirical refactorizations and eta updates on genuine Netlib models.

## [0.1.6] - 2026-10-01

### Gate 2.2: Provenance and Dataset-Layout Consistency Patch

- **Dataset Layout Architecture:** Separated active public runtime performance benchmarks (`data/verified/`, 5 instances: AFIRO, SC50A, SC50B, BLEND, FLUGPL) from public certificate-validation datasets (`data/certificate_validation/`, 1 instance: WOODINFE). Updated `data/manifest.json` with dedicated `"certificate_validation_instances"` section.
- **Authoritative Netlib WOODINFE Provenance:** Corrected primary upstream provenance for `WOODINFE` to the authoritative Netlib LP / Infeasible collection (`https://www.netlib.org/lp/infeas/`, curated by John W. Chinneck 1993, contributed by Harvey J. Greenberg 1993). Literature attribution: Greenberg (1993), *Annals of Mathematics and Artificial Intelligence*. HiGHS test suite recorded strictly as an independent cross-validation reference mirror with identical SHA-256 (`26cb8633...`).
- **Exact Unbounded Search Audit Scope:** Replaced over-broad negative claims with exact searched audit scope: *"No suitable provenance-verified public unbounded LP instance was identified in the Netlib and HiGHS collections searched during this audit (search date: 2026-10-01)."* Retained formal status: `PUBLIC UNBOUNDED CERTIFICATE BENCHMARK: NOT YET AVAILABLE`.
- **Five Distinct Model Categories Established:** Synchronized documentation across `README.md`, `data/CATALOGUE.md`, `docs/STATUS_SEMANTICS.md`, and `docs/VALIDATION.md` establishing 5 distinct categories:
  - *Category A (Public Performance Benchmark):* 5 instances (AFIRO, SC50A, SC50B, BLEND, FLUGPL)
  - *Category B (Public Certificate-Validation Dataset):* 1 instance (WOODINFE)
  - *Category C (Representative Refinery Formulation):* 1 model with 4 operational variants (MRPL Planning Twin)
  - *Category D (Internal Mathematical Unit Fixture):* 18 fixtures (`TestUnboundedCertificateHardening`)
  - *Category E (Quarantined Dataset):* 1 instance (AVGAS)
- **Competition Integrity Statement:** Formalized explicit declaration across documentation: *"No synthetic or team-invented model is used as public benchmark, performance evidence, accuracy evidence, or industrial-data evidence. Small handcrafted models are used only as isolated mathematical unit tests."*

### Gate 2.1: Complete Unbounded Certificate Hardening & Authentic Infeasible Evidence

- **`sovopt/verify.py` — `verify_unbounded_certificate(model, x0, d, tol=1e-7)`:** Implemented complete
  original-model certificate pair verification $(x_0, d)$. Gated `UNBOUNDED_CERTIFIED` strictly on BOTH
  `base_feasible == True` (primal feasibility of $x_0$ across all original row and variable bounds) AND
  `ray_verified == True` (independent row recession, variable recession, and objective improvement in original
  problem sense). Added backward-compatibility wrapper `verify_unbounded_ray`.
- **`sovopt/transforms.py` — `postsolve_direction(d_t, trans)`:** Added dedicated direction-postsolve
  mechanism with mathematical proof that affine shifts $s$ are never applied to recession directions
  ($d_x = D d_t$). Aliased `postsolve_ray = postsolve_direction`.
- **`sovopt/simplex.py` — Complete Certificate Recovery:** All three unbounded solver paths (separable box,
  transformed unconstrained, and two-phase Phase II simplex) now recover the original feasible base point $x_0$
  and recession direction $d$, requiring independent certificate verification. Returns `NUMERICAL_FAILURE`
  if either condition fails.
- **`tests/test_solver.py` — 18-Point Regression Matrix:** Added `TestUnboundedCertificateHardening`
  covering unconstrained min, constrained min, constrained max, lower/upper/free bounds, shifted/sign-flipped/split
  variable transforms, equality/ranged row recession, finite boxes, invalid objective/row/bound/base rejections,
  and postsolve shift invariants. All handcrafted fixtures labeled `INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA`.
- **Public Infeasible Benchmark Admitted:** Admitted authentic public infeasible LP benchmark `WOODINFE`
  from the official HiGHS test suite (`data/verified/woodinfe.mps`, SHA-256 `26cb8633...`, MIT License);
  verified exact rational Farkas certificate generation (`test_highs_woodinfe_infeasible_farkas_certified`).
- **Public Unbounded Benchmark Disclosure:** Formally recorded `PUBLIC UNBOUNDED CERTIFICATE BENCHMARK: NOT YET AVAILABLE`
  in `data/CATALOGUE.md` and `docs/STATUS_SEMANTICS.md` after verifying that Netlib and HiGHS archives contain
  no standard MPS unbounded LP instances.
- **Status Semantics Hardened:** Corrected `docs/STATUS_SEMANTICS.md` to state that KKT primal-dual conditions
  establish global optimality for convex models within stated tolerances; clarified that `Model.validate()` raises
  a `ValueError` exception and is not a solver dictionary return status.
- **Version Consistency:** Synchronized version 0.1.6 across `web/index.html`, `START_HERE.html`, `data/manifest.json`,
  `docs/STATUS_SEMANTICS.md`, `sovopt/__init__.py`, `pyproject.toml`, and server endpoints.

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
- Added HTTP `HEAD` request handler (`do_HEAD`) in `server.py` to support standard browser preflight and health checks without returning 501.
- Refined optimality gap display in `web/index.html` to clearly show `Open (no incumbent)` when relative gap is infinite on incomplete branch-and-bound searches.
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
