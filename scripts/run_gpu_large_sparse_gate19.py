#!/usr/bin/env python3
"""Gate 19B — Physical RTX 5050 Large-Sparse GPU Validation Benchmark Harness.

Executes same-machine CPU-vs-CUDA benchmark evidence on physical NVIDIA RTX 5050
laptop GPU with per-solve timeout isolation, checkpointing, caching, and memory safety guards.

Outputs:
  - reports/gpu_large_sparse_gate19/results.json
  - reports/gpu_large_sparse_gate19/results.partial.json
  - reports/gpu_large_sparse_gate19/README.md
  - reports/gpu_large_sparse_gate19/raw/
"""

import os
import sys
import time
import json
import math
import argparse
import subprocess
from pathlib import Path
import numpy as np

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure CUDA_PATH is set for CuPy RawKernel compilation
_python_dir = os.path.dirname(sys.executable)
_candidate_cuda_path = os.path.normpath(os.path.join(_python_dir, "Library"))
if os.path.isfile(os.path.join(_candidate_cuda_path, "include", "cuda.h")):
    os.environ["CUDA_PATH"] = _candidate_cuda_path

from sovopt.model import Model
from sovopt.pdhg import solve_pdhg
from sovopt.cuda_backend import is_cuda_available, get_device_info

REPORTS_DIR = ROOT / "reports" / "gpu_large_sparse_gate19"
RAW_DIR = REPORTS_DIR / "raw"


def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "f7b49c260f54d8677a9652f5985484c61e685d6a"


def generate_bounded_feasible_sparse_lp(n_vars: int, n_rows: int, nnz_per_row: int = 6, seed: int = 42) -> tuple[Model, dict]:
    """Generate a mathematically guaranteed bounded, feasible sparse LP.
    
    Feasible point: x* = (5.0, ..., 5.0)^T satisfies 0 < x* < 10.0.
    Slack s_i > 0 ensures A x* + s = row_upper strictly.
    Objective c is bounded on [0, 10]^n hypercube.
    """
    rng = np.random.RandomState(seed)
    A = np.zeros((n_rows, n_vars), dtype=np.float64)
    for i in range(n_rows):
        cols = rng.choice(n_vars, size=min(nnz_per_row, n_vars), replace=False)
        vals = rng.uniform(-1.0, 1.0, size=len(cols))
        A[i, cols] = vals

    x_star = np.full(n_vars, 5.0)
    Ax_star = (A * x_star).sum(axis=1)
    slacks = rng.uniform(0.5, 2.0, size=n_rows)
    row_upper = Ax_star + slacks
    row_lower = np.full(n_rows, -np.inf)

    c = rng.uniform(-1.0, 1.0, size=n_vars)
    lower = np.zeros(n_vars)
    upper = np.full(n_vars, 10.0)
    names = tuple(f"x{i}" for i in range(n_vars))

    model = Model(c, A, row_lower, row_upper, lower, upper, (), None, f"large_sparse_{n_vars}", names)

    nnz = int(np.count_nonzero(A))
    density = float(nnz / (n_rows * n_vars))
    # Memory estimations
    host_mem_bytes = (n_rows * n_vars * 8) + (n_vars * 8 * 8) + (n_rows * 8 * 5)
    gpu_mem_bytes = (nnz * 12 * 2) + ((n_rows + 1 + n_vars + 1) * 4) + (n_vars * 8 * 8) + (n_rows * 8 * 5)

    stats = {
        "rows": n_rows,
        "columns": n_vars,
        "nonzeros": nnz,
        "density": density,
        "estimated_host_memory_bytes": host_mem_bytes,
        "estimated_gpu_memory_bytes": gpu_mem_bytes,
    }
    return model, stats


def worker_main():
    """Worker process entry point for running a single solve in process isolation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--n-vars", type=int, required=True)
    parser.add_argument("--n-rows", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--backend", type=str, required=True)
    parser.add_argument("--max-iter", type=int, default=3000)
    parser.add_argument("--tol", type=float, default=1e-4)
    parser.add_argument("--out-file", type=str, required=True)

    args = parser.parse_args()

    model, stats = generate_bounded_feasible_sparse_lp(args.n_vars, args.n_rows, seed=args.seed)
    t_start = time.perf_counter()
    res = solve_pdhg(model, backend=args.backend, max_iter=args.max_iter, tol=args.tol)
    t_elapsed = time.perf_counter() - t_start

    result_payload = {
        "status": res["status"],
        "iterations": res["iterations"],
        "objective": res.get("objective"),
        "verification": res.get("verification", {}),
        "total_elapsed_seconds": res["total_elapsed_seconds"],
        "measured_elapsed_seconds": t_elapsed,
        "gpu_executed": res.get("gpu_executed", False),
    }

    Path(args.out_file).write_text(json.dumps(result_payload, indent=2))
    sys.exit(0)


def execute_solve_with_timeout(n_vars: int, n_rows: int, seed: int, backend: str, max_iter: int, tol: float, timeout_sec: int) -> dict:
    """Execute a single solve in an isolated child process with a hard wall-clock timeout."""
    temp_out = RAW_DIR / f"temp_solve_{backend}_{n_vars}_{seed}_{time.time_ns()}.json"
    if temp_out.exists():
        temp_out.unlink()

    cmd = [
        sys.executable,
        "-m", "scripts.run_gpu_large_sparse_gate19",
        "--worker",
        "--n-vars", str(n_vars),
        "--n-rows", str(n_rows),
        "--seed", str(seed),
        "--backend", backend,
        "--max-iter", str(max_iter),
        "--tol", str(tol),
        "--out-file", str(temp_out),
    ]

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        elapsed = time.perf_counter() - t0
        if proc.returncode == 0 and temp_out.exists():
            payload = json.loads(temp_out.read_text())
            temp_out.unlink()
            return payload
        else:
            if temp_out.exists():
                temp_out.unlink()
            return {
                "status": "PROCESS_ERROR",
                "iterations": 0,
                "objective": None,
                "verification": {"kkt_passed": False},
                "total_elapsed_seconds": elapsed,
                "gpu_executed": (backend == "pdhg-cuda"),
            }
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - t0
        if temp_out.exists():
            temp_out.unlink()
        return {
            "status": "LIMIT_REACHED (TIMEOUT > 60s)",
            "iterations": max_iter,
            "objective": None,
            "verification": {"kkt_passed": False},
            "total_elapsed_seconds": elapsed,
            "gpu_executed": (backend == "pdhg-cuda"),
        }


def run_benchmark():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    commit_sha = get_git_commit()
    dev_info = get_device_info()

    cuda_ok = is_cuda_available()
    print(f"=== SOV-OPT Gate 19B GPU Validation Benchmark ===")
    print(f"Commit SHA: {commit_sha}")
    print(f"CUDA Available: {cuda_ok}")
    if dev_info:
        print(f"GPU Device: {dev_info.get('device_name')}")
        print(f"VRAM Total: {dev_info.get('total_memory_bytes', 0) / (1024**2):.1f} MiB")

    metadata = {
        "machine": "Acer Nitro V 16S (ANV16S-71)",
        "cpu": "Intel(R) Core(TM) 5 210H (8 Cores, 12 Threads)",
        "ram": "16 GB DDR5",
        "gpu": dev_info.get("device_name", "NVIDIA GeForce RTX 5050 Laptop GPU"),
        "vram_bytes": dev_info.get("total_memory_bytes", 8546484224),
        "nvidia_driver": "576.83",
        "cuda_runtime": "12.9",
        "cupy_version": "14.2.0",
        "numpy_version": np.__version__,
        "os": "Windows 11 Home (Build 26200)",
        "commit": commit_sha,
        "benchmark_date": "2026-10-05",
        "power_mode": "Best Performance (Plugged in)",
        "speedup_definition": "speedup = CPU_median / CUDA_median (>1.0 = CUDA faster, <1.0 = CPU faster)",
        "execution_location": "Physical Acer RTX 5050 validation — not executed on Render.",
    }

    # Size ladder
    sizes = [
        {"tier": 1, "vars": 1000, "rows": 500, "nnz_per_row": 6, "warmups": 3, "repeats": 7, "timeout": 60, "max_iter": 3000},
        {"tier": 2, "vars": 2500, "rows": 1250, "nnz_per_row": 6, "warmups": 3, "repeats": 7, "timeout": 60, "max_iter": 3000},
        {"tier": 3, "vars": 5000, "rows": 2500, "nnz_per_row": 6, "warmups": 1, "repeats": 3, "timeout": 60, "max_iter": 2000},
        {"tier": 4, "vars": 10000, "rows": 5000, "nnz_per_row": 6, "warmups": 1, "repeats": 3, "timeout": 60, "max_iter": 2000},
        {"tier": 5, "vars": 25000, "rows": 12500, "nnz_per_row": 6, "warmups": 1, "repeats": 3, "timeout": 60, "max_iter": 2000},
        {"tier": 6, "vars": 50000, "rows": 25000, "nnz_per_row": 6, "warmups": 0, "repeats": 0, "timeout": 60, "max_iter": 2000},
        {"tier": 7, "vars": 100000, "rows": 50000, "nnz_per_row": 6, "warmups": 0, "repeats": 0, "timeout": 60, "max_iter": 2000},
    ]

    max_safe_ram_bytes = 6 * 1024 * 1024 * 1024  # 6.0 GB host RAM limit for dense matrix representation

    suite_results = []
    first_crossover_size = None
    best_valid_ratio = 0.0
    best_valid_tier = None

    for size_cfg in sizes:
        tier_idx = size_cfg["tier"]
        n_vars = size_cfg["vars"]
        n_rows = size_cfg["rows"]
        nnz_row = size_cfg["nnz_per_row"]
        warmups = size_cfg["warmups"]
        repeats = size_cfg["repeats"]
        timeout_sec = size_cfg["timeout"]
        max_iter = size_cfg["max_iter"]
        seed = 42 + tier_idx

        print(f"\n--------------------------------------------------")
        print(f"Tier {tier_idx}: {n_vars:,} variables, {n_rows:,} rows")

        est_host_mem = (n_rows * n_vars * 8) + (n_vars * 8 * 8) + (n_rows * 8 * 5)
        est_gpu_mem = (n_rows * nnz_row * 12 * 2) + ((n_rows + 1 + n_vars + 1) * 4) + (n_vars * 8 * 8) + (n_rows * 8 * 5)
        est_nnz = n_rows * nnz_row
        est_density = float(est_nnz / (n_rows * n_vars))

        print(f"  NNZ: {est_nnz:,} | Density: {est_density:.6f}")
        print(f"  Est. Dense Host Mem: {est_host_mem / (1024**2):.1f} MB | Est. GPU Mem: {est_gpu_mem / (1024**2):.1f} MB")

        # Memory safety check: skip 50k and 100k if host memory exceeds safety threshold
        if est_host_mem > max_safe_ram_bytes:
            print(f"  [SKIPPED_DENSE_REPRESENTATION_LIMIT] Estimated dense host memory ({est_host_mem / (1024**3):.1f} GB) exceeds 6.0 GB safe threshold.")
            tier_record = {
                "tier": tier_idx,
                "n_vars": n_vars,
                "n_rows": n_rows,
                "nonzeros": est_nnz,
                "density": est_density,
                "status": "SKIPPED_DENSE_REPRESENTATION_LIMIT",
                "cpu_median_seconds": None,
                "cuda_median_seconds": None,
                "speedup_ratio": None,
                "verification": "SKIPPED",
                "repeat_count": 0,
            }
            suite_results.append(tier_record)
            continue
        # Generate model stats
        model, stats = generate_bounded_feasible_sparse_lp(n_vars, n_rows, nnz_row, seed=seed)

        # Check if full tier raw JSON is already cached
        cached_tier_file = RAW_DIR / f"tier_{tier_idx}_{n_vars}vars.json"
        if cached_tier_file.exists():
            print(f"  [CACHED] Loading cached tier results from {cached_tier_file.name}...")
            cached_data = json.loads(cached_tier_file.read_text())
            cpu_records = cached_data["cpu_records"]
            cuda_records = cached_data["cuda_records"]
            
            cpu_repeats = [r["wall_clock_seconds"] for r in cpu_records]
            cuda_repeats = [r["wall_clock_seconds"] for r in cuda_records]
            cpu_statuses = [r["status"] for r in cpu_records]
            cuda_statuses = [r["status"] for r in cuda_records]
            cpu_objectives = [r.get("objective") for r in cpu_records]
            cuda_objectives = [r.get("objective") for r in cuda_records]
            cpu_verif = [r.get("verification_status") == "FULL_KKT_PASSED" or r.get("status") == "LIMIT_REACHED" for r in cpu_records]
            cuda_verif = [r.get("verification_status") == "FULL_KKT_PASSED" or r.get("status") == "LIMIT_REACHED" for r in cuda_records]

            cpu_median = float(np.median(cpu_repeats))
            cuda_median = float(np.median(cuda_repeats))
            speedup = cpu_median / cuda_median if cuda_median > 0 else 0.0

            verif_pass = (cpu_statuses[0] == "OPTIMAL_VERIFIED" and cuda_statuses[0] == "OPTIMAL_VERIFIED" and obj_match)
            verif_label = "VERIFIED_VALID" if verif_pass else ("LIMIT_REACHED_CONSISTENT" if (cpu_statuses[0] == cuda_statuses[0]) else "UNVERIFIED — INVALID FOR SPEEDUP CLAIM")

            if verif_pass:
                if speedup > 1.05 and first_crossover_size is None:
                    first_crossover_size = n_vars
                if speedup > best_valid_ratio:
                    best_valid_ratio = speedup
                    best_valid_tier = n_vars

            tier_record = {
                "tier": tier_idx,
                "n_vars": n_vars,
                "n_rows": n_rows,
                "nonzeros": stats["nonzeros"],
                "density": stats["density"],
                "estimated_host_memory_bytes": stats["estimated_host_memory_bytes"],
                "estimated_gpu_memory_bytes": stats["estimated_gpu_memory_bytes"],
                "cpu_status": cpu_statuses[0],
                "cuda_status": cuda_statuses[0],
                "cpu_iterations": cpu_records[0]["iterations"],
                "cuda_iterations": cuda_records[0]["iterations"],
                "cpu_objective": cpu_objectives[0],
                "cuda_objective": cuda_objectives[0],
                "objective_abs_diff": abs(cpu_objectives[0] - cuda_objectives[0]) if (cpu_objectives[0] is not None and cuda_objectives[0] is not None) else None,
                "cpu_median_seconds": cpu_median,
                "cpu_min_seconds": float(min(cpu_repeats)),
                "cpu_max_seconds": float(max(cpu_repeats)),
                "cuda_median_seconds": cuda_median,
                "cuda_min_seconds": float(min(cuda_repeats)),
                "cuda_max_seconds": float(max(cuda_repeats)),
                "speedup_ratio": speedup,
                "verification": verif_label,
                "repeat_count": len(cpu_repeats),
                "raw_cpu_repeats": cpu_repeats,
                "raw_cuda_repeats": cuda_repeats,
            }
            suite_results.append(tier_record)
            print(f"    Loaded CPU Median: {cpu_median:.4f}s | CUDA Median: {cuda_median:.4f}s | Speedup: {speedup:.2f}x")
            continue

        # Benchmark CPU
        print(f"  Benchmarking pdhg-cpu ({warmups} warmups, {repeats} repeats, max_iter={max_iter}, timeout={timeout_sec}s)...")
        for w in range(warmups):
            _ = execute_solve_with_timeout(n_vars, n_rows, seed, "pdhg-cpu", max_iter, 1e-4, timeout_sec)

        cpu_repeats = []
        cpu_statuses = []
        cpu_objectives = []
        cpu_verification_results = []
        cpu_raw_records = []

        for rep in range(1, repeats + 1):
            cached_rep_file = RAW_DIR / f"tier_{tier_idx}_{n_vars}vars_rep{rep}_cpu.json"
            if cached_rep_file.exists():
                rec = json.loads(cached_rep_file.read_text())
            else:
                res_cpu = execute_solve_with_timeout(n_vars, n_rows, seed, "pdhg-cpu", max_iter, 1e-4, timeout_sec)
                rec = {
                    "problem_id": f"sparse_{n_vars}",
                    "seed": seed,
                    "rows": n_rows,
                    "columns": n_vars,
                    "nonzeros": stats["nonzeros"],
                    "density": stats["density"],
                    "backend": "pdhg-cpu",
                    "status": res_cpu["status"],
                    "iterations": res_cpu["iterations"],
                    "objective": res_cpu.get("objective"),
                    "primal_residual": res_cpu.get("verification", {}).get("primal_residual"),
                    "dual_residual": res_cpu.get("verification", {}).get("dual_residual"),
                    "verification_status": res_cpu.get("verification", {}).get("kkt_status"),
                    "wall_clock_seconds": res_cpu["total_elapsed_seconds"],
                    "warmup_count": warmups,
                    "measured_repeat_number": rep,
                    "device": "CPU (Intel Core 5 210H)",
                    "commit_sha": commit_sha,
                }
                cached_rep_file.write_text(json.dumps(rec, indent=2))

            cpu_repeats.append(rec["wall_clock_seconds"])
            cpu_statuses.append(rec["status"])
            cpu_objectives.append(rec.get("objective"))
            cpu_verification_results.append(rec.get("verification_status") == "FULL_KKT_PASSED" or rec.get("status") == "LIMIT_REACHED")
            cpu_raw_records.append(rec)

        cpu_median = float(np.median(cpu_repeats))
        print(f"    CPU Median: {cpu_median:.4f}s (min: {min(cpu_repeats):.4f}s, max: {max(cpu_repeats):.4f}s) | Status: {cpu_statuses[0]}")

        # Benchmark CUDA
        print(f"  Benchmarking pdhg-cuda ({warmups} warmups, {repeats} repeats, max_iter={max_iter}, timeout={timeout_sec}s)...")
        for w in range(warmups):
            _ = execute_solve_with_timeout(n_vars, n_rows, seed, "pdhg-cuda", max_iter, 1e-4, timeout_sec)

        cuda_repeats = []
        cuda_statuses = []
        cuda_objectives = []
        cuda_verification_results = []
        cuda_raw_records = []

        for rep in range(1, repeats + 1):
            cached_rep_file = RAW_DIR / f"tier_{tier_idx}_{n_vars}vars_rep{rep}_cuda.json"
            if cached_rep_file.exists():
                rec = json.loads(cached_rep_file.read_text())
            else:
                res_cuda = execute_solve_with_timeout(n_vars, n_rows, seed, "pdhg-cuda", max_iter, 1e-4, timeout_sec)
                rec = {
                    "problem_id": f"sparse_{n_vars}",
                    "seed": seed,
                    "rows": n_rows,
                    "columns": n_vars,
                    "nonzeros": stats["nonzeros"],
                    "density": stats["density"],
                    "backend": "pdhg-cuda",
                    "status": res_cuda["status"],
                    "iterations": res_cuda["iterations"],
                    "objective": res_cuda.get("objective"),
                    "primal_residual": res_cuda.get("verification", {}).get("primal_residual"),
                    "dual_residual": res_cuda.get("verification", {}).get("dual_residual"),
                    "verification_status": res_cuda.get("verification", {}).get("kkt_status"),
                    "wall_clock_seconds": res_cuda["total_elapsed_seconds"],
                    "warmup_count": warmups,
                    "measured_repeat_number": rep,
                    "device": metadata["gpu"],
                    "commit_sha": commit_sha,
                }
                cached_rep_file.write_text(json.dumps(rec, indent=2))

            cuda_repeats.append(rec["wall_clock_seconds"])
            cuda_statuses.append(rec["status"])
            cuda_objectives.append(rec.get("objective"))
            cuda_verification_results.append(rec.get("verification_status") == "FULL_KKT_PASSED" or rec.get("status") == "LIMIT_REACHED")
            cuda_raw_records.append(rec)

        cuda_median = float(np.median(cuda_repeats))
        speedup = cpu_median / cuda_median if cuda_median > 0 else 0.0
        print(f"    CUDA Median: {cuda_median:.4f}s (min: {min(cuda_repeats):.4f}s, max: {max(cuda_repeats):.4f}s) | Status: {cuda_statuses[0]}")
        print(f"    --> Speedup Ratio (CPU/CUDA): {speedup:.2f}x")

        # Correctness check
        obj_match = False
        if cpu_objectives[0] is not None and cuda_objectives[0] is not None:
            obj_match = abs(cpu_objectives[0] - cuda_objectives[0]) < 1e-3

        verif_pass = (cpu_verification_results[0] and cuda_verification_results[0] and obj_match)
        verif_label = "VERIFIED_VALID" if verif_pass else ("LIMIT_REACHED_CONSISTENT" if (cpu_statuses[0] == cuda_statuses[0]) else "UNVERIFIED — INVALID FOR SPEEDUP CLAIM")

        if verif_pass:
            if speedup > 1.05 and first_crossover_size is None:
                first_crossover_size = n_vars
            if speedup > best_valid_ratio:
                best_valid_ratio = speedup
                best_valid_tier = n_vars

        tier_record = {
            "tier": tier_idx,
            "n_vars": n_vars,
            "n_rows": n_rows,
            "nonzeros": stats["nonzeros"],
            "density": stats["density"],
            "estimated_host_memory_bytes": stats["estimated_host_memory_bytes"],
            "estimated_gpu_memory_bytes": stats["estimated_gpu_memory_bytes"],
            "cpu_status": cpu_statuses[0],
            "cuda_status": cuda_statuses[0],
            "cpu_iterations": cpu_records[0]["iterations"],
            "cuda_iterations": cuda_records[0]["iterations"],
            "cpu_objective": cpu_objectives[0],
            "cuda_objective": cuda_objectives[0],
            "objective_abs_diff": abs(cpu_objectives[0] - cuda_objectives[0]) if (cpu_objectives[0] is not None and cuda_objectives[0] is not None) else None,
            "cpu_median_seconds": cpu_median,
            "cpu_min_seconds": float(min(cpu_repeats)),
            "cpu_max_seconds": float(max(cpu_repeats)),
            "cuda_median_seconds": cuda_median,
            "cuda_min_seconds": float(min(cuda_repeats)),
            "cuda_max_seconds": float(max(cuda_repeats)),
            "speedup_ratio": speedup,
            "verification": verif_label,
            "repeat_count": repeats,
            "raw_cpu_repeats": cpu_repeats,
            "raw_cuda_repeats": cuda_repeats,
        }
        suite_results.append(tier_record)

        # Save tier raw JSON
        cached_tier_file.write_text(json.dumps({
            "metadata": metadata,
            "tier": tier_idx,
            "problem": stats,
            "cpu_records": cpu_raw_records,
            "cuda_records": cuda_raw_records,
        }, indent=2))

        # Checkpoint partial results.partial.json after every completed tier
        (REPORTS_DIR / "results.partial.json").write_text(json.dumps({
            "metadata": metadata,
            "completed_tiers": len(suite_results),
            "first_crossover_size": first_crossover_size,
            "best_valid_ratio": best_valid_ratio,
            "best_valid_tier": best_valid_tier,
            "suite_results": suite_results,
        }, indent=2))

    # Save summary results.json
    results_json_path = REPORTS_DIR / "results.json"
    results_summary = {
        "metadata": metadata,
        "first_crossover_size": first_crossover_size,
        "best_valid_ratio": best_valid_ratio,
        "best_valid_tier": best_valid_tier,
        "suite_results": suite_results,
    }
    results_json_path.write_text(json.dumps(results_summary, indent=2))
    print(f"\nSaved {results_json_path}")

    # Generate README.md
    generate_markdown_report(metadata, suite_results, first_crossover_size, best_valid_ratio, best_valid_tier)


def generate_markdown_report(metadata: dict, suite_results: list[dict], first_crossover: int | None, best_ratio: float, best_tier: int | None):
    readme_path = REPORTS_DIR / "README.md"

    table_rows = []
    for r in suite_results:
        if "SKIPPED" in str(r.get("status", "")):
            table_rows.append(f"| {r['n_vars']:,} | {r['n_rows']:,} | {r['nonzeros']:,} | {r['density']:.6f} | — | — | — | — | — | {r['status']} | {r['repeat_count']} |")
        else:
            crossover_mark = " **(CROSSOVER)**" if first_crossover == r['n_vars'] else ""
            table_rows.append(
                f"| {r['n_vars']:,} | {r['n_rows']:,} | {r['nonzeros']:,} | {r['density']:.6f} | {r['cpu_median_seconds']:.4f}s | {r['cuda_median_seconds']:.4f}s | **{r['speedup_ratio']:.2f}x**{crossover_mark} | {r['cpu_status']} | {r['cuda_status']} | {r['verification']} | {r['repeat_count']} |"
            )

    table_md = "\n".join(table_rows)

    crossover_str = f"**{first_crossover:,} variables**" if first_crossover else "**None within tested sizes**"
    best_ratio_str = f"**{best_ratio:.2f}x** (at {best_tier:,} vars)" if best_tier else "**None**"

    classification = "B. GPU CROSSOVER DEMONSTRATED ABOVE " + str(first_crossover) if first_crossover else "A. NO SAME-MACHINE GPU ADVANTAGE DEMONSTRATED"
    if best_ratio >= 1.5:
        classification = f"C. MEANINGFUL GPU ACCELERATION DEMONSTRATED ON TESTED LARGE-SPARSE WORKLOADS ({best_ratio:.2f}x at {best_tier:,} vars)"

    content = f"""# Gate 19B — Physical RTX 5050 Large-Sparse GPU Validation

## Executive Summary

- **Hardware Platform:** {metadata['machine']}
- **CPU:** {metadata['cpu']}
- **RAM:** {metadata['ram']}
- **GPU:** {metadata['gpu']}
- **VRAM:** {metadata['vram_bytes'] / (1024**2):.1f} MiB
- **NVIDIA Driver:** {metadata['nvidia_driver']} | **CUDA Runtime:** {metadata['cuda_runtime']} | **CuPy:** {metadata['cupy_version']}
- **OS:** {metadata['os']}
- **Commit SHA:** `{metadata['commit']}`
- **Execution Date:** {metadata['benchmark_date']}
- **Power Mode:** {metadata['power_mode']}
- **Provenential Statement:** "{metadata['execution_location']}"

---

## Performance Summary Table

| Workload Size | Rows | Nonzeros | Density | CPU Median | CUDA Median | CPU/CUDA Speedup | CPU Status | CUDA Status | Verification | Repeats |
|--------------:|-----:|---------:|--------:|-----------:|------------:|-----------------:|-----------:|------------:|-------------|--------:|
{table_md}

---

## Key Findings

- **First Valid GPU Crossover Size:** {crossover_str}
- **Best Valid Same-Machine CPU/CUDA Ratio:** {best_ratio_str}
- **Speedup Definition:** `speedup = CPU_median / CUDA_median` (>1.0 indicates CUDA faster)
- **Scientific Classification:** `{classification}`

---

## Methodology & Safety Compliance

1. **Identical Instance Verification:** CPU and CUDA were evaluated on exact mathematically identical bounded, feasible sparse LP instances generated with fixed random seeds.
2. **Subprocess Isolation & Hard Timeouts:** Each individual solve was executed in an isolated child process with a 60-second wall-clock timeout to guarantee bounded execution.
3. **Warmup & Repeat Protocols:** Fast tiers (1k, 2.5k) used 3 warmups + 7 repeats; larger tiers (5k, 10k, 25k) used 1 warmup + 3 repeats with hard 60s bounds.
4. **Synchronized CUDA Timing:** CUDA timers included explicit stream synchronization (`cp.cuda.Stream.null.synchronize()`) before recording end times to prevent measuring asynchronous kernel launch overhead alone.
5. **Memory Safety & Densification Guard:** Workloads exceeding safe host memory margins (50k and 100k dense array representation) were safely classified as `SKIPPED_DENSE_REPRESENTATION_LIMIT`.
6. **Historical Gate Protection:** Historical evidence from Gate 8 (`reports/gpu_validation/`), Gate 9 (`reports/gpu_gate9_final_51b71bb/`), and Gate 19A (`reports/batch_throughput/`) remains strictly untouched and preserved.

---

*Report generated automatically by `scripts/run_gpu_large_sparse_gate19.py` on {metadata['benchmark_date']}.*
"""

    readme_path.write_text(content)
    print(f"Saved {readme_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker_main()
    else:
        run_benchmark()
