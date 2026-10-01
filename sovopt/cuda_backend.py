"""Optional CUDA execution backend for SOV-OPT restarted PDHG.

Uses CuPy exclusively for GPU memory management and runtime dispatch.
Core linear algebra is executed via an explicit custom RawKernel SpMV.
Truthfully reports CUDA availability and hardware capabilities.
Strictly returns CUDA_UNAVAILABLE on Apple Silicon and non-CUDA environments.
"""

import sys

def is_cuda_available():
    """Return True if CuPy and at least one CUDA-capable GPU are accessible."""
    try:
        import cupy as cp
        return cp.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False

def get_device_info():
    """Return detailed metadata about CUDA runtime and hardware, or empty if unavailable."""
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
extern "C" __global__ void spmv(const int* p, const int* j, const double* a,
                                const double* x, double* out, int m) {
    int r = blockDim.x * blockIdx.x + threadIdx.x;
    if (r < m) {
        double v = 0.0;
        for (int k = p[r]; k < p[r + 1]; ++k) {
            v += a[k] * x[j[k]];
        }
        out[r] = v;
    }
}
'''

class CUDACSR:
    """Device CSR matrix representation with sovereign RawKernel SpMV."""

    def __init__(self, p, j, a, shape, kernel, xp):
        self.xp = xp
        self.kernel = kernel
        self.m, self.n = shape
        self.p = xp.asarray(p, dtype=xp.int32)
        self.j = xp.asarray(j, dtype=xp.int32)
        self.a = xp.asarray(a, dtype=xp.float64)

    def dot(self, x, out=None):
        xp = self.xp
        if out is None:
            out = xp.zeros(self.m, dtype=xp.float64)
        else:
            out.fill(0.0)
        if self.m > 0:
            block = 128
            grid = (self.m + block - 1) // block
            self.kernel((grid,), (block,), (self.p, self.j, self.a, x, out, self.xp.int32(self.m)))
        return out

class CUDABackend:
    """NVIDIA CUDA execution backend for restarted preconditioned PDHG."""

    def __init__(self):
        if not is_cuda_available():
            raise RuntimeError("CUDA is not available on this machine.")
        import cupy as cp
        self.xp = cp
        self.kernel = cp.RawKernel(CUDA_SPMV_SOURCE, "spmv")

    def build_csr(self, p, j, a, shape):
        return CUDACSR(p, j, a, shape, self.kernel, self.xp)

    def asarray(self, a, dtype=None):
        return self.xp.asarray(a, dtype=dtype if dtype is not None else self.xp.float64)

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
