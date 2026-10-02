#!/usr/bin/env python3
"""Run benchmark validation across frozen continuous LP instances using restarted PDHG.

Supports --backend pdhg-cpu and --backend pdhg-cuda.
Supports --stratum SMALL | MEDIUM | LARGE | ALL.
Enforces truthful reporting: on non-CUDA hosts (e.g. Apple Silicon),
--backend pdhg-cuda records CUDA_UNAVAILABLE with gpu_executed=False.
"""

import sys, os, json, time, statistics, platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sovopt.cuda_backend import is_cuda_available, get_device_info
from sovopt.mps import read_mps
from sovopt.pdhg import solve_pdhg
from sovopt.verify import verify

def run_validation(backend="pdhg-cpu", stratum="ALL", instance_filter=None, warmups=3, repeats=7, max_iter=50000, tol=1e-7, output_path=None):
    manifest_path = ROOT / "data/manifests/gpu_pdhg_lp.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text())
    cuda_avail = is_cuda_available()
    dev_info = get_device_info()

    if backend == "pdhg-cuda" and not cuda_avail:
        print("[NOTICE] Requested backend 'pdhg-cuda', but NVIDIA CUDA is unavailable on this host.")
        print("[NOTICE] Enforcing truthful reporting: status=CUDA_UNAVAILABLE, gpu_executed=False.")

    # Filter instances
    selected_instances = {}
    for name, item in manifest.items():
        if instance_filter and name.lower() != instance_filter.lower():
            continue
        if stratum != "ALL" and item.get("stratum") != stratum:
            continue
        selected_instances[name] = item

    print(f"Selected {len(selected_instances)} instances (Stratum: {stratum}, Backend: {backend})")

    results = {}
    summary = {
        "total_instances": len(selected_instances),
        "optimal_verified": 0,
        "limit_reached": 0,
        "cuda_unavailable": 0,
        "numerical_failure": 0,
    }

    start_all = time.perf_counter()

    for name, meta in selected_instances.items():
        mps_file = ROOT / meta["local_file"]
        if not mps_file.exists():
            print(f"Warning: {mps_file} not found; skipping.")
            continue

        print(f"\n--- [{meta.get('stratum')}] {name.upper()} (n={meta['n_variables']}, m={meta['n_constraints']}, nnz={meta['n_nonzeros']}) ---")
        model = read_mps(mps_file)

        if backend == "pdhg-cuda" and not cuda_avail:
            results[name] = {
                "instance": name,
                "stratum": meta.get("stratum"),
                "status": "CUDA_UNAVAILABLE",
                "gpu_executed": False,
                "backend": backend,
                "message": "NVIDIA CUDA runtime is not available on this host",
                "reference_objective": meta.get("reference_objective"),
            }
            summary["cuda_unavailable"] += 1
            print(f"  Result: CUDA_UNAVAILABLE (gpu_executed=False)")
            continue

        # Warmup runs
        for w in range(warmups):
            _ = solve_pdhg(model, backend=backend, tol=tol, max_iter=min(max_iter, 2000), restart=1000, scaling=True)

        # Timed measurement runs
        timings = []
        last_res = None
        for r in range(repeats):
            t0 = time.perf_counter()
            res = solve_pdhg(model, backend=backend, tol=tol, max_iter=max_iter, restart=1000, scaling=True)
            t_elapsed = time.perf_counter() - t0
            timings.append(t_elapsed)
            last_res = res

        median_time = statistics.median(timings)
        min_time = min(timings)
        max_time = max(timings)
        stdev_time = statistics.stdev(timings) if len(timings) > 1 else 0.0

        status = last_res.get("status", "UNKNOWN")
        if status == "OPTIMAL_VERIFIED":
            summary["optimal_verified"] += 1
        elif status == "LIMIT_REACHED":
            summary["limit_reached"] += 1
        else:
            summary["numerical_failure"] += 1

        ref_obj = meta.get("reference_objective")
        sov_obj = last_res.get("objective")
        disc = abs(sov_obj - ref_obj) if (sov_obj is not None and ref_obj is not None) else None
        rel_disc = (disc / max(1.0, abs(ref_obj))) if (disc is not None and ref_obj is not None) else None

        results[name] = {
            "instance": name,
            "stratum": meta.get("stratum"),
            "status": status,
            "gpu_executed": bool(last_res.get("gpu_executed", False)),
            "backend": backend,
            "iterations": last_res.get("iterations"),
            "median_elapsed_seconds": median_time,
            "min_elapsed_seconds": min_time,
            "max_elapsed_seconds": max_time,
            "stdev_elapsed_seconds": stdev_time,
            "raw_timings_seconds": timings,
            "objective": sov_obj,
            "reference_objective": ref_obj,
            "objective_discrepancy": disc,
            "relative_discrepancy": rel_disc,
            "setup_seconds": last_res.get("setup_seconds"),
            "iteration_seconds": last_res.get("iteration_seconds"),
            "verification_seconds": last_res.get("verification_seconds"),
            "telemetry": last_res.get("telemetry"),
            "verification": last_res.get("verification"),
        }

        print(f"  Status   : {status} (gpu_executed={last_res.get('gpu_executed', False)})")
        print(f"  Iters    : {last_res.get('iterations')}")
        print(f"  Time     : median={median_time*1000:.2f}ms (min={min_time*1000:.2f}ms, max={max_time*1000:.2f}ms)")
        if sov_obj is not None and ref_obj is not None:
            print(f"  Objective: {sov_obj:.8e} (ref: {ref_obj:.8e}, rel_err: {rel_disc:.2e})")

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "backend_requested": backend,
        "stratum_requested": stratum,
        "warmups": warmups,
        "repeats": repeats,
        "tolerance": tol,
        "max_iter": max_iter,
        "machine_metadata": {
            "system": platform.system(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
        },
        "device_info": dev_info,
        "summary": summary,
        "results": results,
        "total_elapsed_seconds": time.perf_counter() - start_all,
    }

    if output_path is None:
        ts_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = ROOT / f"reports/gpu/validation_{backend}_{ts_slug}.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nValidation report saved to: {output_path}")
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SOV-OPT GPU PDHG Validation Runner")
    parser.add_argument("--backend", choices=["pdhg-cpu", "pdhg-cuda"], default="pdhg-cpu", help="Solver backend")
    parser.add_argument("--stratum", choices=["ALL", "SMALL", "MEDIUM", "LARGE"], default="ALL", help="Size stratum")
    parser.add_argument("--instance", default=None, help="Filter specific instance name")
    parser.add_argument("--warmups", type=int, default=3, help="Number of warmup iterations")
    parser.add_argument("--repeats", type=int, default=7, help="Number of timed benchmark repetitions")
    parser.add_argument("--max-iter", type=int, default=50000, help="Maximum PDHG iterations")
    parser.add_argument("--tol", type=float, default=1e-7, help="Target KKT verification tolerance")
    parser.add_argument("--output", "-o", default=None, help="Custom output JSON report path")
    args = parser.parse_args()

    run_validation(
        backend=args.backend,
        stratum=args.stratum,
        instance_filter=args.instance,
        warmups=args.warmups,
        repeats=args.repeats,
        max_iter=args.max_iter,
        tol=args.tol,
        output_path=args.output,
    )

if __name__ == "__main__":
    main()
