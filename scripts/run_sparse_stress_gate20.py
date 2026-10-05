"""Gate 20A Sovereign True Sparse Stress Representation Test.

Evaluates sovereign CSRMatrix construction, memory footprint, SpMV, SpMV-transpose,
and bounded PDHG steps across scales from 10K to 1M variables.
Zero external solver dependencies. Zero densification.
"""
import os
import sys
import json
import time
import resource
import numpy as np

# Ensure sovopt can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sovopt.sparse import CSRMatrix, csr_from_triplets
from sovopt.model import Model
from sovopt.pdhg import solve_pdhg


def get_process_memory_mb():
    try:
        # On macOS ru_maxrss is in bytes
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        return rusage.ru_maxrss / (1024 * 1024)
    except Exception:
        return 0.0


def run_sparse_stress():
    tiers = [
        {"name": "10K", "n_vars": 10000, "n_rows": 5000, "nnz_per_row": 5},
        {"name": "25K", "n_vars": 25000, "n_rows": 10000, "nnz_per_row": 5},
        {"name": "50K", "n_vars": 50000, "n_rows": 25000, "nnz_per_row": 5},
        {"name": "100K", "n_vars": 100000, "n_rows": 50000, "nnz_per_row": 5},
        {"name": "250K", "n_vars": 250000, "n_rows": 100000, "nnz_per_row": 5},
        {"name": "500K", "n_vars": 500000, "n_rows": 250000, "nnz_per_row": 5},
        {"name": "1M", "n_vars": 1000000, "n_rows": 500000, "nnz_per_row": 5},
    ]

    results = {
        "benchmark": "Gate 20A True Sparse Stress Representation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tiers": []
    }

    print(f"Starting Gate 20A Sparse Stress Benchmark across {len(tiers)} scales...")

    for t in tiers:
        n = t["n_vars"]
        m = t["n_rows"]
        k = t["nnz_per_row"]
        total_nnz = m * k
        dense_bytes = float(m) * float(n) * 8.0
        dense_gb = dense_bytes / (1024.0 ** 3)

        print(f"\n--- Tier {t['name']}: {m:,} rows x {n:,} cols, {total_nnz:,} NNZ ---")
        mem_before = get_process_memory_mb()

        # Step 1: Deterministic CSR generation without dense allocation
        t0 = time.perf_counter()
        indptr = np.arange(0, total_nnz + 1, k, dtype=np.int64)

        # Deterministically space columns across n
        # For speed on large sizes, construct in vectorized chunks
        step = max(1, n // k)
        row_offsets = np.arange(m, dtype=np.int64) % step
        cols = np.empty((m, k), dtype=np.int64)
        for col_idx in range(k):
            cols[:, col_idx] = col_idx * step + row_offsets
        indices = cols.ravel()
        data = np.ones(total_nnz, dtype=np.float64) * 1.5

        csr = CSRMatrix(m, n, indptr, indices, data, validate=True)
        t_construct = time.perf_counter() - t0

        sparse_bytes = csr.memory_bytes
        sparse_mb = sparse_bytes / (1024.0 * 1024.0)
        compression = dense_bytes / sparse_bytes if sparse_bytes > 0 else 0.0

        print(f"  Construction & Validation: {t_construct:.4f} s")
        print(f"  Sparse Memory: {sparse_mb:.2f} MB | Dense Would Require: {dense_gb:.2f} GB")
        print(f"  Compression Ratio: {compression:,.0f}x")

        # Step 2: Sovereign SpMV (y = A @ x)
        x = np.ones(n, dtype=np.float64)
        t0 = time.perf_counter()
        y = csr.dot(x)
        t_spmv = time.perf_counter() - t0
        spmv_valid = bool(np.all(np.isfinite(y)) and len(y) == m)
        print(f"  SpMV (A @ x): {t_spmv * 1000.0:.2f} ms (Valid: {spmv_valid})")

        # Step 3: Sovereign SpMV-transpose (x = A.T @ y)
        y_vec = np.ones(m, dtype=np.float64)
        t0 = time.perf_counter()
        x_res = csr.transpose_dot(y_vec)
        t_spmv_t = time.perf_counter() - t0
        spmv_t_valid = bool(np.all(np.isfinite(x_res)) and len(x_res) == n)
        print(f"  SpMV-T (A.T @ y): {t_spmv_t * 1000.0:.2f} ms (Valid: {spmv_t_valid})")

        # Step 4: Bounded PDHG step execution (for n <= 100K)
        pdhg_iterations = 0
        pdhg_time_s = None
        pdhg_ms_per_iter = None
        pdhg_status = None

        if n <= 100000:
            c = np.ones(n, dtype=np.float64)
            b_l = np.zeros(m, dtype=np.float64)
            b_u = np.full(m, 10.0, dtype=np.float64)
            l_bound = np.zeros(n, dtype=np.float64)
            u_bound = np.full(n, 5.0, dtype=np.float64)

            model = Model(c=c, A=csr, row_lower=b_l, row_upper=b_u, lower=l_bound, upper=u_bound)

            t0 = time.perf_counter()
            # Run 10 iterations of PDHG
            res = solve_pdhg(model, max_iter=10, check_freq=10)
            pdhg_time_s = time.perf_counter() - t0
            pdhg_iterations = res.get("iterations", 10)
            pdhg_ms_per_iter = (pdhg_time_s / pdhg_iterations) * 1000.0 if pdhg_iterations > 0 else 0.0
            pdhg_status = res.get("status")
            print(f"  PDHG 10 iterations: {pdhg_time_s:.4f} s ({pdhg_ms_per_iter:.2f} ms/iter, status: {pdhg_status})")
        else:
            print("  PDHG bounded step: Skipped (scale > 100K; SpMV verified)")

        mem_after = get_process_memory_mb()

        tier_record = {
            "tier": t["name"],
            "variables": n,
            "constraints": m,
            "nnz": total_nnz,
            "density": csr.density,
            "construction_time_s": t_construct,
            "sparse_memory_bytes": sparse_bytes,
            "sparse_memory_mb": sparse_mb,
            "dense_memory_bytes": int(dense_bytes),
            "dense_memory_gb": dense_gb,
            "compression_ratio": compression,
            "spmv_time_s": t_spmv,
            "spmv_ms": t_spmv * 1000.0,
            "spmv_valid": spmv_valid,
            "spmv_t_time_s": t_spmv_t,
            "spmv_t_ms": t_spmv_t * 1000.0,
            "spmv_t_valid": spmv_t_valid,
            "pdhg_iterations": pdhg_iterations,
            "pdhg_time_s": pdhg_time_s,
            "pdhg_ms_per_iter": pdhg_ms_per_iter,
            "pdhg_status": pdhg_status,
            "process_rss_mb": mem_after
        }
        results["tiers"].append(tier_record)

        # Free tier arrays
        del csr, indptr, indices, data, cols, x, y, y_vec, x_res

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "gate20a_sparse_mittelmann"))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "sparse_stress.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved stress benchmark results to {out_file}")
    return results


if __name__ == "__main__":
    run_sparse_stress()
