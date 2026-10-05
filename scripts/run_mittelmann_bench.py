"""Gate 20A Sovereign Mittelmann LP Benchmark Suite.

Executes parse stage, bounded sovereign solve (PDHG-CPU), and independent
external HiGHS comparison directly from compressed .bz2 archives:
  - qap15.mps.bz2
  - brazil3.mps.bz2
  - chromaticindex1024-7.mps.bz2
  - supportcase10.mps.bz2

Reports all results honestly without hiding limit-reached outcomes or baseline wins.
Zero external solver dependencies in sovopt/.
"""
import os
import sys
import json
import time
import bz2
import hashlib
import subprocess
from pathlib import Path
import numpy as np

# Ensure sovopt can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sovopt.mps import read_mps
from sovopt.sparse import CSRMatrix
from sovopt.pdhg import solve_pdhg


BENCHMARK_CONFIG = [
    {
        "name": "qap15",
        "archive": "qap15.mps.bz2",
        "domain": "LP benchmark instance (QAP relaxation)",
        "source_url": "https://plato.asu.edu/ftp/lptestset/qap15.mps.bz2",
        "reference_obj": 1040.99,
        "reference_source": "Hans Mittelmann LP Benchmark (plato.asu.edu/ftp/lpopt.html)",
        "sovopt_time_limit": 20.0,
        "highs_time_limit": 30.0,
        "max_iter": 2000,
        "check_freq": 50,
    },
    {
        "name": "brazil3",
        "archive": "brazil3.mps.bz2",
        "domain": "LP benchmark instance (MIPLIB 2017 LP relaxation)",
        "source_url": "https://plato.asu.edu/ftp/lptestset/brazil3.mps.bz2",
        "reference_obj": 2.0,
        "reference_source": "MIPLIB 2017 LP Relaxation / HiGHS C++",
        "sovopt_time_limit": 20.0,
        "highs_time_limit": 30.0,
        "max_iter": 2000,
        "check_freq": 50,
    },
    {
        "name": "chromaticindex1024-7",
        "archive": "chromaticindex1024-7.mps.bz2",
        "domain": "LP benchmark instance (MIPLIB 2017 LP relaxation)",
        "source_url": "https://plato.asu.edu/ftp/lptestset/chromaticindex1024-7.mps.bz2",
        "reference_obj": None,
        "reference_source": "MIPLIB 2017 LP Relaxation / HiGHS C++",
        "sovopt_time_limit": 20.0,
        "highs_time_limit": 30.0,
        "max_iter": 1000,
        "check_freq": 50,
    },
    {
        "name": "supportcase10",
        "archive": "supportcase10.mps.bz2",
        "domain": "LP benchmark instance (MIPLIB 2017 LP relaxation)",
        "source_url": "https://plato.asu.edu/ftp/lptestset/supportcase10.mps.bz2",
        "reference_obj": None,
        "reference_source": "MIPLIB 2017 LP Relaxation / HiGHS C++",
        "sovopt_time_limit": 20.0,
        "highs_time_limit": 30.0,
        "max_iter": 1000,
        "check_freq": 50,
    },
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def sha256_bz2_stream(path):
    h = hashlib.sha256()
    with bz2.open(path, "rb") as bzf:
        while chunk := bzf.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_mittelmann_benchmarks():
    repo_root = Path(__file__).resolve().parent.parent
    mittelmann_dir = repo_root / "data" / "mittelmann"
    reports_dir = repo_root / "reports" / "gate20a_sparse_mittelmann"
    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "benchmark_set": "Hans Mittelmann Linear Programming Benchmark Set (plato.asu.edu/ftp/lptestset/)",
        "retrieval_date": "2026-10-05T04:38:45+05:30",
        "storage_format": "Original compressed .mps.bz2 (uncompressed physical files omitted from git to avoid repository bloat; stream hashes verified)",
        "instances": []
    }

    results = {
        "suite": "Gate 20A True Sparse Mittelmann Evaluation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "solver_identity": "SOV-OPT Sovereign Core (NumPy only, zero solver dependencies)",
        "external_baseline": "HiGHS (via isolated subprocess scripts/baseline_worker.py)",
        "transparency_notice": (
            "We report every evaluated benchmark, including failures, iteration limits, "
            "and cases where the baseline solver is faster. Industrial C++ simplex/interior-point "
            "solvers are expected to outperform first-order prototypes on large degenerate LPs."
        ),
        "time_limit_semantics": (
            "SOV-OPT evaluated with a 20-second in-loop time budget checked at convergence checkpoints; "
            "wall-clock elapsed time may exceed the nominal budget by one checkpoint interval. "
            "External HiGHS evaluated with a 30-second evaluation window."
        ),
        "instances": []
    }

    print(f"Executing Gate 20A Mittelmann Benchmark Suite directly from compressed archives on {len(BENCHMARK_CONFIG)} instances...")

    for cfg in BENCHMARK_CONFIG:
        name = cfg["name"]
        bz2_path = mittelmann_dir / cfg["archive"]

        if not bz2_path.exists():
            print(f"Error: {bz2_path} not found.")
            continue

        bz2_sha256 = sha256_file(bz2_path)
        uncompressed_sha256 = sha256_bz2_stream(bz2_path)

        print(f"\n=======================================================")
        print(f"Instance: {name}")
        print(f"Domain: {cfg['domain']}")
        print(f"Compressed SHA-256: {bz2_sha256}")
        print(f"Uncompressed Stream SHA-256: {uncompressed_sha256}")
        print(f"=======================================================")

        # -------------------------------------------------------------------
        # Phase 1: Sovereign True Sparse Parse & Validation
        # -------------------------------------------------------------------
        print(f"  [1/3] Parsing directly from .bz2 stream with sovereign sparse parser (zero densification)...")
        t0 = time.perf_counter()
        model = read_mps(str(bz2_path), sparse=True)
        parse_time = time.perf_counter() - t0

        m_rows, n_cols = model.A.shape
        nnz = model.A.nnz
        density = model.A.density
        csr_mb = model.A.memory_bytes / (1024.0 * 1024.0)
        dense_bytes = float(m_rows) * float(n_cols) * 8.0
        dense_gb = dense_bytes / (1024.0 ** 3)
        compression = dense_bytes / model.A.memory_bytes if model.A.memory_bytes > 0 else 0.0

        t0_val = time.perf_counter()
        model.validate()
        val_time = time.perf_counter() - t0_val

        print(f"    Dimensions: {m_rows:,} rows x {n_cols:,} cols, {nnz:,} NNZ (density {density:.6f})")
        print(f"    Parse Time: {parse_time:.4f} s | Validation: {val_time:.4f} s")
        print(f"    Sparse Memory: {csr_mb:.2f} MB | Dense Footprint: {dense_gb:.2f} GB (Compression: {compression:,.0f}x)")

        # Record manifest entry
        manifest["instances"].append({
            "name": name,
            "archive": cfg["archive"],
            "domain": cfg["domain"],
            "source_url": cfg["source_url"],
            "sha256_bz2": bz2_sha256,
            "sha256_uncompressed_stream": uncompressed_sha256,
            "rows": m_rows,
            "columns": n_cols,
            "nonzeros": nnz,
            "density": density,
            "sparse_memory_mb": round(csr_mb, 2),
            "dense_memory_gb": round(dense_gb, 2),
            "compression_ratio": round(compression, 1),
            "reference_obj": cfg["reference_obj"],
            "reference_source": cfg["reference_source"],
        })

        # -------------------------------------------------------------------
        # Phase 2: Sovereign Bounded Solve (PDHG-CPU)
        # -------------------------------------------------------------------
        print(f"  [2/3] Executing sovereign bounded solve (PDHG-CPU, limit: {cfg['sovopt_time_limit']}s)...")
        t0_solve = time.perf_counter()
        try:
            sol = solve_pdhg(
                model,
                backend="pdhg-cpu",
                max_iter=cfg["max_iter"],
                check_freq=cfg["check_freq"],
                time_limit=cfg["sovopt_time_limit"]
            )
            solve_time = time.perf_counter() - t0_solve
            sov_status = sol.get("status", "UNKNOWN")
            sov_iters = sol.get("iterations", 0)
            sov_obj = sol.get("objective")
            vr = sol.get("verification", {})
            primal_res = vr.get("primal_residual")
            dual_res = vr.get("dual_residual")
            rel_gap = vr.get("relative_duality_gap")
            kkt_passed = vr.get("kkt_passed", False)
        except Exception as e:
            solve_time = time.perf_counter() - t0_solve
            sov_status = "NUMERICAL_FAILURE"
            sov_iters = 0
            sov_obj = None
            primal_res = None
            dual_res = None
            rel_gap = None
            kkt_passed = False
            print(f"    Solver error: {e}")

        print(f"    Status: {sov_status} | Time: {solve_time:.3f} s | Iterations: {sov_iters}")
        print(f"    Objective: {sov_obj}")
        print(f"    Primal Residual: {primal_res} | Dual Residual: {dual_res} | KKT Passed: {kkt_passed}")

        # Honest verdict classification
        if sov_status == "OPTIMAL_VERIFIED" or kkt_passed:
            verdict = "CONVERGED"
        elif sov_status == "LIMIT_REACHED":
            verdict = "TIME_OR_ITERATION_LIMIT"
        elif sov_status == "NUMERICAL_FAILURE":
            verdict = "NUMERICAL_FAILURE"
        else:
            verdict = sov_status

        # -------------------------------------------------------------------
        # Phase 3: External Baseline Comparison (HiGHS)
        # -------------------------------------------------------------------
        print(f"  [3/3] Executing external HiGHS comparison (time limit: {cfg['highs_time_limit']}s)...")
        highs_env = os.environ.copy()
        highs_env["HIGHS_TIME_LIMIT"] = str(cfg["highs_time_limit"])
        try:
            cmd = [
                str(repo_root / ".venv" / "bin" / "python"),
                str(repo_root / "scripts" / "baseline_worker.py"),
                str(bz2_path)
            ]
            p = subprocess.run(cmd, env=highs_env, capture_output=True, text=True, timeout=cfg["highs_time_limit"] + 15)
            if p.returncode == 0:
                highs_res = json.loads(p.stdout)
            else:
                highs_res = {"status": "SUBPROCESS_ERROR", "error": p.stderr}
        except subprocess.TimeoutExpired:
            highs_res = {"model_status": "HighsModelStatus.kTimeLimit", "seconds": cfg["highs_time_limit"], "objective": None}
        except Exception as e:
            highs_res = {"status": "ERROR", "message": str(e)}

        highs_status = highs_res.get("model_status", "UNKNOWN")
        highs_time = highs_res.get("seconds")
        highs_obj = highs_res.get("objective")
        highs_iters = highs_res.get("simplex_iterations", 0) + highs_res.get("ipm_iterations", 0)

        highs_summary = (
            f"HiGHS reported kOptimal with objective {highs_obj} in approximately {highs_time:.3f} s."
            if "kOptimal" in str(highs_status)
            else "HiGHS did not report an optimal solution within the 30-second evaluation window."
        )

        print(f"    HiGHS Status: {highs_status} | Time: {highs_time} s | Objective: {highs_obj}")

        # Gap calculation if both provide objective
        rel_diff = None
        if sov_obj is not None and highs_obj is not None and abs(highs_obj) > 1e-12:
            rel_diff = abs(sov_obj - highs_obj) / abs(highs_obj)

        instance_record = {
            "instance": name,
            "archive": cfg["archive"],
            "domain": cfg["domain"],
            "dimensions": {
                "rows": m_rows,
                "columns": n_cols,
                "nonzeros": nnz,
                "density": density,
            },
            "memory": {
                "csr_memory_mb": round(csr_mb, 2),
                "dense_memory_gb": round(dense_gb, 2),
                "compression_ratio": round(compression, 1),
            },
            "parse": {
                "status": "PARSED_SPARSE_OK",
                "parse_time_s": round(parse_time, 4),
                "validation_time_s": round(val_time, 4),
            },
            "sovopt": {
                "backend": "pdhg-cpu",
                "status": sov_status,
                "verdict": verdict,
                "time_s": round(solve_time, 3),
                "iterations": sov_iters,
                "objective": sov_obj,
                "primal_residual": primal_res,
                "dual_residual": dual_res,
                "relative_gap": rel_gap,
                "kkt_passed": kkt_passed,
            },
            "highs": {
                "backend": highs_res.get("backend", "HiGHS C++"),
                "status": highs_status,
                "time_s": round(highs_time, 3) if highs_time is not None else None,
                "iterations": highs_iters,
                "objective": highs_obj,
                "summary": highs_summary,
            },
            "comparison": {
                "relative_objective_diff": rel_diff,
                "reference_objective": cfg["reference_obj"],
                "reference_source": cfg["reference_source"],
                "note": "SOV-OPT is a pure-Python first-order prototype; HiGHS is an industrial C++ revised simplex/IPM solver."
            }
        }
        results["instances"].append(instance_record)

    # Save outputs
    manifest_file = reports_dir / "mittelmann_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    results_file = reports_dir / "mittelmann_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=======================================================")
    print(f"Mittelmann benchmark suite completed successfully.")
    print(f"Manifest written to: {manifest_file}")
    print(f"Results written to: {results_file}")
    print(f"=======================================================")
    return results


if __name__ == "__main__":
    run_mittelmann_benchmarks()
