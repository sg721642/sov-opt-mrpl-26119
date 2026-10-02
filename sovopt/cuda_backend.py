"""Optional CUDA execution backend for SOV-OPT restarted PDHG.

Uses CuPy exclusively for GPU memory management and runtime dispatch.
Core linear algebra is executed via an explicit custom RawKernel SpMV.
Truthfully reports CUDA availability and hardware capabilities.
Strictly returns CUDA_UNAVAILABLE on Apple Silicon and non-CUDA environments.

Environment setup: CUDA_PATH is auto-detected from the conda environment
Library directory (Library/include/cuda.h) so that CuPy can compile
RawKernel JIT kernels without requiring a system-level CUDA toolkit install.
"""

import os
import sys
import numpy as np


def _ensure_cuda_path():
    """Auto-detect and set CUDA_PATH if it is not already set.

    CuPy's RawKernel JIT compilation requires CUDA toolkit headers.
    In conda environments, these are installed under Library/include/cuda.h.
    This function finds and sets CUDA_PATH so CuPy can locate them.
    """
    if os.environ.get("CUDA_PATH"):
        return  # Already set by user or environment

    # Strategy 1: check relative to the running Python executable
    try:
        import sys
        python_dir = os.path.dirname(sys.executable)
        # In conda envs, Library/ is sibling to Scripts/ (Windows) or bin/
        for candidate in [
            os.path.join(python_dir, "Library"),
            os.path.join(python_dir, "..", "Library"),
            os.path.join(python_dir, "..", "..", "Library"),
        ]:
            candidate = os.path.normpath(candidate)
            if os.path.isfile(os.path.join(candidate, "include", "cuda.h")):
                os.environ["CUDA_PATH"] = candidate
                # Also add Library/bin to PATH so DLLs (nvJitLink etc.) are found
                lib_bin = os.path.join(candidate, "bin")
                if os.path.isdir(lib_bin):
                    current_path = os.environ.get("PATH", "")
                    if lib_bin not in current_path:
                        os.environ["PATH"] = lib_bin + os.pathsep + current_path
                return
    except Exception:
        pass


def is_cuda_available():
    """Return True if CuPy and at least one CUDA-capable GPU are accessible."""
    _ensure_cuda_path()
    try:
        import cupy as cp
        return cp.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False

def get_device_info():
    """Return detailed metadata about CUDA runtime and hardware, or empty if unavailable."""
    _ensure_cuda_path()
    if not is_cuda_available():
        return {
            "cuda_available": False,
            "device_count": 0,
            "device_name": None,
            "compute_capability": None,
            "total_memory_bytes": None,
            "free_memory_bytes": None,
            "runtime_version": None,
        }
    try:
        import cupy as cp
        dev = cp.cuda.Device(0)
        props = cp.cuda.runtime.getDeviceProperties(dev.id)
        mem_info = dev.mem_info
        cc_major = props.get("major", getattr(dev, "compute_capability", "unknown"))
        cc_minor = props.get("minor", "")
        cc = f"{cc_major}.{cc_minor}" if cc_minor != "" else str(cc_major)
        name = props.get("name", "Unknown NVIDIA GPU")
        if isinstance(name, bytes):
            name = name.decode("utf-8", errors="ignore")
        return {
            "cuda_available": True,
            "device_count": cp.cuda.runtime.getDeviceCount(),
            "device_name": name,
            "compute_capability": cc,
            "total_memory_bytes": mem_info[1],
            "free_memory_bytes": mem_info[0],
            "runtime_version": str(cp.cuda.runtime.runtimeGetVersion()),
        }
    except Exception as e:
        return {
            "cuda_available": False,
            "device_count": 0,
            "device_name": None,
            "compute_capability": None,
            "total_memory_bytes": None,
            "free_memory_bytes": None,
            "runtime_version": None,
            "error": str(e),
        }

CUDA_SPMV_SOURCE = r'''
extern "C" __global__ void spmv(
    const int* __restrict__ p,
    const int* __restrict__ j,
    const double* __restrict__ a,
    const double* __restrict__ x,
    double* __restrict__ out,
    int m
) {
    int stride = blockDim.x * gridDim.x;
    for (int r = blockDim.x * blockIdx.x + threadIdx.x; r < m; r += stride) {
        double v = 0.0;
        int start = p[r];
        int end = p[r + 1];
        #pragma unroll 4
        for (int k = start; k < end; ++k) {
            v += a[k] * x[j[k]];
        }
        out[r] = v;
    }
}
'''

CUDA_DUAL_STEP_SOURCE = r'''
extern "C" __global__ void dual_step_fused(
    const double* __restrict__ Ax_bar,
    const double* __restrict__ hh,
    const double* __restrict__ sigma,
    double* __restrict__ y,
    double* __restrict__ avgy,
    double inv_count,
    int m
) {
    int stride = blockDim.x * gridDim.x;
    for (int i = blockDim.x * blockIdx.x + threadIdx.x; i < m; i += stride) {
        double y_val = y[i];
        double step = y_val + sigma[i] * (Ax_bar[i] - hh[i]);
        double y_new = step > 0.0 ? step : 0.0;
        avgy[i] += (y_new - avgy[i]) * inv_count;
        y[i] = y_new;
    }
}
'''

CUDA_PRIMAL_STEP_SOURCE = r'''
#include <math.h>

extern "C" __global__ void primal_step_fused(
    const double* __restrict__ ATy,
    const double* __restrict__ c,
    const double* __restrict__ tau,
    const double* __restrict__ lo,
    const double* __restrict__ hi,
    double* __restrict__ x,
    double* __restrict__ bar,
    double* __restrict__ avg,
    double inv_count,
    int n
) {
    int stride = blockDim.x * gridDim.x;
    for (int j = blockDim.x * blockIdx.x + threadIdx.x; j < n; j += stride) {
        double x_old = x[j];
        double step = x_old - tau[j] * (c[j] + ATy[j]);
        double l = lo[j];
        double u = hi[j];
        double x_new = fmin(fmax(step, l), u);
        bar[j] = 2.0 * x_new - x_old;
        avg[j] += (x_new - avg[j]) * inv_count;
        x[j] = x_new;
    }
}
'''

CUDA_VECTOR_COPY_SOURCE = r'''
extern "C" __global__ void vector_copy(
    const double* __restrict__ src,
    double* __restrict__ dst,
    int n
) {
    int stride = blockDim.x * gridDim.x;
    for (int i = blockDim.x * blockIdx.x + threadIdx.x; i < n; i += stride) {
        dst[i] = src[i];
    }
}
'''

class CUDACSR:
    """Device CSR matrix representation with sovereign RawKernel SpMV.

    Row pointer p, column indices j, and values a must be in CSR format:
    entries must be grouped by row (i.e., COO (r,j,a) sorted by row before
    computing bincount-based row pointer).
    """

    def __init__(self, p, j, a, shape, kernel, xp):
        self.xp = xp
        self.kernel = kernel
        self.m, self.n = shape
        self.p = xp.asarray(p, dtype=xp.int32)
        self.j = xp.asarray(j, dtype=xp.int32)
        self.a = xp.asarray(a, dtype=xp.float64)
        self.m_int32 = np.int32(self.m)
        self.block = (128,)
        self.grid = (min(65535, max(1, (self.m + 127) // 128)),)

    def dot(self, x, out=None):
        if out is None:
            out = self.xp.zeros(self.m, dtype=self.xp.float64)
        if self.m > 0:
            self.kernel(self.grid, self.block, (self.p, self.j, self.a, x, out, self.m_int32))
        return out

class CUDABackend:
    """NVIDIA CUDA execution backend for restarted preconditioned PDHG."""

    def __init__(self):
        _ensure_cuda_path()
        if not is_cuda_available():
            raise RuntimeError("CUDA is not available on this machine.")
        import cupy as cp
        self.xp = cp
        self.spmv_kernel = cp.RawKernel(CUDA_SPMV_SOURCE, "spmv")
        self.dual_step_kernel = cp.RawKernel(CUDA_DUAL_STEP_SOURCE, "dual_step_fused")
        self.primal_step_kernel = cp.RawKernel(CUDA_PRIMAL_STEP_SOURCE, "primal_step_fused")
        self.copy_kernel = cp.RawKernel(CUDA_VECTOR_COPY_SOURCE, "vector_copy")
        # Compatibility alias
        self.kernel = self.spmv_kernel

    def build_csr(self, p, j, a, shape):
        return CUDACSR(p, j, a, shape, self.spmv_kernel, self.xp)

    def asarray(self, a, dtype=None):
        return self.xp.asarray(a, dtype=dtype if dtype is not None else self.xp.float64)

    def zeros(self, shape, dtype=None):
        return self.xp.zeros(shape, dtype=dtype if dtype is not None else self.xp.float64)

    def to_cpu(self, a):
        return self.xp.asnumpy(a)

    def synchronize(self):
        self.xp.cuda.Stream.null.synchronize()

    def get_memory_stats(self):
        pool = self.xp.get_default_memory_pool()
        return {
            "used_bytes": pool.used_bytes(),
            "total_bytes": pool.total_bytes(),
        }
