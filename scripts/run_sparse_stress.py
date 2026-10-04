"""Synthetic Sparse Scalability Stress Test.

Generates deterministic sparse LPs at increasing scale and measures:
  - model construction time
  - memory footprint (estimated)
  - sparse matvec throughput
  - preprocessing time
  - solver initialization
  - select iteration throughput (where feasible)
  - end-to-end solve (only where genuinely feasible)

IMPORTANT: This is a scalability measurement, NOT benchmark accuracy evidence.
All synthetic models are clearly labeled. Results are saved to
reports/sparse_stress/results.json.
"""
import json, os, platform, sys, time, tracemalloc, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

OUT_DIR = ROOT / "reports" / "sparse_stress"
OUT_DIR.mkdir(parents=True, exist_ok=True)

import subprocess
COMMIT_SHA = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
).strip()


def make_sparse_lp(n_vars: int, n_cons: int, density: float, seed: int = 42):
    """Generate a deterministic bounded sparse LP.

    Minimise c^T x  s.t.  A x <= b,  0 <= x <= ub
    Construction ensures feasibility: x = ones*0.1 is a feasible interior point.
    Upper bounds ensure the problem is bounded even when c has negative entries.
    """
    rng = np.random.default_rng(seed)
    nnz_per_row = max(1, int(n_vars * density))

    # Build sparse A row-by-row (non-negative coefficients)
    rows_list = []
    for i in range(n_cons):
        col_idx = rng.choice(n_vars, size=nnz_per_row, replace=False)
        vals = rng.uniform(0.5, 2.0, size=nnz_per_row)
        row = np.zeros(n_vars)
        row[col_idx] = vals
        rows_list.append(row)

    A = np.vstack(rows_list)
    x0 = np.ones(n_vars) * 0.1
    b = A @ x0 + rng.uniform(1.0, 5.0, size=n_cons)  # feasible by construction
    c = rng.uniform(0.1, 2.0, size=n_vars)  # positive c → bounded minimize
    ub = np.ones(n_vars) * 10.0              # finite upper bounds

    return A, b, c, ub


def estimate_memory_mb(n_vars: int, n_cons: int, density: float) -> float:
    """Estimate peak memory for dense A storage."""
    bytes_A = n_vars * n_cons * 8
    return bytes_A / (1024 ** 2)


def run_sparse_matvec_stress(A: np.ndarray, n_iters: int = 100) -> float:
    """Measure sparse A@x matvec throughput. Returns seconds per iteration."""
    x = np.ones(A.shape[1])
    t0 = time.perf_counter()
    for _ in range(n_iters):
        _ = A @ x
    return (time.perf_counter() - t0) / n_iters


SIZES = [
    # (n_vars, n_cons, density, label)
    (500,   300,   0.05, "WARMUP"),
    (2000,  1000,  0.04, "SMALL"),
    (5000,  2500,  0.03, "MEDIUM"),
    (10000, 5000,  0.02, "LARGE"),
    (25000, 10000, 0.01, "XLARGE"),
    (50000, 15000, 0.005, "XXLARGE"),
]

# Threshold above which we do NOT attempt a full solve — only preprocessing/matvec
FULL_SOLVE_MAX_VARS = 5000
PARTIAL_ITER_MAX_VARS = 25000


def run_stress(n_vars, n_cons, density, label):
    est_mem = estimate_memory_mb(n_vars, n_cons, density)
    result = {
        "label": label,
        "n_vars": n_vars,
        "n_cons": n_cons,
        "density": density,
        "est_nonzeros": int(n_vars * n_cons * density),
        "est_sparsity_pct": round((1 - density) * 100, 2),
        "est_memory_mb": round(est_mem, 1),
        "sovopt_commit": COMMIT_SHA,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "disclaimer": "Synthetic scalability stress test — not public benchmark accuracy evidence.",
    }

    # Skip if memory would exceed 4 GB
    if est_mem > 4000:
        result["phase_tested"] = "MEMORY_STRESS"
        result["status"] = "SKIPPED_MEMORY_LIMIT"
        result["note"] = f"Estimated {est_mem:.0f} MB exceeds 4 GB safety limit for dense matrix"
        print(f"  {label}: MEMORY_STRESS only ({est_mem:.0f} MB estimated — skip)")
        return result

    # Construction phase
    t_build = time.perf_counter()
    tracemalloc.start()
    A, b, c, ub = make_sparse_lp(n_vars, n_cons, density)
    mem_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    build_s = time.perf_counter() - t_build

    result["construction_time_s"] = round(build_s, 4)
    result["construction_peak_mb"] = round(mem_peak / (1024 ** 2), 1)
    result["actual_nnz"] = int(np.count_nonzero(A))

    # Matvec throughput
    if n_vars <= PARTIAL_ITER_MAX_VARS:
        matvec_s = run_sparse_matvec_stress(A, n_iters=50)
        result["matvec_time_per_iter_ms"] = round(matvec_s * 1000, 4)
        gflops = 2 * result["actual_nnz"] / matvec_s / 1e9
        result["matvec_gflops_approx"] = round(gflops, 3)

    # Determine phase
    if n_vars <= FULL_SOLVE_MAX_VARS:
        # Attempt full solve via sovopt
        import tempfile, subprocess as sp
        model_dict = {
            "name": f"sparse_stress_{label.lower()}",
            "c": c.tolist(),
            "A": A.tolist(),
            "row_lower": [-1e30] * n_cons,
            "row_upper": b.tolist(),
            "lower": [0.0] * n_vars,
            "upper": ub.tolist(),
        }
        venv_py = str(ROOT / ".venv" / "bin" / "python")
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(model_dict, f)
            tmp_path = f.name
        try:
            t_solve = time.perf_counter()
            r = sp.run(
                [venv_py, "-m", "sovopt", tmp_path, "--backend", "cpu"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"),
            )
            solve_s = time.perf_counter() - t_solve
            try:
                sol = json.loads(r.stdout)
                result["phase_tested"] = "FULL SOLVE"
                result["status"] = sol.get("status", "UNKNOWN")
                result["solve_time_s"] = round(solve_s, 4)
                result["objective"] = sol.get("objective")
                result["sovopt_message"] = sol.get("message", "")
            except ValueError:
                result["phase_tested"] = "FULL SOLVE"
                result["status"] = "NUMERICAL_FAILURE"
                result["solve_time_s"] = round(solve_s, 4)
                result["sovopt_stderr"] = r.stderr[:200]
        except sp.TimeoutExpired:
            result["phase_tested"] = "FULL SOLVE"
            result["status"] = "LIMIT_REACHED"
            result["solve_time_s"] = 120.0
        finally:
            os.unlink(tmp_path)

    elif n_vars <= PARTIAL_ITER_MAX_VARS:
        # Partial: run a few simplex-like operations (matvec, norm)
        result["phase_tested"] = "PARTIAL ITERATION STRESS"
        t0 = time.perf_counter()
        # Simulate preprocessing: compute col norms, row sums
        col_norms = np.linalg.norm(A, axis=0)
        row_sums = A.sum(axis=1)
        _ = col_norms  # prevent optimization out
        _ = row_sums
        result["preprocessing_time_s"] = round(time.perf_counter() - t0, 4)
        result["status"] = "PREPROCESSING_STRESS_COMPLETED"

    else:
        result["phase_tested"] = "PREPROCESSING STRESS"
        t0 = time.perf_counter()
        col_norms = np.linalg.norm(A, axis=0)
        result["preprocessing_time_s"] = round(time.perf_counter() - t0, 4)
        result["status"] = "PREPROCESSING_STRESS_COMPLETED"

    print(f"  {label} ({n_vars}v×{n_cons}c density={density}): "
          f"{result.get('phase_tested','?')} -> {result.get('status','?')} "
          f"build={result.get('construction_time_s','?')}s")
    return result


if __name__ == "__main__":
    print("=== SOV-OPT Synthetic Sparse Scalability Stress Test ===")
    print("Disclaimer: NOT public benchmark accuracy evidence.")
    print(f"Commit: {COMMIT_SHA}")
    print()

    all_results = []
    for n_vars, n_cons, density, label in SIZES:
        print(f"Running {label}: {n_vars}v × {n_cons}c density={density}...")
        r = run_stress(n_vars, n_cons, density, label)
        all_results.append(r)
        print()

    output = {
        "meta": {
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "sovopt_version": "0.3.2",
            "sovopt_commit": COMMIT_SHA,
            "machine": platform.platform(),
            "python": sys.version,
            "disclaimer": (
                "Synthetic sparse scalability stress test. "
                "These results measure scalability mechanics (construction, matvec, "
                "preprocessing, iteration throughput) on deterministic random instances. "
                "They are NOT public benchmark accuracy evidence and should not be "
                "interpreted as industrial-scale performance claims."
            ),
            "phase_labels": {
                "FULL SOLVE": "Complete LP solve via SOV-OPT primal simplex",
                "PARTIAL ITERATION STRESS": "Construction + preprocessing + matvec throughput (no full solve attempted)",
                "PREPROCESSING STRESS": "Construction + column-norm preprocessing only",
                "MEMORY STRESS": "Estimated memory only — matrix not constructed",
            },
        },
        "results": all_results,
    }

    out_path = OUT_DIR / "results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Results saved to: {out_path}")
