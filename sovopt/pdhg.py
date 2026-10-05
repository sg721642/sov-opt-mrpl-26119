"""Restarted preconditioned Primal-Dual Hybrid Gradient (PDHG) solver for continuous LP.

Supports sovereign CSR SpMV on CPU (pdhg-cpu) and custom RawKernel on GPU (pdhg-cuda).
GPU accelerates; CPU verifies original model against exact KKT conditions.
Strictly reports CUDA_UNAVAILABLE with gpu_executed=False on non-CUDA environments.
"""

import time
import numpy as np
from .verify import verify
from .cuda_backend import is_cuda_available, CUDABackend
from .sparse import CSRMatrix as SovereignCSRMatrix, csr_from_dense

class CSRMatrix(SovereignCSRMatrix):
    """Sovereign CPU Compressed Sparse Row representation with dense-array fallback."""

    def __init__(self, A_or_m, n=None, indptr=None, indices=None, data=None, validate=True):
        if n is None and indptr is None:
            if isinstance(A_or_m, SovereignCSRMatrix):
                super().__init__(A_or_m.n_rows, A_or_m.n_cols, A_or_m.indptr, A_or_m.indices, A_or_m.data, validate=False)
            else:
                csr = csr_from_dense(A_or_m)
                super().__init__(csr.n_rows, csr.n_cols, csr.indptr, csr.indices, csr.data, validate=False)
        else:
            super().__init__(A_or_m, n, indptr, indices, data, validate=validate)

    @property
    def m(self):
        return self.n_rows

    @property
    def n(self):
        return self.n_cols

    @property
    def p(self):
        return self.indptr

    @property
    def j(self):
        return self.indices

    @property
    def a(self):
        return self.data


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
        dict: Standardized solver result dictionary with granular timing & telemetry.
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
                'verification': {'kkt_passed': False, 'primal_residual': None, 'dual_residual': None},
                'iterations': 0,
                'setup_seconds': 0.0,
                'iteration_seconds': 0.0,
                'verification_seconds': 0.0,
                'iteration_and_verification_seconds': 0.0,
                'total_elapsed_seconds': 0.0,
                'telemetry': {
                    'kernel_launches_count': 0,
                    'restarts_count': 0,
                    'convergence_checks_count': 0,
                },
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

    # Extract standard inequality form: G * x <= h in sovereign CSR format
    if hasattr(model, 'sparse_inequalities'):
        G_sp, h, _ = model.sparse_inequalities(bounds=False)
    else:
        G_raw, h, _ = model.inequalities(bounds=False)
        G_sp = csr_from_dense(G_raw)

    n = len(model.c)
    m = len(h)

    setup_start = time.perf_counter()

    GT_sp = G_sp.transpose()

    if cuda is not None:
        p_G = G_sp.indptr.astype(np.int32)
        j_G = G_sp.indices.astype(np.int32)
        a_G = G_sp.data.astype(np.float64)
        A = cuda.build_csr(p_G, j_G, a_G, (m, n))

        p_GT = GT_sp.indptr.astype(np.int32)
        j_GT = GT_sp.indices.astype(np.int32)
        a_GT = GT_sp.data.astype(np.float64)
        AT = cuda.build_csr(p_GT, j_GT, a_GT, (n, m))
    else:
        A = G_sp
        AT = GT_sp

    c = xp.asarray(model.c, dtype=xp.float64)
    lo = xp.asarray(model.lower, dtype=xp.float64)
    hi = xp.asarray(model.upper, dtype=xp.float64)
    hh = xp.asarray(h, dtype=xp.float64)

    # Step-size preconditioning in O(nnz)
    row_abs = G_sp.row_sums(abs_vals=True)
    col_abs = G_sp.col_sums(abs_vals=True)
    if scaling:
        tau_denom = np.maximum(col_abs, 1.0)
        sigma_denom = np.maximum(row_abs, 1.0)
        tau = xp.asarray(0.99 / tau_denom, dtype=xp.float64)
        sigma = xp.asarray(0.99 / sigma_denom, dtype=xp.float64)
    else:
        bound = max(1.0, float(np.sqrt(np.max(col_abs, initial=0.0) * np.max(row_abs, initial=0.0))))
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
            'iteration_seconds': 0.0,
            'verification_seconds': 0.0,
            'iteration_and_verification_seconds': 0.0,
            'total_elapsed_seconds': time.perf_counter() - setup_start,
            'telemetry': {
                'kernel_launches_count': 0,
                'restarts_count': 0,
                'convergence_checks_count': 0,
            },
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

    # Preallocated work buffers to eliminate memory churn during iterations
    Ax_bar = xp.zeros(m, dtype=xp.float64)
    ATy = xp.zeros(n, dtype=xp.float64)

    if cuda is not None:
        grid_m = (min(65535, max(1, (m + 127) // 128)),)
        grid_n = (min(65535, max(1, (n + 127) // 128)),)
        block = (128,)
        m_int32 = np.int32(m)
        n_int32 = np.int32(n)

    sync()
    setup_seconds = time.perf_counter() - setup_start
    compute_start = time.perf_counter()

    AT_cpu = GT_sp

    def checked_cpu(xc, yc):
        grad = model.c + AT_cpu.dot(yc)
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

    kernel_launches_count = 0
    restarts_count = 0
    convergence_checks_count = 0
    verification_seconds = 0.0

    check_freq = max(1, int(kwargs.get('check_freq', 100)))
    time_limit = kwargs.get('time_limit', None)

    k = 0
    for k in range(1, max_iter + 1):
        if cuda is not None:
            # 1. SpMV Ax_bar = A * bar
            A.dot(bar, out=Ax_bar)
            # 2. Fused dual step + projection + running average
            count += 1
            inv_count = 1.0 / count
            cuda.dual_step_kernel(grid_m, block, (Ax_bar, hh, sigma, y, avgy, np.float64(inv_count), m_int32))
            # 3. SpMV ATy = AT * y
            AT.dot(y, out=ATy)
            # 4. Fused primal step + projection + extrapolation + running average
            cuda.primal_step_kernel(grid_n, block, (ATy, c, tau, lo, hi, x, bar, avg, np.float64(inv_count), n_int32))
            kernel_launches_count += 4
        else:
            A.dot(bar, out=Ax_bar)
            y = np.maximum(0.0, y + sigma * (Ax_bar - hh))
            AT.dot(y, out=ATy)
            new_x = np.clip(x - tau * (c + ATy), lo, hi)
            bar = 2.0 * new_x - x
            x = new_x
            count += 1
            inv_count = 1.0 / count
            avg += (x - avg) * inv_count
            avgy += (y - avgy) * inv_count

        # Periodic KKT check & numerical guard
        if k % check_freq == 0 or k == max_iter:
            xc = to_cpu(x)
            yc = to_cpu(y)
            if not (np.isfinite(xc).all() and np.isfinite(yc).all()):
                sync()
                tot_t = time.perf_counter() - compute_start
                return {
                    'status': 'NUMERICAL_FAILURE',
                    'algorithm': 'diagonal PDHG with periodic averaging restart' if do_restart else 'diagonal PDHG without restart',
                    'message': f'NaN or Inf detected in PDHG iterates at iteration {k}',
                    'x': xc.tolist(),
                    'dual': yc.tolist(),
                    'objective': None,
                    'verification': {'kkt_passed': False, 'primal_residual': float('nan'), 'dual_residual': float('nan')},
                    'iterations': k,
                    'history': history,
                    'setup_seconds': setup_seconds,
                    'iteration_seconds': max(0.0, tot_t - verification_seconds),
                    'verification_seconds': verification_seconds,
                    'iteration_and_verification_seconds': tot_t,
                    'total_elapsed_seconds': setup_seconds + tot_t,
                    'telemetry': {
                        'kernel_launches_count': kernel_launches_count,
                        'restarts_count': restarts_count,
                        'convergence_checks_count': convergence_checks_count,
                    },
                    'gpu_executed': (device == 'cuda'),
                }

            t_v0 = time.perf_counter()
            xc, z, vr = checked_cpu(xc, yc)
            if not vr.get('kkt_passed', False):
                xa = to_cpu(avg)
                ya = to_cpu(avgy)
                xa, za, va = checked_cpu(xa, ya)
                if va.get('kkt_passed', False):
                    xc, z, vr = xa, za, va
            verification_seconds += (time.perf_counter() - t_v0)
            convergence_checks_count += 1

            history.append(dict(
                iteration=k,
                primal_residual=vr.get('primal_residual'),
                dual_residual=vr.get('dual_residual'),
                relative_gap=vr.get('relative_duality_gap'),
            ))
            if vr.get('kkt_passed', False):
                break
            if time_limit is not None and (time.perf_counter() - compute_start) >= float(time_limit):
                break

        # Deterministic periodic restart
        if do_restart and (k % restart_interval == 0):
            restarts_count += 1
            if cuda is not None:
                cuda.copy_kernel(grid_n, block, (avg, x, n_int32))
                cuda.copy_kernel(grid_n, block, (avg, bar, n_int32))
                cuda.copy_kernel(grid_m, block, (avgy, y, m_int32))
                kernel_launches_count += 3
            else:
                x[:] = avg
                bar[:] = avg
                y[:] = avgy
            count = 0

    sync()
    total_compute_seconds = time.perf_counter() - compute_start
    pure_iteration_seconds = max(0.0, total_compute_seconds - verification_seconds)

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
        'iteration_seconds': pure_iteration_seconds,
        'verification_seconds': verification_seconds,
        'iteration_and_verification_seconds': total_compute_seconds,
        'total_elapsed_seconds': setup_seconds + total_compute_seconds,
        'telemetry': {
            'kernel_launches_count': kernel_launches_count,
            'restarts_count': restarts_count,
            'convergence_checks_count': convergence_checks_count,
        },
        'gpu_executed': (device == 'cuda'),
    }
