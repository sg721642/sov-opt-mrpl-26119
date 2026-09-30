"""SOV-OPT reference prototype 0.1.0."""
import platform,time
from .model import Model,load
__version__='0.1.0'

def solve(model,backend='cpu',tol=1e-7,**options):
    model.validate()
    if not 1e-10<=tol<=1e-4:raise ValueError('Tolerance must be between 1e-10 and 1e-4')
    if 'max_iter' in options and (not isinstance(options['max_iter'],int) or options['max_iter']<1):raise ValueError('max_iter must be a positive integer')
    start=time.perf_counter()
    if backend not in ('cpu','pdhg-cpu','pdhg-cuda'):raise ValueError('Unknown backend')
    if backend.startswith('pdhg'):
        if model.Q is not None or model.integer:raise ValueError('PDHG supports continuous LP only')
        from .pdhg import solve_pdhg
        r=solve_pdhg(model,device=backend.split('-')[1],tol=tol,**options)
    elif model.integer:
        from .milp import solve_milp
        r=solve_milp(model,tol=tol,**options)
    elif model.Q is not None:
        from .qp import solve_qp
        r=solve_qp(model,tol=tol,**options)
    else:
        from .simplex import solve_lp
        r=solve_lp(model,tol=tol,**options)
    r.update(model_name=model.name,model_sha256=model.fingerprint(),solver_version=__version__,elapsed_seconds=time.perf_counter()-start,backend=backend,variables=len(model.c),rows=len(model.A),nonzeros=int((model.A!=0).sum()),machine=dict(system=platform.system(),architecture=platform.machine(),python=platform.python_version()))
    return r
