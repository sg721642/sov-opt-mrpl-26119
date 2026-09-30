# Benchmarking and evidence

## Included measurements

`reports/tests.txt` records the delivered test run. `reports/benchmark.json` contains repeated runs on synthetic examples, including scaling on/off and external LP/MILP comparisons. These are not Netlib/MIPLIB/QPLIB performance results. Timing values depend on the Linux delivery environment and are not predictions for your Mac.

The external worker imports SciPy/HiGHS in a separate process. The core never imports it. There is no measured commercial solver comparison, no downloaded public benchmark collection, and no measured GPU result. The convex QP is checked by constructed KKT cases and analytic demo values, not by an external QP solver in this package.

## Reproduce the isolated baseline

Keep benchmark dependencies out of the core environment when reproducing:

```bash
python3 -m venv .venv-benchmark
.venv-benchmark/bin/python -m pip install numpy==2.3.5 scipy==1.17.0
source .venv/bin/activate
python scripts/benchmark.py --external-python .venv-benchmark/bin/python --repeats 3
```

Windows equivalent uses `.venv-benchmark\Scripts\python.exe`. The adapter handles native JSON LP/MILP and uses SciPy's interface to HiGHS. Its LP/MIP solver defaults are not matched to our internal tolerances, so interpret the current comparison as an objective sanity check, not a publication-quality speed race. Before a performance claim, fix equivalent feasibility/optimality criteria, thread counts and all external options.

The benchmark's solver time excludes interpreter process startup. External imports occur before its timer, but JSON loading is included there; our timing starts after model creation. This small asymmetry makes the current time columns descriptive only. A publication harness must apply consistent timing boundaries to both engines.

## Freeze a manifest

```bash
python scripts/freeze_manifest.py examples/refinery_lp.json examples/refinery_milp.json --output reports/manifest.json
python scripts/run_manifest.py reports/manifest.json
```

The manifest stores hashes and relative paths. Fill in official provenance and any verified reference objective before publishing it. `run_manifest.py` refuses changed files and retains invalid/unsupported inputs and external timeouts as results. Do not remove failures from denominators after seeing them.

For additional files, use the same workflow with authorized local JSON/MPS files. Standard dataset files must first be in a supported, decompressed format; the parser does not read `.mps.gz` directly. Never convert unsupported/free variables by adding arbitrary bounds solely to improve a benchmark score.

## Public benchmark progression

1. Obtain documented instances from the official Netlib, MIPLIB or QPLIB repositories (links in `07_REFERENCES.md`). Respect dataset terms.
2. Expand parser and model support before claiming suite coverage. Most industrial instances exceed this release's finite-box/dense restrictions.
3. Define a supported-feature filter in advance. Save rejected names and reasons.
4. Split a deterministic development and held-out subset before tuning.
5. Record source URLs, download/freeze date, file hash, reference solution provenance, dimensions/nonzeros, model type, tolerances, solver commit, machine and memory limits.
6. Run every frozen case with a subprocess deadline and memory limit.
7. Report objective error and original primal/dual residuals for LP; stationarity/complementarity for QP; incumbent, valid bound, gap and nodes for MILP.
8. Compare at matched accepted accuracy. Use multiple repeats for short problems. Include cold versus warm device costs.
9. Use a predefined timeout policy for summaries; report solved, failed, unsupported and timed-out counts separately. If using shifted geometric mean, publish the shift and timeout penalty.
10. Publish largest actually solved dimensions and memory rather than intended capacity.

## Accuracy targets

The default numerical tolerance is 1e-7. A stronger number is not automatically more accurate if the model is ill-conditioned. Test original absolute violations in physical units, normalized residuals, objective error against a reference and sensitivity to coefficient scaling. Residual verification is necessary but does not prove universal reliability.

The internal test suite has 50 constructed LP optima, 25 tiny integer models exhaustively enumerated, and 20 constructed diagonal convex-QP optima, plus focused numerical and interface tests. These are valuable regression checks and too small/easy to establish industrial robustness.

## Allowed presentation language

“Original reference solver passes the supplied regression suite; synthetic refinery LP and MILP objectives agree with an external HiGHS process.”

“Every reported continuous optimum is checked against the original-model KKT conditions; exact rational bounds support finite-box MILP pruning.”

“Experimental CUDA PDHG source is included; GPU performance validation is pending.”

Do not say “99.9% accuracy,” “CPLEX replacement,” “certified exact optimality for all outputs,” “million-variable capability,” “2× faster on GPU,” “full research blueprint implemented,” or “MRPL-validated refinery model” based on this delivery.
