#!/usr/bin/env python3
"""SOV-OPT Multicore Characterization — Parallel Batch Throughput.

Measures wall-clock throughput across concurrent independent solves.
IMPORTANT:
This experiment measures process-level parallel batch throughput across independent
optimization problems. It does NOT represent parallel branch-and-bound or
intra-solve multi-threaded simplex.
"""
import datetime
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sovopt

INSTANCES = [
    "adlittle", "afiro", "blend", "kb2",
    "recipe", "sc50a", "sc50b", "stocfor1"
]
WORKER_COUNTS = [1, 2, 4]


def get_git_commit() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"


def solve_subprocess(mps_path: Path) -> dict:
    t0 = time.perf_counter()
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    cmd = [sys.executable, "-m", "sovopt", str(mps_path)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    elapsed = time.perf_counter() - t0
    status = "UNKNOWN"
    try:
        data = json.loads(r.stdout)
        status = data.get("status", "UNKNOWN")
    except Exception:
        status = "PARSE_ERROR"
    return {"status": status, "elapsed": elapsed}


def run_benchmark():
    print("=== SOV-OPT Multicore Characterization: Parallel Batch Throughput ===")
    print("Disclaimer: Parallel batch throughput across independent solves.")
    print("Does NOT represent intra-solve parallel B&B or multi-threaded simplex.")
    commit = get_git_commit()
    print(f"Commit: {commit}\n")

    paths = [ROOT / f"data/netlib/{inst}.mps" for inst in INSTANCES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"Required benchmark instance {p} not found.")

    results_by_workers = []
    base_throughput = None

    for workers in WORKER_COUNTS:
        print(f"Running batch with {workers} worker(s)...")
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            task_results = list(ex.map(solve_subprocess, paths))
        wall_time = time.perf_counter() - t0
        throughput = len(paths) / wall_time
        if base_throughput is None:
            base_throughput = throughput
        speedup = throughput / base_throughput

        all_optimal = all(r["status"] == "OPTIMAL_VERIFIED" for r in task_results)
        print(f"  Workers: {workers} -> Wall-clock: {wall_time:.3f} s, Throughput: {throughput:.2f} inst/s, Scaling: {speedup:.2f}x (All verified: {all_optimal})")

        results_by_workers.append({
            "workers": workers,
            "wall_clock_seconds": round(wall_time, 4),
            "throughput_instances_per_second": round(throughput, 2),
            "speedup_vs_single_worker": round(speedup, 2),
            "batch_size": len(paths),
            "all_verified": all_optimal,
            "instance_details": [
                {"instance": inst, "status": tr["status"], "elapsed_seconds": round(tr["elapsed"], 4)}
                for inst, tr in zip(INSTANCES, task_results)
            ]
        })

    output = {
        "meta": {
            "experiment": "Parallel Batch Throughput — Independent Solves",
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "sovopt_version": sovopt.__version__,
            "sovopt_commit": commit,
            "machine": subprocess.run(["uname", "-srm"], capture_output=True, text=True).stdout.strip(),
            "python": sys.version.split()[0],
            "disclaimer": "Parallel batch throughput across independent solves. This does NOT represent parallel branch-and-bound or intra-solve multi-threaded simplex.",
            "concurrency_mechanism": "Subprocess-level concurrency with OPENBLAS_NUM_THREADS=1 isolation per process",
            "evaluation_set": INSTANCES,
        },
        "results": results_by_workers
    }

    out_dir = ROOT / "reports/batch_throughput"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "results.json"
    out_file.write_text(json.dumps(output, indent=2))
    print(f"\nResults saved to: {out_file}")


if __name__ == "__main__":
    run_benchmark()
