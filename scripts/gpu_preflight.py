#!/usr/bin/env python3
"""Preflight environment diagnostics for SOV-OPT GPU PDHG validation pipeline.

Inspects machine architecture, CUDA driver/runtime availability, device memory,
and verifies micro SpMV execution.
Enforces truthful reporting: on non-CUDA machines (e.g. Apple Silicon),
reports cuda_available=False and gpu_executed=False.
"""

import sys, os, json, platform, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sovopt.cuda_backend import is_cuda_available, get_device_info

def run_preflight(output_path=None):
    start = time.perf_counter()
    ts = datetime.now(timezone.utc).isoformat()
    dev_info = get_device_info()
    cuda_ok = dev_info.get("cuda_available", False)

    machine_meta = {
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
    }
    try:
        import numpy as np
        machine_meta["numpy"] = np.__version__
    except ImportError:
        machine_meta["numpy"] = None

    micro_test = None
    gpu_executed = False

    if cuda_ok:
        try:
            from sovopt.cuda_backend import CUDABackend
            backend = CUDABackend()
            # Micro benchmark: 1000x1000 matrix with 5000 nonzeros
            import numpy as np
            m, n, nnz = 1000, 1000, 5000
            np.random.seed(42)
            r = np.random.randint(0, m, nnz)
            j = np.random.randint(0, n, nnz)
            a = np.random.randn(nnz)
            p = np.r_[0, np.cumsum(np.bincount(r, minlength=m))]
            x = np.random.randn(n)

            csr = backend.build_csr(p, j, a, (m, n))
            x_dev = backend.asarray(x)
            backend.synchronize()

            t0 = time.perf_counter()
            for _ in range(50):
                out = csr.dot(x_dev)
            backend.synchronize()
            spmv_time = (time.perf_counter() - t0) / 50.0

            out_cpu = backend.to_cpu(out)
            ref_cpu = np.zeros(m)
            np.add.at(ref_cpu, r, a * x[j])
            max_err = float(np.max(np.abs(out_cpu - ref_cpu)))

            mem_stats = backend.get_memory_stats()
            gpu_executed = True
            micro_test = {
                "passed": max_err < 1e-12,
                "max_discrepancy": max_err,
                "avg_spmv_microseconds": spmv_time * 1e6,
                "memory_used_mb": mem_stats["used_bytes"] / (1024 * 1024),
            }
        except Exception as e:
            micro_test = {
                "passed": False,
                "error": str(e),
            }

    status_str = "NVIDIA_CUDA_READY" if (cuda_ok and micro_test and micro_test.get("passed")) else "CUDA_UNAVAILABLE"

    report = {
        "timestamp_utc": ts,
        "status": status_str,
        "cuda_available": cuda_ok,
        "gpu_executed": gpu_executed,
        "device_info": dev_info,
        "machine_metadata": machine_meta,
        "micro_spmv_test": micro_test,
        "elapsed_seconds": time.perf_counter() - start,
    }

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(report, indent=2) + "\n")

    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SOV-OPT GPU Preflight Environment Verification")
    parser.add_argument("--output", "-o", default=str(ROOT / "reports/gpu/preflight.json"), help="Output JSON path")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args()

    report = run_preflight(output_path=args.output)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print(" SOV-OPT GPU ENVIRONMENT PREFLIGHT")
        print("=" * 60)
        print(f" Timestamp (UTC)  : {report['timestamp_utc']}")
        print(f" System / Arch    : {report['machine_metadata']['system']} ({report['machine_metadata']['architecture']})")
        print(f" Python / NumPy   : {report['machine_metadata']['python']} / {report['machine_metadata']['numpy']}")
        print(f" CUDA Available   : {report['cuda_available']}")
        print(f" GPU Executed     : {report['gpu_executed']}")
        print(f" Preflight Status : {report['status']}")
        if report['cuda_available']:
            dev = report['device_info']
            print(f" GPU Device       : {dev.get('device_name')} (CC {dev.get('compute_capability')})")
            print(f" VRAM Total       : {dev.get('total_memory_bytes', 0) / (1024**3):.2f} GB")
            if report['micro_spmv_test']:
                print(f" Micro SpMV Test  : {'PASSED' if report['micro_spmv_test']['passed'] else 'FAILED'}")
                print(f" SpMV Latency     : {report['micro_spmv_test'].get('avg_spmv_microseconds', 0):.2f} us")
        else:
            print(" Host Diagnostics : No NVIDIA CUDA runtime detected (CPU-only execution).")
        print(f" Saved report to  : {args.output}")
        print("=" * 60)

if __name__ == "__main__":
    main()
