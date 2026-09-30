# Step by step setup and first demonstration

This guide gets the supplied code running before you change it. You do not need training data, an AI model, an API key, a commercial solver licence, Node.js, or a GPU for the CPU demo. Optimization accuracy here means feasibility, stationarity, complementarity and an optimality gap, rather than a machine-learning accuracy percentage.

## Step 1 — Extract the ZIP

1. Download `SOV-OPT-MRPL-26119-Prototype.zip`.
2. On macOS, double-click the ZIP in Finder.
3. Move the extracted `sov-opt` folder to a stable location such as `Documents`.
4. Open that folder. You should see `README.md`, `server.py`, `requirements.txt`, `sovopt`, `docs`, and `examples`.
5. Double-click `START_HERE.html` for an offline guide. This is a guide, not the running dashboard.

Do not run Python from inside an unextracted ZIP.

## Step 2 — Install or check Python

1. Open Terminal (Spotlight: Command+Space, type Terminal, press Return).
2. Run `python3 --version`.
3. If Python is absent or older than 3.11, download the Python 3.12 macOS installer from https://www.python.org/downloads/macos/ and complete its installer. Reopen Terminal afterwards.
4. Run `python3 --version` again.

The delivery was tested with Python 3.12.14 and NumPy 2.3.5 on Linux x86-64. The CPU code is portable, but this package was not executed on your Mac. On Apple Silicon, use a native ARM Python installation. Long-double precision varies by platform; the verifier reports the actual mantissa precision rather than assuming 80-bit arithmetic everywhere.

## Step 3 — Open the source in Antigravity

1. Launch Antigravity.
2. Use its folder-opening command (commonly File → Open Folder).
3. Select the extracted `sov-opt` directory, not the ZIP.
4. Trust this project only after you have reviewed the source as you would any downloaded project.
5. Open `README.md` in the editor.
6. Open an integrated terminal using the editor's terminal command. Menu wording may vary with the installed release; macOS Terminal works equally well.
7. Run `pwd` and `ls`. `ls` should list `server.py` and `requirements.txt`. If it does not, navigate to the project folder first.

For a folder placed in Documents:

```bash
cd ~/Documents/sov-opt
```

If the path contains spaces, enclose the complete path in double quotes. You can also type `cd ` and drag the folder from Finder into Terminal, then press Return.

## Step 4 — Create the isolated environment

Run these commands one at a time from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The initial installation needs internet access. Afterwards the CPU solver and dashboard work offline. Keep the `.venv` local; it is not included in the ZIP. The pinned NumPy version makes the array-library dependency reproducible; Python, OS and BLAS differences can still affect floating-point results.

If the editor asks you to select a Python interpreter, choose `.venv/bin/python` inside this folder. This is optional for terminal execution but helpful for code completion and debugging.

## Step 5 — Run the validation suite

```bash
python -m unittest discover -s tests -v
```

Expected result: **17 tests, OK**. Several tests loop over multiple cases: 50 constructed LP optima, 25 integer models checked against exhaustive enumeration, and 20 convex QPs with known KKT solutions. Other tests exercise degeneracy, scaling, fixed variables, lower bounds, Farkas certificates, invalid candidates, MPS input, limits and the HTTP API.

If a test fails, keep the full output and fix that failure before describing your copy as validated. Do not delete tests or loosen tolerances solely to make a green output.

## Step 6 — Start the dashboard

```bash
python server.py
```

Expected message:

```text
SOV-OPT demo at http://127.0.0.1:8000
```

Keep this terminal open. Open Chrome or Safari and enter `http://127.0.0.1:8000` in the address bar. Double-clicking `web/index.html` is not sufficient because the page needs the local solve API.

To stop the server, return to Terminal and press Control+C. To use another port:

```bash
python server.py --port 8001
```

Then open `http://127.0.0.1:8001`.

## Step 7 — Run the LP demonstration

1. Select **Synthetic refinery blending LP**.
2. Leave algorithm route at **CPU reference solver**.
3. Leave feed cost multiplier at **1**.
4. Click **Run & verify**.
5. Confirm `OPTIMAL_VERIFIED` and objective **4865**.
6. Inspect the four feed allocations: **45, 15, 17.5, 32.5**.
7. Read the primal residual, stationarity residual and full reproducibility record.
8. Click **Download audit JSON**. The export includes the exact model you solved and its result.

There is no prefilled dashboard result. Every click calls the real local solver.

## Step 8 — Show decisions changing with the model

1. Change feed cost multiplier to **1.2**.
2. Solve again. On the LP, all feed costs scale equally, so allocations should stay the same and the objective becomes **5838**.
3. To change allocations instead, open **Edit model JSON**, change the second feed cost from 34 to 60, click **Use edited model**, reset multiplier to 1, and solve.
4. A fresh model fingerprint must appear because the input changed.
5. Re-select the original model to restore the shipped input.

For a more meaningful scenario, change quality bounds or crude availability. Preserve units and document every change. Do not change the model silently between solver comparisons.

## Step 9 — Demonstrate MILP

1. Select **Synthetic refinery activation MILP**.
2. Choose CPU and multiplier 1.
3. Solve. Expected objective: **4985**; the binary `high_feed_enabled` variable is **1**.
4. Show the conservative bound, search gap and node count.
5. Explain that the fixed activation cost is 120 synthetic cost units, and the LP relaxation can use fractional activation whereas the MILP cannot.

The MILP badge is based on the tree and gap closure, not continuous KKT checks. The dashboard correctly displays continuous KKT as not used for MILP. Final export verifies the incumbent; it is not a standalone, replayable formal proof of the entire branch-and-bound tree.

## Step 10 — Demonstrate convex QP

1. Select **Synthetic refinery smooth blending QP**.
2. Choose CPU and multiplier 1.
3. Solve. Expect objective near **5009.5** with small original-model residuals.
4. Show the convergence trace and complementarity in the JSON record.
5. Explain that the added objective is `0.04 * sum(x_j^2)` because the model convention is `0.5*x^T*Q*x` and `Q = 0.08*I`.

The QP is convex. This does not solve nonconvex pooling or nonlinear refinery physics.

## Step 11 — Show an infeasibility certificate

1. Select **Contradictory production requirements**.
2. Solve on CPU.
3. Observe `INFEASIBLE_CERTIFIED` and no fake decision vector.
4. Explain the conflict: the same variable must be at least 8 and at most 3.
5. Expand the record to show the certificate. It is checked using exact rational arithmetic on the binary64 input values.

For arbitrary infeasible models, certificate reconstruction may fail. The implementation then reports `NUMERICAL_FAILURE`; do not relabel it as certified infeasibility.

## Step 12 — Run the experimental first-order path

Select the authentic **AVGAS** blending LP, then **Experimental PDHG · CPU**. Solve and compare objective/residuals. Do not select MILP or QP with this route; the API rejects those combinations explicitly. On small cases this method can be slower than simplex. That is an informative result.

The CPU and CUDA PDHG paths share the algorithm but have distinct SpMV implementations. Apple Silicon GPUs do not run this CUDA backend. The supplied CUDA experiment is for an NVIDIA Linux machine; follow `docs/05_GPU_AND_DEPLOYMENT.md`.

## Step 13 — Use the CLI and Python API

```bash
python -m sovopt examples/avgas.json --output reports/local_validation/avgas.json
python -m sovopt examples/afiro.json --output reports/local_validation/afiro.json
python -m sovopt examples/blend.json --output reports/local_validation/blend.json
python -m sovopt examples/flugpl.json --output reports/local_validation/flugpl.json
python -m sovopt examples/avgas.json --backend pdhg-cpu
```

In Python, run from this project folder:

```python
from sovopt import load, solve
model = load('examples/avgas.json')
result = solve(model, tol=1e-7)
print(result['status'], result.get('objective'))
```

To recheck an exported browser audit (replace the example path with your downloaded file):

```bash
python scripts/validate_audit.py ~/Downloads/sovopt-avgas-audit.json
```

## Step 14 — Give Antigravity the correct task

Open `docs/ANTIGRAVITY_PROMPT.md`, copy its instructions into the editor assistant, and ask for one development gate at a time. The code already runs; the first task should be validation and inspection, not rebuilding the whole project. Review all changes with a diff before keeping them.

## Step 15 — Repeat the benchmarks and preserve evidence

```bash
python scripts/generate_reports.py
```

Reports are written under `reports/`. Copy experiment results into dated subfolders before rerunning, because these commands overwrite their named report files. Read `docs/06_BENCHMARKS.md` before presenting comparisons.

## Windows equivalent

Install Python 3.12 from python.org, extract the ZIP, open the project in your editor, and open Command Prompt in that folder:

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

The `start_windows.bat` launcher automates these commands. In PowerShell you can avoid activation-policy changes by calling `.venv\Scripts\python.exe` directly.

## Troubleshooting

| Symptom | Action |
|---|---|
| `No module named numpy` | Activate the project environment and run `python -m pip install -r requirements.txt` |
| `No module named sovopt` | Open the terminal in the folder containing `sovopt/` and `server.py` |
| Port already in use | Stop the earlier server or use `--port 8001` |
| Browser shows no results | Start `server.py`; use its HTTP address, not a file URL |
| `INVALID_MODEL` | Read the error; check finite variable bounds, dimensions, symmetry and supported features |
| `NUMERICAL_FAILURE` | Preserve the model/report and inspect conditioning; never change the badge manually |
| `LIMIT_REACHED` | Inspect any returned candidate and its verification; this is not an optimum claim |
| CUDA unavailable | Use CPU locally or move the GPU experiment to a supported NVIDIA machine |
| Too many web requests | Wait for a worker to finish; there are two concurrent slots |
| macOS refuses the launcher | Use the manual Terminal commands; no need to bypass system security |
