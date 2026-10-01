# Reproducible Validation and Evidence — SOV-OPT

This document records the exact procedures for reproducing all numerical benchmarks, unit tests, differential comparisons against external reference solvers, and honest disclosures of current coverage gaps.

---

## 1. Quick Verification Commands

All commands below assume execution from the project root with the project-local virtual environment active:

```bash
# 1. Run full unit and regression test suite (18 tests: 16 passing, 2 integration tests skipped in restricted sandbox)
.venv/bin/python -m unittest discover -s tests -v

# 2. Run automated report and benchmark generator
.venv/bin/python scripts/generate_reports.py

# 3. Run with external HiGHS differential validation (requires benchmark environment)
SOVOPT_BENCHMARK_PYTHON=.venv-benchmark/bin/python .venv/bin/python scripts/generate_reports.py

# 4. Launch local dashboard
.venv/bin/python server.py --port 8000
```

---

## 2. Test Suite Organization

The active test suite is split into two modules:

### 2.1 Solver Correctness (\`tests/test_solver.py\`)
1. **\`test_lu_pivot_refinement_real_basis\`**: Evaluates dense LU factorization residuals ($\le 10^{-10}$) on actual basis matrices from Netlib LP instances (AFIRO, SC50A, BLEND).
2. **\`test_verified_real_instances\`**: Validates end-to-end revised simplex solutions and KKT conditions against published Netlib MINOS 5.3 reference values for AFIRO, SC50A, SC50B, and BLEND.
3. **\`test_milib_flugpl_solve_and_lower_bound\`**: Solves MIPLIB FLUGPL to node limit (50 nodes); verifies the conservative rational lower bound is $\ge 769500.0$ and $\le 1201500.0$.
4. **\`test_infeasible_farkas_certificate_genuine\`**: Tests exact rational Farkas certificate generation and lossless JSON round-trip on a genuine infeasible branch node of FLUGPL.
5. **\`test_bad_candidate_validation\`**: Challenges the independent verifier (\`sovopt/verify.py\`) with intentionally corrupted and non-feasible vectors on Netlib AFIRO to ensure invalid candidates are strictly rejected.
6. **\`test_variable_transformations_equiv\`**: Applies an invertible affine transformation ($x = D \tilde{x} + s$) to Netlib AFIRO; confirms postsolve recovers original primal and dual solutions matching KKT conditions to machine precision ($10^{-12}$).
7. **\`test_pdhg_cpu_convergence\`**: Verifies first-order Primal-Dual Hybrid Gradient convergence on Netlib AFIRO to $-464.75314$ within tolerance.
8. **\`test_limits_honest_enforcement\`**: Validates that node limits (0 nodes) and iteration limits (1 iteration) trigger honest \`LIMIT_REACHED\` status without fabricating an incumbent.
9. **\`test_exact_rational_lagrangian_bound\`**: Verifies that exact rational basis duals construct a provably valid lower bound on the FLUGPL LP relaxation node.
10. **\`test_flugpl_honest_metadata\`**: Enforces mathematical invariants on the FLUGPL branch-and-bound search: valid finite lower bound, strictly respected node budget, and required incumbent feasibility if an incumbent is found.

### 2.2 Server and Dashboard API (\`tests/test_server.py\`)
- **\`HandlerUnitTests\`**: Direct in-process testing of the HTTP request handler:
  - \`test_get_health\`: Validates 200 response and version string.
  - \`test_get_root_page\`: Validates dashboard HTML serving.
  - \`test_get_manifest\`: Validates dataset manifest serving.
  - \`test_get_examples\`: Confirms examples list contains only verified instances.
  - \`test_post_solve_afiro\`: End-to-end solve request; checks \`model_name\`, \`backend\`, and \`OPTIMAL_VERIFIED\` status.
  - \`test_post_solve_invalid_payload\`: Confirms 400 error on malformed input.
- **\`ServerIntegrationTests\`**: Socket-based integration tests connecting over loopback network. (Automatically skipped when loopback sockets are restricted by sandbox policy).

---

## 3. External Differential Validation Setup

External differential validation compares SOV-OPT against native HiGHS (C++) running in an isolated subprocess. External solvers are **never imported** by the core solver (\`sovopt/\`) or server.

### Creating the Benchmark Environment
Run the setup script:
```bash
bash scripts/create_benchmark_env.sh .venv-benchmark
```
This script creates an isolated virtual environment containing \`highspy\` (1.15.1) and \`scipy\` (1.17.1).

### Running Differential Validation
```bash
SOVOPT_BENCHMARK_PYTHON=.venv-benchmark/bin/python .venv/bin/python scripts/generate_reports.py
```
This script invokes \`scripts/baseline_worker.py\` in a separate subprocess for each active instance and records:
- Executed command and exit code.
- Dynamic solver version (\`1.15.1\`).
- Parsed model dimensions, objective sense, and integer variables.
- Status, objective, solution availability, and best bounds.
- Comparison status (\`MATCH\` or \`BOUND_ONLY\`) and objective discrepancy vs SOV-OPT.

Output is written to \`reports/external_validation.json\` and summarized in \`reports/VERIFIED_BENCHMARKS.md\`.

---

## 4. Current Evidence Locations

- **Automated Benchmark Report:** \`reports/VERIFIED_BENCHMARKS.md\`
- **External Validation JSON:** \`reports/external_validation.json\`
- **Local Solve Records (timestamped):** \`reports/local_validation/2026-10-01_verified/\`
  - \`afiro.json\`, \`sc50a.json\`, \`sc50b.json\`, \`blend.json\`, \`flugpl.json\`, \`afiro_pdhg.json\`, \`summary.json\`
- **Verified Dataset Files:** \`data/verified/\` (MPS and normalized JSON)
- **Dataset Provenance and Metadata:** \`data/CATALOGUE.md\` and \`data/manifest.json\`
- **Quarantined Datasets:** \`data/quarantined/\`

---

## 5. Coverage Gaps & Honest Disclosures

1. **MILP \`OPTIMAL_VERIFIED\` Coverage Gap:**
   - There is currently no admitted genuine MILP instance in the verified suite that solves to full tree closure (\`OPTIMAL_VERIFIED\`) within practical automated test time limits on this machine.
   - MIPLIB \`FLUGPL\` reaches \`LIMIT_REACHED\` at 50 nodes, advancing the conservative lower bound to approximately \`1173644.9999999998\` (optimal is 1201500).
   - The optimality basis language regression is verified by code inspection and invariant checks; no synthetic MILP model has been constructed to manufacture a false green badge.

2. **Proprietary MRPL Refinery Data (Empty State):**
   - No authorized MRPL refinery dataset is available in this project.
   - Fictional refinery numbers are prohibited. Netlib refinery LP \`BLEND\` is provided as an authentic blending problem.

3. **Industrial Convex QP Data (Empty State):**
   - No authentic public industrial convex QP benchmark is currently admitted. Synthetic toy models have been removed.
   - Convex QP solving is validated via continuous KKT conditions on positive semi-definite matrices.

4. **AVGAS Historical Provenance (Quarantined):**
   - \`avgas.mps\` is sourced from the HiGHS repository (SHA-256 verified).
   - Its historical attribution to Charnes, Cooper, Mellon (1952) and Symonds (1955) has not been verified against primary literature. It is quarantined outside active runtime paths.

5. **CUDA Acceleration (Hardware Unavailable):**
   - Development is performed on Apple Silicon ARM64, which lacks NVIDIA CUDA hardware.
   - \`gpu_executed\` is strictly \`false\` on all local runs. CUDA kernels in \`sovopt/pdhg.py\` remain unvalidated until tested on a physical NVIDIA device.

---

## 6. Baseline History Summary (Gate 0)

At the initial Gate 0 milestone (Git commit \`31f8de8\`), the sovereign boundary was verified on macOS ARM64 with Python 3.11.16 and NumPy 2.3.5. All 17 initial unit test methods passed without external solver imports. Subsequent milestones introduced verified public benchmarks (Netlib, MIPLIB), exact rational duals, ray recovery, model validation, and the current clean test suite.
