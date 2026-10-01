"""SOV-OPT reference prototype 0.1.6."""
import platform, time
from datetime import datetime, timezone
from .model import Model, load
from .dispatcher import auto_dispatch, inspect_model
from .refinery_twin import build_refinery_twin

__version__ = '0.1.6'

def solve(model, backend='cpu', tol=1e-7, method='auto', **options):
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

    if selected_method in ('pdhg-gpu', 'pdhg-cpu') or effective_backend.startswith('pdhg'):
        if model.Q is not None or model.integer:
            raise ValueError('PDHG supports continuous LP only')
        from .pdhg import solve_pdhg
        device = 'cuda' if selected_method == 'pdhg-gpu' or effective_backend == 'pdhg-cuda' else 'cpu'
        r = solve_pdhg(model, device=device, tol=tol, **options)
    elif selected_method == 'bb' or model.integer:
        from .milp import solve_milp
        r = solve_milp(model, tol=tol, **options)
    elif selected_method == 'ipm' or model.Q is not None:
        from .qp import solve_qp
        r = solve_qp(model, tol=tol, **options)
    else:
        from .simplex import solve_lp
        r = solve_lp(model, tol=tol, **options)

    r.pop('dual_exact_fraction', None)
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
    if model.maximize:
        r['objective_sense'] = 'maximize'
    if model.obj_offset != 0.0:
        r['obj_offset'] = model.obj_offset
    return r
