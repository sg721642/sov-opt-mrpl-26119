# SOV-OPT reference prototype for MRPL PS 26119

Start with **START_HERE.html** or **docs/01_SETUP.md**. This folder contains runnable source, not pseudocode: an original optimization core, a local dashboard, a CLI/API, synthetic refinery examples, tests, and measured reports.

**Scope:** a small, finite-bound research prototype. It does not implement the full industrial solver in the attached research blueprint. In particular, it uses dense primal revised simplex rather than sparse dual simplex. CUDA PDHG source is included but was not executed on GPU hardware during delivery. There is no claim of industrial-scale capacity, commercial-solver superiority, or universal accuracy.

## Run

Use Python 3.12 (3.11+ supported by project metadata). In a terminal opened in this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

Open **http://127.0.0.1:8000**. For Windows use `start_windows.bat` with Python 3.12 installed, or follow the manual commands in the setup guide.

```bash
python -m sovopt examples/refinery_lp.json --output reports/my_lp.json
python -m sovopt examples/refinery_milp.json --output reports/my_milp.json
python -m sovopt examples/refinery_qp.json --output reports/my_qp.json
```

## What is included

| Location | Contents |
|---|---|
| `sovopt/` | Original LU, simplex, predictor-corrector QP, B&B, verifier, MPS subset and CSR PDHG |
| `server.py`, `web/` | Local demo, live solve API, result and audit export |
| `examples/` | LP, MILP, QP, certified-infeasible example, tiny free-format MPS |
| `tests/` | Numerical regression tests, known-optimum cases, exhaustive MILP checks, HTTP integration |
| `scripts/` | Benchmarks, external baseline worker, manifest freezing, GPU comparison, audit checks |
| `docs/` | Setup, mathematics, data format, development plan, deployment, validation and references |
| `reports/` | Actual delivery-time test log, solver outputs and synthetic comparison results |

The core imports NumPy for arrays/vector operations, not an existing optimization package. LU, optimization algorithms, CSR SpMV and verification are implemented here. Optional SciPy/HiGHS exists only in a separate benchmark worker process. The strongest sovereignty design in your PDF also requires custom sparse infrastructure, which this release does not yet provide.

## Measured example results

| Example | Result | Objective |
|---|---|---:|
| Synthetic refinery LP | Numerically verified optimum | 4865 |
| Synthetic refinery MILP | Verified incumbent and numerical gap closure | 4985 |
| Synthetic refinery convex QP | Numerically verified KKT conditions | approximately 5009.500002 |
| Contradictory production | Exact rational Farkas certificate | Not applicable |

These are cost units on synthetic data, not rupees or validated MRPL economics. See `reports/VALIDATION.md` for the distinction between numerical checks and formal certificates.
