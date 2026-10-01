"""Restarted preconditioned Primal-Dual Hybrid Gradient (PDHG) solver for continuous LP.

Supports sovereign CSR SpMV on CPU (pdhg-cpu) and custom RawKernel on GPU (pdhg-cuda).
GPU accelerates; CPU verifies original model against exact KKT conditions.
Strictly reports CUDA_UNAVAILABLE with gpu_executed=False on non-CUDA environments.
"""

import time
import numpy as np
from .verify import verify
from .cuda_backend import is_cuda_available, CUDABackend

class CSRMatrix:
    """Sovereign CPU Compressed Sparse Row representation."""

    def __init__(self, A):
        self.m, self.n = A.shape
        r, j = np.nonzero(A)
        self.r = np.asarray(r, dtype=np.int32)
        self.j = np.asarray(j, dtype=np.int32)
        self.a = np.asarray(A[r, j], dtype=np.float64)
        self.p = np.asarray(np.r_[0, np.cumsum(np.bincount(r, minlength=self.m))], dtype=np.int32)

    def dot(self, x):
        out = np.zeros(self.m, dtype=np.float64)
        if len(self.r) > 0:
            np.add.at(out, self.r, self.a * x[self.j])
        return out


def solve_pdhg(model, device='cpu', backend=None, tol=1e-7, max_iter=50000, restart=1000, scaling=True, **kwargs):
    """Solve continuous LP via restarted diagonally preconditioned PDHG.

    Args:
        model: Continuous LP Model instance.
        device: 'cpu' or 'cuda' (deprecated in favor of backend).
        backend: 'pdhg-cpu' or 'pdhg-cuda'. Overrides device if provided.
        tol: Convergence tolerance for KKT verification.
        max_iter: Maximum number of PDHG iterations.
        restart: Restart interval (iterations). Set to False, 0, or None to disable.
        scaling: If True, use Pock-Chambolle diagonal l1 preconditioning.

    Returns:
        dict: Standardized solver result dictionary.
    """
    if backend is not None:
        device = 'cuda' if backend == 'pdhg-cuda' else 'cpu'

    if device == 'cuda':
        if not is_cuda_available():
            return {
                'status': 'CUDA_UNAVAILABLE',
                'gpu_executed': False,
                'algorithm': 'pdhg-cuda',
                'message': 'CUDA backend unavailable; no NVIDIA GPU or CuPy runtime found',
                'x': [],
                'dual': [],
                'objective': None,
                'verification': {'kkt_passed': False, 'primal_residual': float('nan'), 'dual_residual': float('nan')},
                'iterations': 0,
                'setup_seconds': 0.0,
                'iteration_and_verification_seconds': 0.0,
            }
        cuda = CUDABackend()
        xp = cuda.xp
        to_cpu = cuda.to_cpu
        sync = cuda.synchronize
    else:
        xp = np
        cuda = None
        to_cpu = np.asarray
        sync = lambda: None

    # Extract standard inequality form: G * x <= h
    G, h, _ = model.inequalities(bounds=False)
    n = len(model.c)
    m = len(h)

    setup_start = time.perf_counter()

    if cuda is not None:
        r_G, j_G = np.nonzero(G)
        a_G = G[r_G, j_G]
        # Sort COO by row before building CSR row pointer; without this, p
        # describes grouped rows while j_G/a_G remain in column-major COO
        # order, causing the custom RawKernel SpMV to produce wrong results.
        ord_G = np.argsort(r_G, kind="stable")
        r_G = r_G[ord_G].astype(np.int32)
        j_G = j_G[ord_G].astype(np.int32)
        a_G = a_G[ord_G].astype(np.float64)
        p_G = np.r_[0, np.cumsum(np.bincount(r_G, minlength=m))].astype(np.int32)
        A = cuda.build_csr(p_G, j_G, a_G, (m, n))

        r_GT, j_GT = np.nonzero(G.T)
        a_GT = G.T[r_GT, j_GT]
        ord_GT = np.argsort(r_GT, kind="stable")
        r_GT = r_GT[ord_GT].astype(np.int32)
        j_GT = j_GT[ord_GT].astype(np.int32)
        a_GT = a_GT[ord_GT].astype(np.float64)
        p_GT = np.r_[0, np.cumsum(np.bincount(r_GT, minlength=n))].astype(np.int32)
        AT = cuda.build_csr(p_GT, j_GT, a_GT, (n, m))
    else:
        A = CSRMatrix(G)
        AT = CSRMatrix(G.T)

    c = xp.asarray(model.c, dtype=xp.float64)
    lo = xp.asarray(model.lower, dtype=xp.float64)
    hi = xp.asarray(model.upper, dtype=xp.float64)
    hh = xp.asarray(h, dtype=xp.float64)

    # Step-size preconditioning
    if scaling:
        tau_denom = np.maximum(np.sum(np.abs(G), axis=0), 1.0)
        sigma_denom = np.maximum(np.sum(np.abs(G), axis=1), 1.0)
        tau = xp.asarray(0.99 / tau_denom, dtype=xp.float64)
        sigma = xp.asarray(0.99 / sigma_denom, dtype=xp.float64)
    else:
        bound = max(1.0, float(np.sqrt(np.max(np.sum(np.abs(G), axis=0), initial=0.0) * np.max(np.sum(np.abs(G), axis=1), initial=0.0))))
        tau = xp.full(n, 0.99 / bound, dtype=xp.float64)
        sigma = xp.full(m, 0.99 / bound, dtype=xp.float64)

    # Numerical guard: check step sizes are positive and finite
    tau_cpu = to_cpu(tau)
    sigma_cpu = to_cpu(sigma)
    if not (np.isfinite(tau_cpu).all() and (tau_cpu > 0).all() and np.isfinite(sigma_cpu).all() and (sigma_cpu > 0).all()):
        return {
            'status': 'NUMERICAL_FAILURE',
            'gpu_executed': (device == 'cuda'),
            'algorithm': 'pdhg-cuda' if device == 'cuda' else 'pdhg-cpu',
            'message': 'Preconditioner step sizes are non-positive or non-finite',
            'x': [],
            'dual': [],
            'objective': None,
            'verification': {'kkt_passed': False, 'primal_residual': float('nan'), 'dual_residual': float('nan')},
            'iterations': 0,
            'setup_seconds': time.perf_counter() - setup_start,
            'iteration_and_verification_seconds': 0.0,
        }

    # Initial point: midpoint for finite bounds, or lower+1 / upper-1 / 0
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

    sync()
    setup_seconds = time.perf_counter() - setup_start
    compute_start = time.perf_counter()

    def checked(xx, yy):
        xc = to_cpu(xx)
        yc = to_cpu(yy)
        grad = model.c + G.T @ yc
        z = list(yc)
        for j_idx in range(n):
            if np.isfinite(model.upper[j_idx]):
                athi = abs(xc[j_idx] - model.upper[j_idx]) <= tol
                z.append(max(0.0, -grad[j_idx]) if athi else 0.0)
            if np.isfinite(model.lower[j_idx]):
                atlo = abs(xc[j_idx] - model.lower[j_idx]) <= tol
                z.append(max(0.0, grad[j_idx]) if atlo else 0.0)
        return xc, z, verify(model, xc, z, tol)

    vr = {'kkt_passed': False, 'primal_residual': float('nan'), 'dual_residual': float('nan'), 'relative_duality_gap': float('nan'), 'objective': None}
    xc = to_cpu(x)
    z = []

    do_restart = bool(restart is not False and restart is not None and int(restart) > 0)
    restart_interval = int(restart) if do_restart else 0

    k = 0
    for k in range(1, max_iter + 1):
        # Dual proximal update
        y = xp.maximum(0.0, y + sigma * (A.dot(bar) - hh))
        # Primal proximal update
        new_x = xp.clip(x - tau * (c + AT.dot(y)), lo, hi)
        # Extrapolation
        bar = 2.0 * new_x - x
        x = new_x
        count += 1
        avg += (x - avg) / count
        avgy += (y - avgy) / count

        # Numerical guard: check for NaN/Inf in iterates
        if k % 100 == 0:
            if not (np.isfinite(to_cpu(x)).all() and np.isfinite(to_cpu(y)).all()):
                sync()
                return {
                    'status': 'NUMERICAL_FAILURE',
                    'algorithm': 'diagonal PDHG with periodic averaging restart' if do_restart else 'diagonal PDHG without restart',
                    'message': f'NaN or Inf detected in PDHG iterates at iteration {k}',
                    'x': to_cpu(x).tolist(),
                    'dual': to_cpu(y).tolist(),
                    'objective': None,
                    'verification': {'kkt_passed': False, 'primal_residual': float('nan'), 'dual_residual': float('nan')},
                    'iterations': k,
                    'history': history,
                    'setup_seconds': setup_seconds,
                    'iteration_and_verification_seconds': time.perf_counter() - compute_start,
                    'gpu_executed': (device == 'cuda'),
                }

        # Periodic KKT check
        if k % 100 == 0 or k == max_iter:
            xc, z, vr = checked(x, y)
            if not vr.get('kkt_passed', False):
                xa, za, va = checked(avg, avgy)
                if va.get('kkt_passed', False):
                    xc, z, vr = xa, za, va
            history.append(dict(
                iteration=k,
                primal_residual=vr.get('primal_residual'),
                dual_residual=vr.get('dual_residual'),
                relative_gap=vr.get('relative_duality_gap'),
            ))
            if vr.get('kkt_passed', False):
                break

        # Deterministic periodic restart
        if do_restart and (k % restart_interval == 0):
            x = avg.copy()
            y = avgy.copy()
            bar = x.copy()
            count = 0
            avg = x.copy()
            avgy = y.copy()

    sync()
    total_compute_seconds = time.perf_counter() - compute_start

    return {
        'status': 'OPTIMAL_VERIFIED' if vr.get('kkt_passed', False) else 'LIMIT_REACHED',
        'algorithm': 'diagonal PDHG with periodic averaging restart' if do_restart else 'diagonal PDHG without restart',
        'x': xc.tolist(),
        'dual': z,
        'objective': vr.get('objective'),
        'verification': vr,
        'iterations': k,
        'history': history,
        'setup_seconds': setup_seconds,
        'iteration_and_verification_seconds': total_compute_seconds,
        'gpu_executed': (device == 'cuda'),
    }
