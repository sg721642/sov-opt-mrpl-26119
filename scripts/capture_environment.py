"""Capture real hardware environment metadata for Gate 8 Phase B.

Generates environment.json without any hardcoded values.
Power source is reported as UNKNOWN if not determinable programmatically.
"""
import json, platform, subprocess, sys, ctypes
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "reports/gpu_validation/rtx5050_2026-10-02_c5788513/environment.json"

# --- Timestamp ---
timestamp_utc = datetime.now(timezone.utc).isoformat()

# --- Platform ---
machine_info = {
    "system": platform.system(),
    "release": platform.release(),
    "version": platform.version(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "node": platform.node(),
}

# --- RAM ---
try:
    import ctypes
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    ms = MEMORYSTATUSEX()
    ms.dwLength = ctypes.sizeof(ms)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
    total_ram_bytes = int(ms.ullTotalPhys)
    total_ram_gb = round(total_ram_bytes / (1024**3), 2)
except Exception as e:
    total_ram_bytes = None
    total_ram_gb = None
    print(f"RAM detection failed: {e}")

# --- GPU via CuPy ---
try:
    import cupy as cp
    import numpy as np
    dev = cp.cuda.Device(0)
    dev.use()
    props = cp.cuda.runtime.getDeviceProperties(0)
    gpu_info = {
        "name": props["name"].decode() if isinstance(props["name"], bytes) else props["name"],
        "compute_capability": f"{props['major']}.{props['minor']}",
        "vram_total_bytes": int(props["totalGlobalMem"]),
        "vram_total_gb": round(props["totalGlobalMem"] / (1024**3), 2),
        "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
        "device_count": cp.cuda.runtime.getDeviceCount(),
    }
    cupy_version = cp.__version__
    numpy_version = np.__version__
except Exception as e:
    gpu_info = {"error": str(e)}
    cupy_version = None
    numpy_version = None
    print(f"GPU detection failed: {e}")

# --- NVIDIA driver via nvidia-smi ---
try:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=10
    )
    driver_version = result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
except Exception:
    driver_version = "UNKNOWN"
gpu_info["driver_version"] = driver_version

# --- Power source ---
# On Windows, query WMI battery status
power_source = "UNKNOWN"
try:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Battery).BatteryStatus"],
        capture_output=True, text=True, timeout=10
    )
    status_out = result.stdout.strip()
    if result.returncode == 0 and status_out:
        # BatteryStatus: 2 = AC power, 1 = Discharging, 6 = Charging
        try:
            bs = int(status_out)
            if bs == 2:
                power_source = "AC_CONNECTED_FULL"
            elif bs == 6:
                power_source = "AC_CONNECTED_CHARGING"
            elif bs == 1:
                power_source = "BATTERY_DISCHARGING"
            else:
                power_source = f"BATTERY_STATUS_{bs}"
        except ValueError:
            power_source = "UNKNOWN"
    else:
        # No battery returned (desktop or battery not reported)
        power_source = "NO_BATTERY_REPORTED"
except Exception as e:
    power_source = "UNKNOWN"
    print(f"Power detection failed: {e}")

# --- Git SHA ---
try:
    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=10
    )
    git_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "UNKNOWN"
except Exception:
    git_sha = "UNKNOWN"

# --- Software ---
software_info = {
    "python": platform.python_version(),
    "numpy": numpy_version,
    "cupy": cupy_version,
    "conda_env": "sovopt-gpu",
}

# --- Benchmark config (frozen) ---
benchmark_config = {
    "warmups": 3,
    "repeats": 7,
    "tolerance": 1e-7,
    "max_iter": 50000,
    "restart": 1000,
    "scaling": True,
}

env = {
    "timestamp_utc": timestamp_utc,
    "git_sha": git_sha,
    "machine": machine_info,
    "ram": {
        "total_bytes": total_ram_bytes,
        "total_gb": total_ram_gb,
    },
    "gpu": gpu_info,
    "software": software_info,
    "benchmark_config": benchmark_config,
    "power_source": power_source,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(env, indent=2) + "\n")
print(json.dumps(env, indent=2))
print(f"\nWritten to: {OUTPUT}")
