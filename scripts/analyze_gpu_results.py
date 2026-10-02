import json
from pathlib import Path

evidence_dir = Path("reports/gpu_validation/rtx5050_2026-10-02_c5788513")
env = json.loads((evidence_dir / "environment.json").read_text())
preflight = json.loads((evidence_dir / "preflight.json").read_text())
cpu = json.loads((evidence_dir / "validation_cpu.json").read_text())
cuda = json.loads((evidence_dir / "validation_cuda.json").read_text())

print("=== HARDWARE & ENVIRONMENT ===")
print(f"GPU: {env['gpu']['name']} ({env['gpu']['vram_total_gb']} GB VRAM, CC {env['gpu']['compute_capability']})")
print(f"Driver: {env['gpu']['driver_version']}, CUDA: {env['gpu']['cuda_runtime_version']}")
print(f"Power State: {env['power_source']}")
print(f"Git SHA: {env['git_sha']}")
print(f"Preflight Status: {preflight['status']}, Micro SpMV Discrepancy: {preflight['micro_spmv_test']['max_discrepancy']:.2e}")

print("\n=== INSTANCE PERFORMANCE SUMMARY ===")
print(f"{'Instance':<10} | {'Stratum':<7} | {'Status':<17} | {'CPU (ms)':<10} | {'CUDA (ms)':<10} | {'Speedup / Ratio':<15} | {'Obj Diff':<10}")
print("-" * 95)

cpu_results = cpu['results']
cuda_results = cuda['results']

strata_stats = {}

for name in cuda_results:
    res_cuda = cuda_results[name]
    res_cpu = cpu_results.get(name, {})
    
    stratum = res_cuda['stratum']
    status_cuda = res_cuda['status']
    status_cpu = res_cpu.get('status', 'N/A')
    
    t_cuda = res_cuda['median_elapsed_seconds'] * 1000
    t_cpu = res_cpu.get('median_elapsed_seconds', 0) * 1000
    
    # Speedup: T_cpu / T_cuda (or CUDA overhead ratio if < 1.0)
    speedup = t_cpu / t_cuda if t_cuda > 0 else 0
    
    obj_cuda = res_cuda.get('objective')
    obj_cpu = res_cpu.get('objective')
    obj_diff = abs(obj_cuda - obj_cpu) if (obj_cuda is not None and obj_cpu is not None) else 0.0
    
    if stratum not in strata_stats:
        strata_stats[stratum] = {'cpu_time': [], 'cuda_time': []}
    strata_stats[stratum]['cpu_time'].append(t_cpu)
    strata_stats[stratum]['cuda_time'].append(t_cuda)
    
    print(f"{name:<10} | {stratum:<7} | {status_cuda:<17} | {t_cpu:10.2f} | {t_cuda:10.2f} | {speedup:14.2f}x | {obj_diff:10.2e}")

print("\n=== STRATUM LEVEL SUMMARY ===")
for stratum, data in strata_stats.items():
    avg_cpu = sum(data['cpu_time']) / len(data['cpu_time'])
    avg_cuda = sum(data['cuda_time']) / len(data['cuda_time'])
    total_cpu = sum(data['cpu_time'])
    total_cuda = sum(data['cuda_time'])
    speedup = total_cpu / total_cuda if total_cuda > 0 else 0
    print(f"Stratum [{stratum}]: Total CPU = {total_cpu:.2f} ms, Total CUDA = {total_cuda:.2f} ms, Aggregate Ratio = {speedup:.2f}x")
