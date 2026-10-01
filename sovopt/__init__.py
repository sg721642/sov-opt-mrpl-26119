"""SOV-OPT reference prototype 0.3.2."""
import platform, time
from datetime import datetime, timezone
from .model import Model, load
from .dispatcher import auto_dispatch, inspect_model
from .refinery_twin import build_refinery_twin
from .qplib import read_qplib, parse_probtype, QPLIBError, UnsupportedQPLIBError, QPLIBFormatError

__version__ = '0.3.2'

def solve(model, backend='cpu', tol=1e-7, method='auto', presolve=True, scaling=True, **options):
    model.validate()
    if not 1e-10 <= tol <= 1e-4:
        raise ValueError('Tolerance must be between 1e-10 and 1e-4')
    if 'max_iter' in options and (not isinstance(options['max_iter'], int) or options['max_iter'] < 1):
        raise ValueError('max_iter must be a positive integer')

    start = time.perf_counter()
    disp = auto_dispatch(model, method=method, backend=backend)
    selected_method = disp['method']
    effective_backend = disp['backend']

    if effective_backend not in ('cpu', 'pdhg-cpu', 'pdhg-cuda'):
        raise ValueError(f'Unknown backend: {effective_backend}')

    if selected_method in ('pdhg-gpu', 'pdhg-cuda', 'pdhg-cpu') or effective_backend.startswith('pdhg'):
        if model.Q is not None or model.integer:
            raise ValueError('PDHG supports continuous LP only')
        from .pdhg import solve_pdhg
        device = 'cuda' if selected_method in ('pdhg-gpu', 'pdhg-cuda') or effective_backend == 'pdhg-cuda' else 'cpu'
        r = solve_pdhg(model, device=device, tol=tol, **options)
    elif selected_method == 'bb' or model.integer:
        from .milp import solve_milp
        r = solve_milp(model, tol=tol, **options)
    elif selected_method == 'ipm' or model.Q is not None:
        from .qp import solve_qp
        r = solve_qp(model, tol=tol, **options)
    elif selected_method == 'dual-simplex':
        from .dual_simplex import solve_dual_simplex
        r = solve_dual_simplex(model, tol=tol, presolve=presolve, scaling=scaling, **options)
    else:
        from .simplex import solve_lp
        r = solve_lp(model, tol=tol, scaling=scaling, **options)

    r.pop('dual_exact_fraction', None)
    if 'basis_state' in r and hasattr(r['basis_state'], 'to_dict'):
        r['basis_state'] = r['basis_state'].to_dict()
    gpu_done = bool(r.get('gpu_executed', False))
    r.update(
        model_name=model.name,
        model_sha256=model.fingerprint(),
        solver_version=__version__,
        elapsed_seconds=time.perf_counter() - start,
        backend=effective_backend,
        gpu_executed=gpu_done,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        variables=len(model.c),
        rows=len(model.A),
        nonzeros=int((model.A != 0).sum()),
        dispatch=disp,
        machine=dict(system=platform.system(), architecture=platform.machine(), python=platform.python_version())
    )
    r['method_requested'] = method
    r['method_selected'] = selected_method
    r['selection_reason'] = disp['rationale']
    if 'method_used' not in r:
        if selected_method == 'simplex':
            r['method_used'] = 'primal-simplex'
        else:
            r['method_used'] = selected_method
    if 'fallback_reason' not in r or r['fallback_reason'] is None:
        r['fallback_reason'] = disp.get('fallback_reason', None)
    if 'linear_algebra_used' not in r:
        if effective_backend.startswith('pdhg'):
            r['linear_algebra_used'] = 'pdhg'
        elif r.get('matrix_storage_used') == 'csc' or r.get('basis_storage_used') == 'sparse':
            r['linear_algebra_used'] = 'sparse'
        else:
            r['linear_algebra_used'] = 'dense'
    r.setdefault('presolve_applied', presolve if selected_method in ('dual-simplex', 'simplex') else False)
    r.setdefault('scaling_applied', scaling if selected_method in ('dual-simplex', 'simplex') else False)
    if model.maximize:
        r['objective_sense'] = 'maximize'
    if model.obj_offset != 0.0:
        r['obj_offset'] = model.obj_offset
    return r
