# SOV-OPT Deployment & Operations Guide

This guide describes the production deployment configuration, runtime dependencies,
and operational parameters for the SOV-OPT web dashboard and HTTP API.

---

## 1. Runtime Environment & Dependencies

- **Tested Python Version:** Python 3.11 (Python >= 3.11 supported).
- **Core Runtime Dependency:** NumPy (`numpy==2.3.5` in `requirements.txt`).
- **Core Dependencies:** Python standard library (`http.server`, `json`, `argparse`, `subprocess`, `tempfile`, `fractions`, `hashlib`).
- **Zero External Solvers:** No HiGHS, SCIP, CBC, OR-Tools, CVXPY, PuLP, Gurobi, or CPLEX.
- **CPU-Only Operation:** CuPy, CUDA toolkit, and NVIDIA drivers are strictly optional and NOT required for web deployment. The server automatically falls back to CPU execution with zero performance degradation on standard cloud platforms.

---

## 2. Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install exact pinned runtime dependencies
pip install --no-cache-dir -r requirements.txt
```

---

## 3. Server Startup & Configuration

### Production Start Command
```bash
python server.py
```

### Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `HOST` | `127.0.0.1` | Network interface to bind. Use `HOST=0.0.0.0` for cloud deployment. |
| `PORT` | `8000` | Port number assigned by hosting provider or local config. |
| `SOVOPT_COMMIT_SHA` | `null` | Optional Git commit SHA displayed in the Trust Passport for traceability. |
| `OPENBLAS_NUM_THREADS` | `1` | Enforced internally per solver worker to prevent thread starvation. |
| `OMP_NUM_THREADS` | `1` | Enforced internally per solver worker. |

### Command-Line Arguments
```bash
python server.py --host 0.0.0.0 --port 8000
```
Command-line arguments override environment variables when explicitly passed.

---

## 4. Health & Liveness Endpoints

The server provides lightweight health check endpoints that do not trigger solver computations:

- `GET /health`
- `GET /api/health`

### Response Schema (HTTP 200)
```json
{
  "status": "ok",
  "service": "sov-opt",
  "version": "0.3.2",
  "solver_ready": true
}
```

---

## 5. Security & Resource Safeguards

For public deployment, `server.py` enforces the following built-in safeguards:
1. **Model Size Limits:** Maximum 100 variables and 150 constraints on `/api/solve`. Larger models must use the sovereign CLI.
2. **Request Payload Cap:** Maximum 300,000 bytes per request (prevents denial-of-service via huge payloads).
3. **Execution Concurrency Cap:** Maximum 2 concurrent optimization workers via `threading.BoundedSemaphore(2)`. Subsequent requests receive HTTP 429 (`Two solves already running; retry shortly`).
4. **Subprocess Timeout:** Hard 35-second execution deadline per solve job. Times out gracefully returning HTTP 200 with `status: LIMIT_REACHED`.
5. **Worker Isolation:** Each solve executes in an isolated temporary directory via `python -m sovopt`, automatically cleaned up after completion.
6. **Backend Gate:** Web demo permits only `cpu` or `pdhg-cpu` backends. Uncertified or unsupported backends are rejected with HTTP 400.

---

## 6. Local Verification Smoke Test

To verify deployment readiness on an alternate port:
```bash
HOST=127.0.0.1 PORT=8765 python server.py &
SERVER_PID=$!

# Test health
curl -s http://127.0.0.1:8765/api/health

# Test root page
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/

# Test model generation
curl -s http://127.0.0.1:8765/api/refinery_twin?variant=lp | grep -q "MRPL_Refinery_Twin_LP" && echo "Model API OK"

# Stop server
kill $SERVER_PID
```
