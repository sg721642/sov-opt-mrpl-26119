# SOV-OPT Reproducibility Guide

This guide describes how evaluators and hackathon judges can independently reproduce and verify SOV-OPT solver results, benchmark evidence, and differential comparisons.

---

## 1. Environment & Prerequisites

- **Supported Platforms:** Linux x86_64, macOS (Apple Silicon / Intel), Windows 11
- **Required Python Version:** Python $\ge$ 3.11 (tested on Python 3.11.16)
- **Core Dependencies:** NumPy (`numpy==2.3.5` in `requirements.txt`) + Python standard library
- **Zero Core Solver Dependencies:** No HiGHS, Gurobi, CPLEX, SCIP, CBC, OR-Tools, CVXPY, or PuLP in the core solver (`sovopt/`).
- **Cloud Note:** Public cloud web deployment is CPU-only. CUDA GPU execution was conducted on an Acer laptop with NVIDIA RTX 5050.

---

## 2. Installation

```bash
# 1. Clone repository
git clone https://github.com/sg721642/sov-opt-mrpl-26119.git
cd sov-opt-mrpl-26119

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install core dependencies
pip install --no-cache-dir -r requirements.txt

# 4. Optional: Install benchmark baseline worker dependency (BENCHMARK ONLY)
# Note: highspy is used exclusively by scripts/baseline_worker.py in subprocess isolation.
pip install highspy==1.15.1
```

---

## 3. Push-Button Evidence Evaluator

The evaluator script `scripts/reproduce_evidence.py` runs standard verification suites in seconds:

```bash
# Run all reproducibility modes
python scripts/reproduce_evidence.py --all

# Or run individual verification targets:
python scripts/reproduce_evidence.py --mode self-test
python scripts/reproduce_evidence.py --mode small-lp
python scripts/reproduce_evidence.py --mode small-qp
python scripts/reproduce_evidence.py --mode small-milp
python scripts/reproduce_evidence.py --mode infeasible
python scripts/reproduce_evidence.py --mode netlib-sample
python scripts/reproduce_evidence.py --mode highs-sample
```

### Expected Output Summary

| Mode | Target | Expected Status | Guarantee / Output |
| :--- | :--- | :--- | :--- |
| `self-test` | Core Sanity LP | `OPTIMAL_VERIFIED` | Pure NumPy dispatch verified |
| `small-lp` | Refinery LP Twin | `OPTIMAL_VERIFIED` | KKT residuals $\le 10^{-7}$ |
| `small-qp` | Refinery Smooth Dispatch | `OPTIMAL_VERIFIED` | Predictor-corrector IPM KKT verified |
| `small-milp` | Refinery Unit Commitment | `OPTIMAL_VERIFIED` | Exact $\mathbb{Q}$-bound relative gap $0.00\%$ |
| `infeasible` | Refinery Infeasible Demand | `INFEASIBLE_CERTIFIED` | Exact rational Farkas certificate ray |
| `netlib-sample`| Netlib AFIRO | `OPTIMAL_VERIFIED` | Relative error to reference $< 10^{-10}$ |
| `highs-sample` | Netlib AFIRO vs HiGHS | `OPTIMAL_VERIFIED` | Relative objective diff $0.00\times 10^0$ [MATCH] |

---

## 4. Full Regression Test Suite

Run the full automated test suite (342 tests):

```bash
python -m unittest discover -s tests -v
```

Expected result: `Ran 342 tests in ~60s ... OK (skipped=14)`.

---

## 5. Checksum Verification

Verify SHA-256 integrity across all repository files:

```bash
python scripts/verify_checksums.py
```

Expected result: `SUCCESS: All entries in SHA256SUMS.json are valid and match working tree.`

---

## 6. Local Web Workstation Verification

Start the local HTTP workstation and inspect the browser interface:

```bash
python server.py --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in your web browser:
- **Optimization Console:** Run live continuous, discrete, and quadratic refinery schedules.
- **Trust & Verification:** Inspect KKT stationarity, Farkas infeasibility rays, and export canonical JSON Trust Passports.
- **Benchmarks Tab:** Review physical RTX 5050 hardware evidence, SOV-OPT vs HiGHS differential tables, MIPLIB 2017 results, and synthetic sparse scalability data.
- **Evidence & Audits Tab:** Inspect the complete 20-row Problem Statement Coverage Matrix and numerical stress test cases.
