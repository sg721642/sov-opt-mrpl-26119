"""Differential benchmark: SOV-OPT vs HiGHS (external, subprocess-isolated).

Runs SOV-OPT via its own CLI subprocess and HiGHS via baseline_worker.py
subprocess. Neither solver touches the other. Results are written to
reports/differential_benchmark/results.json.

IMPORTANT: highspy and scipy are NEVER imported here in the parent process.
All external solver calls go through a separate Python interpreter invocation
of baseline_worker.py.
"""
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
BASELINE_WORKER = ROOT / "scripts" / "baseline_worker.py"
NETLIB_DIR = ROOT / "data" / "netlib"
MIPLIB_DIR = ROOT / "data" / "miplib"
NETLIB_MANIFEST = ROOT / "data" / "manifests" / "netlib_lp.json"
MIPLIB_MANIFEST = ROOT / "data" / "manifests" / "miplib_milp.json"
OUT_DIR = ROOT / "reports" / "differential_benchmark"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COMMIT_SHA = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
).strip()

import platform, datetime
META = {
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "sovopt_version": "0.3.2",
    "sovopt_commit": COMMIT_SHA,
    "highs_baseline": "highspy (subprocess-isolated, never imports into sovopt/)",
    "machine": platform.platform(),
    "python": sys.version,
    "disclaimer": (
        "External HiGHS is called exclusively from baseline_worker.py "
        "in a separate subprocess. It is NEVER imported into sovopt/ or server.py."
    ),
    "reporting_policy": (
        "All evaluated instances are reported, including LIMIT_REACHED, "
        "NUMERICAL_FAILURE, and cases where HiGHS is faster."
    ),
}


def run_sovopt(mps_path: Path, timeout: float = 60.0) -> dict:
    """Run SOV-OPT CLI on an MPS file; return parsed result dict."""
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            [str(VENV_PY), "-m", "sovopt", str(mps_path), "--backend", "cpu"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"),
        )
        elapsed = time.perf_counter() - t0
        try:
            result = json.loads(r.stdout)
        except ValueError:
            result = {
                "status": "NUMERICAL_FAILURE",
                "message": f"sovopt worker stderr: {r.stderr[:300].strip()}",
            }
        result["seconds"] = elapsed
        result.setdefault("solver_name", "SOV-OPT")
        return result
    except subprocess.TimeoutExpired:
        return {
            "status": "LIMIT_REACHED",
            "message": f"SOV-OPT timeout after {timeout}s",
            "seconds": timeout,
            "solver_name": "SOV-OPT",
        }


def run_highs_subprocess(mps_path: Path, timeout: float = 60.0) -> dict:
    """Run HiGHS baseline worker as a subprocess; return parsed result dict."""
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            [str(VENV_PY), str(BASELINE_WORKER), str(mps_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"),
        )
        elapsed = time.perf_counter() - t0
        try:
            result = json.loads(r.stdout)
        except ValueError:
            result = {
                "status": "BASELINE_ERROR",
                "message": f"baseline_worker stderr: {r.stderr[:300].strip()}",
                "seconds": elapsed,
            }
        result["seconds"] = elapsed
        result.setdefault("solver_name", "HiGHS")
        return result
    except subprocess.TimeoutExpired:
        return {
            "status": "LIMIT_REACHED",
            "message": f"HiGHS baseline timeout after {timeout}s",
            "seconds": timeout,
            "solver_name": "HiGHS",
        }


def normalize_status(s: str) -> str:
    """Map solver-specific statuses to canonical strings."""
    s = str(s)
    if "Optimal" in s or "OPTIMAL" in s or "kOptimal" in s:
        return "OPTIMAL"
    if "INFEASIBLE" in s or "Infeasible" in s:
        return "INFEASIBLE"
    if "UNBOUNDED" in s or "Unbounded" in s:
        return "UNBOUNDED"
    if "LIMIT_REACHED" in s or "ObjectiveBound" in s or "IterationLimit" in s:
        return "LIMIT_REACHED"
    if "NUMERICAL" in s:
        return "NUMERICAL_FAILURE"
    if "UNSUPPORTED" in s:
        return "UNSUPPORTED"
    return s


def obj_diff(sov_obj, highs_obj):
    if sov_obj is None or highs_obj is None:
        return None
    denom = max(abs(highs_obj), 1e-10)
    return abs(sov_obj - highs_obj) / denom


def run_netlib_comparison(timeout=60.0):
    manifest = json.loads(NETLIB_MANIFEST.read_text())
    results = []
    for key, meta in manifest.items():
        mps = ROOT / meta["local_file"]
        if not mps.exists():
            print(f"  SKIP (missing): {key}")
            continue
        print(f"  LP {key} ({meta['n_variables']}v {meta['n_constraints']}c)...", end="", flush=True)
        sov = run_sovopt(mps, timeout)
        hig = run_highs_subprocess(mps, timeout)
        sov_status = normalize_status(sov.get("status", "UNKNOWN"))
        hig_status = normalize_status(hig.get("model_status", hig.get("status", "UNKNOWN")))
        if hig_status == "UNKNOWN" and hig.get("success"):
            hig_status = "OPTIMAL"
        sov_obj = sov.get("objective")
        hig_obj = hig.get("objective")
        rel_diff = obj_diff(sov_obj, hig_obj)
        ver = "MATCH" if (rel_diff is not None and rel_diff < 1e-4) else (
            "MISMATCH" if rel_diff is not None else "N/A"
        )
        print(f" SOV={sov_status}({sov.get('seconds', 0):.3f}s) HiGHS={hig_status}({hig.get('seconds', 0):.3f}s) {ver}")
        results.append({
            "instance": key.upper(),
            "class": "LP",
            "variables": meta["n_variables"],
            "constraints": meta["n_constraints"],
            "nonzeros": meta.get("n_nonzeros", None),
            "sovopt_status": sov_status,
            "sovopt_time_s": round(sov.get("seconds", 0), 4),
            "highs_status": hig_status,
            "highs_time_s": round(hig.get("seconds", 0), 4),
            "sovopt_objective": sov_obj,
            "highs_objective": hig_obj,
            "relative_obj_diff": round(rel_diff, 8) if rel_diff is not None else None,
            "verification": ver,
            "reference_objective": meta.get("reference_objective"),
            "sovopt_message": sov.get("message", ""),
            "highs_model_status": hig.get("model_status", ""),
        })
    return results


def run_miplib_comparison(timeout=30.0):
    manifest = json.loads(MIPLIB_MANIFEST.read_text())
    results = []
    for key, meta in manifest.items():
        mps = ROOT / meta["local_file"]
        if not mps.exists():
            print(f"  SKIP (missing): {key}")
            continue
        n = meta.get("n_variables", "?")
        m = meta.get("n_constraints", "?")
        ni = meta.get("n_integer", "?")
        print(f"  MILP {key} ({n}v {m}c {ni}int)...", end="", flush=True)
        sov = run_sovopt(mps, timeout)
        hig = run_highs_subprocess(mps, timeout)
        sov_status = normalize_status(sov.get("status", "UNKNOWN"))
        hig_status = normalize_status(hig.get("model_status", hig.get("status", "UNKNOWN")))
        if hig_status == "UNKNOWN" and hig.get("success"):
            hig_status = "OPTIMAL"
        sov_obj = sov.get("objective") or sov.get("incumbent")
        hig_obj = hig.get("objective")
        rel_diff = obj_diff(sov_obj, hig_obj)
        ver = "MATCH" if (rel_diff is not None and rel_diff < 1e-3) else (
            "MISMATCH" if rel_diff is not None else "N/A"
        )
        print(f" SOV={sov_status}({sov.get('seconds', 0):.3f}s) HiGHS={hig_status}({hig.get('seconds', 0):.3f}s) {ver}")
        results.append({
            "instance": key,
            "class": "MILP",
            "variables": meta.get("n_variables"),
            "constraints": meta.get("n_constraints"),
            "integer_variables": meta.get("n_integer"),
            "binary_variables": meta.get("n_binary"),
            "nonzeros": meta.get("n_nonzeros"),
            "sovopt_status": sov_status,
            "sovopt_time_s": round(sov.get("seconds", 0), 4),
            "highs_status": hig_status,
            "highs_time_s": round(hig.get("seconds", 0), 4),
            "sovopt_objective": sov_obj,
            "sovopt_bound": sov.get("best_bound"),
            "sovopt_nodes": sov.get("nodes_explored"),
            "sovopt_gap": sov.get("gap"),
            "highs_objective": hig_obj,
            "highs_bound": hig.get("best_bound"),
            "relative_obj_diff": round(rel_diff, 8) if rel_diff is not None else None,
            "verification": ver,
            "reference_objective": meta.get("reference_objective"),
            "reference_status": meta.get("reference_status"),
            "sovopt_message": sov.get("message", ""),
        })
    return results


if __name__ == "__main__":
    print("=== SOV-OPT vs HiGHS Differential Benchmark ===")
    print(f"Commit: {COMMIT_SHA}")
    print(f"Output: {OUT_DIR}")
    print()

    print("[1/2] Netlib LP Comparison (17 instances)...")
    lp_results = run_netlib_comparison(timeout=90.0)

    print(f"\n[2/2] MIPLIB MILP Comparison ({len(json.loads(MIPLIB_MANIFEST.read_text()))} instances)...")
    milp_results = run_miplib_comparison(timeout=30.0)

    output = {
        "meta": META,
        "lp_comparison": lp_results,
        "milp_comparison": milp_results,
        "summary": {
            "lp_total": len(lp_results),
            "lp_sovopt_optimal": sum(1 for r in lp_results if r["sovopt_status"] == "OPTIMAL"),
            "lp_highs_optimal": sum(1 for r in lp_results if r["highs_status"] == "OPTIMAL"),
            "lp_objective_matches": sum(1 for r in lp_results if r["verification"] == "MATCH"),
            "milp_total": len(milp_results),
            "milp_sovopt_optimal": sum(1 for r in milp_results if r["sovopt_status"] == "OPTIMAL"),
            "milp_highs_optimal": sum(1 for r in milp_results if r["highs_status"] == "OPTIMAL"),
            "milp_sovopt_limit": sum(1 for r in milp_results if r["sovopt_status"] == "LIMIT_REACHED"),
        },
    }

    out_path = OUT_DIR / "results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nResults saved to: {out_path}")
    print(f"LP: {output['summary']['lp_sovopt_optimal']}/{output['summary']['lp_total']} OPTIMAL, "
          f"{output['summary']['lp_objective_matches']} objective matches")
    print(f"MILP: {output['summary']['milp_sovopt_optimal']}/{output['summary']['milp_total']} OPTIMAL, "
          f"{output['summary']['milp_sovopt_limit']} LIMIT_REACHED")
