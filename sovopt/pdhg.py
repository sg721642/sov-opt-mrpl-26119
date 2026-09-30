"""Experimental diagonally preconditioned PDHG, optional periodic ergodic restart.
Own CSR SpMV on CPU / own CUDA RawKernel, CuPy only for device arrays/runtime.
CUDA path requires independent hardware validation; no automatic fallback.
"""
import time
import numpy as np
from .verify import verify

CUDA_SOURCE = r'''
extern "C" __global__ void spmv(const int* p, const int* j, const double* a,
 const double* x, double* out, int m) {
 int r=blockDim.x*blockIdx.x+threadIdx.x;
 if(r<m){double v=0.;for(int k=p[r];k<p[r+1];++k)v+=a[k]*x[j[k]];out[r]=v;}
}
'''

class CSR:
    def __init__(self, A, xp, kernel=None):
        self.xp = xp
        self.kernel = kernel
        self.m, self.n = A.shape
        r, j = np.nonzero(A)
        self.r = xp.asarray(r, dtype=xp.int32)
        self.j = xp.asarray(j, dtype=xp.int32)
        self.a = xp.asarray(A[r, j])
        self.p = xp.asarray(np.r_[0, np.cumsum(np.bincount(r, minlength=self.m))], dtype=xp.int32)

    def dot(self, x):
        xp = self.xp
        out = xp.zeros(self.m, dtype=xp.float64)
        if self.kernel is None:
            xp.add.at(out, self.r, self.a * x[self.j])
        elif self.m:
            self.kernel(((self.m + 127) // 128,), (128,), (self.p, self.j, self.a, x, out, np.int32(self.m)))
        return out

def solve_pdhg(model, device='cpu', tol=1e-7, max_iter=50000, restart=1000, scaling=True):
    if device == 'cuda':
        try:
            import cupy as xp
            if xp.cuda.runtime.getDeviceCount() < 1:
                raise RuntimeError('No CUDA device')
        except Exception as e:
            raise ValueError('CUDA backend unavailable; use pdhg-cpu or an NVIDIA Linux machine') from e
        kernel = xp.RawKernel(CUDA_SOURCE, 'spmv')
        to_cpu = xp.asnumpy
    else:
        xp = np
        kernel = None
        to_cpu = np.asarray

    G, h, _ = model.inequalities(bounds=False)
    n = len(model.c)
    m = len(h)
    setup = time.perf_counter()
    A = CSR(G, xp, kernel)
    AT = CSR(G.T, xp, kernel)
    c = xp.asarray(model.c)
    lo = xp.asarray(model.lower)
    hi = xp.asarray(model.upper)
    hh = xp.asarray(h)

    if scaling:
        tau = xp.asarray(0.99 / np.maximum(np.sum(abs(G), axis=0), 1.0))
        sigma = xp.asarray(0.99 / np.maximum(np.sum(abs(G), axis=1), 1.0))
    else:
        bound = max(1.0, float(np.sqrt(np.max(np.sum(abs(G), axis=0), initial=0) * np.max(np.sum(abs(G), axis=1), initial=0))))
        tau = xp.ones(n) * (0.99 / bound)
        sigma = xp.ones(m) * (0.99 / bound)

    # Initial point: midpoint for finite bounds, or lower+1 / upper-1 / 0 for infinite bounds
    x_init = np.where(np.isfinite(model.lower) & np.isfinite(model.upper),
                      (model.lower + model.upper) / 2.0,
                      np.where(np.isfinite(model.lower), model.lower + 1.0,
                               np.where(np.isfinite(model.upper), model.upper - 1.0, 0.0)))
    x = xp.asarray(x_init, dtype=xp.float64)
    bar = x.copy()
    y = xp.zeros(m, dtype=xp.float64)
    avg = x.copy()
    avgy = y.copy()
    count = 0
    history = []

    if device == 'cuda':
        xp.cuda.Stream.null.synchronize()
    setup_seconds = time.perf_counter() - setup
    compute = time.perf_counter()

    def checked(xx, yy):
        xc = to_cpu(xx)
        yc = to_cpu(yy)
        grad = model.c + G.T @ yc
        z = list(yc)
        # Append bound multipliers matching model.inequalities() order:
        for j in range(n):
            if np.isfinite(model.upper[j]):
                athi = abs(xc[j] - model.upper[j]) <= tol
                z.append(max(0.0, -grad[j]) if athi else 0.0)
            if np.isfinite(model.lower[j]):
                atlo = abs(xc[j] - model.lower[j]) <= tol
                z.append(max(0.0, grad[j]) if atlo else 0.0)
        return xc, z, verify(model, xc, z, tol)

    vr = {'kkt_passed': False, 'primal_residual': float('nan'), 'dual_residual': float('nan'), 'relative_duality_gap': float('nan'), 'objective': None}
    xc = to_cpu(x)
    z = []

    for k in range(1, max_iter + 1):
        y = xp.maximum(0.0, y + sigma * (A.dot(bar) - hh))
        new = xp.clip(x - tau * (c + AT.dot(y)), lo, hi)
        bar = 2.0 * new - x
        x = new
        count += 1
        avg += (x - avg) / count
        avgy += (y - avgy) / count

        if k % 100 == 0 or k == max_iter:
            xc, z, vr = checked(x, y)
            if not vr.get('kkt_passed', False):
                xa, za, va = checked(avg, avgy)
                if va.get('kkt_passed', False):
                    xc, z, vr = xa, za, va
            history.append(dict(iteration=k, primal_residual=vr.get('primal_residual'),
                                dual_residual=vr.get('dual_residual'), relative_gap=vr.get('relative_duality_gap')))
            if vr.get('kkt_passed', False):
                break

        if restart and k % restart == 0:
            x = avg.copy()
            y = avgy.copy()
            bar = x.copy()
            count = 0
            avg = x.copy()
            avgy = y.copy()

    if device == 'cuda':
        xp.cuda.Stream.null.synchronize()

    return dict(status='OPTIMAL_VERIFIED' if vr.get('kkt_passed', False) else 'LIMIT_REACHED',
                algorithm='diagonal PDHG with periodic averaging restart',
                x=xc.tolist(), dual=z, objective=vr.get('objective'),
                verification=vr, iterations=k, history=history,
                setup_seconds=setup_seconds, iteration_and_verification_seconds=time.perf_counter() - compute,
                gpu_executed=(device == 'cuda'))
