# SOV-OPT Reference Prototype for MRPL PS 26119

Start with **START_HERE.html** or **docs/01_SETUP.md**. This repository contains a working, reproducible numerical optimization research prototype developed for MRPL SIH Problem Statement 26119.

**Scope:** A finite-box continuous and mixed-integer numerical optimization engine built from first principles. It uses dense revised simplex with exact rational dual and Farkas certification, branch-and-bound with exact rational lower bounding, and interior-point QP. Zero third-party optimization libraries (HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, CPLEX, cuOpt) are imported in the solver core.

All models in the active suite are authentic, public benchmarks from authoritative sources (Netlib LP, MIPLIB, and published operations research literature).

---

## Quick Start

Use Python 3.11 or 3.12. In a terminal opened in this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

Open **http://127.0.0.1:8000** to launch the interactive verification dashboard.

Solve verified instances via CLI:

```bash
python -m sovopt examples/avgas.json --output reports/local_validation/avgas.json
python -m sovopt examples/afiro.json --output reports/local_validation/afiro.json
python -m sovopt examples/blend.json --output reports/local_validation/blend.json
python -m sovopt examples/flugpl.json --output reports/local_validation/flugpl.json
```

---

## What is Included

| Location | Contents |
|---|---|
| `sovopt/` | Sovereign LU factorization, revised simplex, branch-and-bound, predictor-corrector QP, independent verifier, MPS parser, and PDHG |
| `server.py`, `web/` | Local interactive dashboard, live solve API, trust reports, and audit export |
| `data/verified/` | Authentic MPS benchmark instances with cryptographic hashes (`avgas.mps`, `afiro.mps`, `sc50a.mps`, `sc50b.mps`, `blend.mps`, `flugpl.mps`) |
| `examples/` | Canonical JSON versions of verified instances |
| `tests/` | Regression tests, exact Farkas certificates, rational bounds, LU residuals, and HTTP endpoints |
| `scripts/` | Benchmark generators, report tools, and isolated baseline comparison workers |
| `docs/` | Architecture, mathematics, setup, and implementation status |
| `reports/` | Test logs, verified benchmark tables, and master audit documentation |

---

## Verified Benchmark Results (Apple Silicon ARM64 CPU)

| Instance | Class | Dimensions | Status | SOV-OPT Objective | Published Reference | Reference Source |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **AVGAS** | LP | 10 x 8 | `OPTIMAL_VERIFIED` | **-7.750000** | -7.75 | Symonds (1955) |
| **AFIRO** | LP | 27 x 32 | `OPTIMAL_VERIFIED` | **-464.753143** | -4.6475314286E+02 | Netlib / MINOS 5.3 |
| **SC50A** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-64.575077** | -6.4575077059E+01 | Netlib / MINOS 5.3 |
| **SC50B** | LP | 50 x 48 | `OPTIMAL_VERIFIED` | **-70.000000** | -7.0000000000E+01 | Netlib / MINOS 5.3 |
| **BLEND** | LP | 74 x 83 | `OPTIMAL_VERIFIED` | **-30.812150** | -3.0812149846E+01 | Netlib / MINOS 5.3 |
| **FLUGPL** | MILP | 18 x 18 (11 int) | `LIMIT_REACHED` | Bound: **1173645.0** | 1201500 (opt) / 769500 (root) | MIPLIB 1.0 / 2017 |

---

## Disclosures & Empty States

1. **Proprietary MRPL Refinery Data (Empty State):**
   - *No authorized MRPL dataset is available in this project.* Fictional refinery parameters or placeholder economic numbers are strictly prohibited. Genuine historical petroleum blending benchmarks (`AVGAS` and `BLEND`) are provided instead.

2. **Industrial Convex QP Data (Empty State):**
   - *No authentic public industrial convex QP benchmark is currently verified in the active suite.* Synthetic toy QP instances have been removed.

3. **Hardware Execution:**
   - All benchmark solves execute on the CPU (`gpu_executed: false`).
   - The experimental CUDA PDHG backend is not executable on Apple Silicon macOS; no GPU speedup claims are made.

