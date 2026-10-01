#!/usr/bin/env python3
"""Run ablation experiments on restarted PDHG: Preconditioning and Restarting.

Ablations evaluated:
1. Preconditioning: scaling=True (Pock-Chambolle l1 diagonal) vs scaling=False (uniform step size).
2. Restarting: restart=1000 (ergodic averaging restart) vs restart=False (unrestarted).

Supports --backend pdhg-cpu and --backend pdhg-cuda.
Enforces truthful reporting: on non-CUDA hosts (e.g. Apple Silicon),
records CUDA_UNAVAILABLE with gpu_executed=False.
"""

import sys, os, json, time, platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sovopt.cuda_backend import is_cuda_available, get_device_info
from sovopt.mps import read_mps
from sovopt.pdhg import solve_pdhg

DEFAULT_ABLATION_INSTANCES = ["afiro", "sc50a", "blend", "sc105"]

def run_ablation(instances=None, backend="pdhg-cpu", max_iter=30000, tol=1e-7, output_path=None):
    if instances is None:
        instances = DEFAULT_ABLATION_INSTANCES

    manifest_path = ROOT / "data/manifests/gpu_pdhg_lp.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    cuda_avail = is_cuda_available()
    dev_info = get_device_info()

    if backend == "pdhg-cuda" and not cuda_avail:
        print("[NOTICE] Requested backend 'pdhg-cuda', but NVIDIA CUDA is unavailable on this host.")
        print("[NOTICE] Enforcing truthful reporting: status=CUDA_UNAVAILABLE, gpu_executed=False.")

    experiments = [
        {"name": "baseline_restarted_scaled", "scaling": True, "restart": 1000},
        {"name": "no_scaling", "scaling": False, "restart": 1000},
        {"name": "no_restart", "scaling": True, "restart": False},
        {"name": "no_scaling_no_restart", "scaling": False, "restart": False},
    ]

    results = {}
    start_all = time.perf_counter()

    for inst in instances:
        inst_lower = inst.lower()
        mps_path = ROOT / f"data/netlib/{inst_lower}.mps"
        if not mps_path.exists():
            print(f"Warning: {mps_path} not found; skipping.")
            continue

        model = read_mps(mps_path)
        ref_obj = manifest.get(inst_lower, {}).get("reference_objective")
        results[inst_lower] = {
            "instance": inst_lower,
            "dimensions": {"n": len(model.c), "m": len(model.A), "nnz": int((model.A != 0).sum())},
            "reference_objective": ref_obj,
            "configurations": {},
        }

        print(f"\n=== Ablation on {inst_lower.upper()} (n={len(model.c)}, m={len(model.A)}) ===")

        if backend == "pdhg-cuda" and not cuda_avail:
            results[inst_lower]["status"] = "CUDA_UNAVAILABLE"
            results[inst_lower]["gpu_executed"] = False
            for exp in experiments:
                results[inst_lower]["configurations"][exp["name"]] = {
                    "status": "CUDA_UNAVAILABLE",
                    "gpu_executed": False,
                    "backend": backend,
                }
            print("  Result: CUDA_UNAVAILABLE (gpu_executed=False)")
            continue

        for exp in experiments:
            cfg_name = exp["name"]
            scaling = exp["scaling"]
            restart = exp["restart"]

            t0 = time.perf_counter()
            res = solve_pdhg(
                model,
                backend=backend,
                tol=tol,
                max_iter=max_iter,
                restart=restart,
                scaling=scaling,
            )
            elapsed = time.perf_counter() - t0

            vr = res.get("verification", {})
            sov_obj = res.get("objective")
            rel_disc = abs(sov_obj - ref_obj) / max(1.0, abs(ref_obj)) if (sov_obj is not None and ref_obj is not None) else None

            cfg_result = {
                "config": exp,
                "status": res.get("status"),
                "gpu_executed": bool(res.get("gpu_executed", False)),
                "iterations": res.get("iterations"),
                "elapsed_seconds": elapsed,
                "objective": sov_obj,
                "relative_discrepancy": rel_disc,
                "primal_residual": vr.get("primal_residual"),
                "dual_residual": vr.get("dual_residual"),
                "relative_gap": vr.get("relative_duality_gap"),
                "kkt_passed": vr.get("kkt_passed", False),
            }
            results[inst_lower]["configurations"][cfg_name] = cfg_result
            print(f"  [{cfg_name:24s}] Status: {res.get('status'):16s} Iters: {res.get('iterations'):6d}  Time: {elapsed*1000:7.1f}ms  KKT: {vr.get('kkt_passed', False)}")

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "max_iter": max_iter,
        "tolerance": tol,
        "machine_metadata": {
            "system": platform.system(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
        },
        "device_info": dev_info,
        "experiments": experiments,
        "results": results,
        "total_elapsed_seconds": time.perf_counter() - start_all,
    }

    if output_path is None:
        ts_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = ROOT / f"reports/gpu/ablation_{backend}_{ts_slug}.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nAblation report saved to: {output_path}")
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SOV-OPT PDHG Preconditioning & Restart Ablation Runner")
    parser.add_argument("--backend", choices=["pdhg-cpu", "pdhg-cuda"], default="pdhg-cpu", help="Solver backend")
    parser.add_argument("--instances", nargs="+", default=None, help="Instances to benchmark")
    parser.add_argument("--max-iter", type=int, default=30000, help="Maximum PDHG iterations per run")
    parser.add_argument("--tol", type=float, default=1e-7, help="Target KKT verification tolerance")
    parser.add_argument("--output", "-o", default=None, help="Custom output JSON path")
    args = parser.parse_args()

    run_ablation(
        instances=args.instances,
        backend=args.backend,
        max_iter=args.max_iter,
        tol=args.tol,
        output_path=args.output,
    )

if __name__ == "__main__":
    main()
