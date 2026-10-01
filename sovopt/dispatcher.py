"""Automatic Algorithm Dispatcher for SOV-OPT.

Inspects model dimensions, integrality, quadratic structure, sparsity, and
numerical dynamic range to automatically select the optimal sovereign solver method
and execution backend per MRPL PS 26119 specifications.
"""

import numpy as np

def inspect_model(model):
    """Analyze mathematical properties of an optimization model."""
    m, n = model.A.shape
    nnz = int((model.A != 0).sum())
    density = float(nnz / (m * n)) if (m * n) > 0 else 0.0
    int_count = len(model.integer)
    has_qp = model.Q is not None and np.any(model.Q != 0)

    # Dynamic range of nonzero coefficients
    nonzeros = []
    if model.c is not None and len(model.c) > 0:
        c_nz = np.abs(model.c[model.c != 0])
        if len(c_nz): nonzeros.extend(c_nz)
    if nnz > 0:
        a_nz = np.abs(model.A[model.A != 0])
        nonzeros.extend(a_nz)
    
    if len(nonzeros) > 0:
        min_coeff = float(np.min(nonzeros))
        max_coeff = float(np.max(nonzeros))
        dyn_range = float(max_coeff / min_coeff) if min_coeff > 0 else float('inf')
    else:
        min_coeff = 0.0
        max_coeff = 0.0
        dyn_range = 1.0

    return {
        'variables': n,
        'constraints': m,
        'nonzeros': nnz,
        'density': density,
        'integer_variables': int_count,
        'has_quadratic_objective': has_qp,
        'min_nonzero_coeff': min_coeff,
        'max_nonzero_coeff': max_coeff,
        'dynamic_range': dyn_range,
    }

def auto_dispatch(model, method='auto', backend='cpu'):
    """Determine optimal algorithm and backend for given model.
    
    Args:
        model: Model instance.
        method: Requested method ('auto', 'simplex', 'dual-simplex', 'ipm', 'bb', 'pdhg-cpu', 'pdhg-gpu').
        backend: Execution backend ('cpu', 'pdhg-cpu', 'pdhg-cuda').
    
    Returns:
        dict: Dispatch decision containing 'method', 'backend', 'problem_class', 'inspection', 'rationale'.
    """
    info = inspect_model(model)
    m = method.lower() if method else 'auto'

    if m not in ('auto', 'simplex', 'dual-simplex', 'ipm', 'bb', 'pdhg-cpu', 'pdhg-gpu', 'pdhg-cuda'):
        raise ValueError(f"Unknown method '{method}'. Supported: auto, simplex, ipm, bb, pdhg-cpu, pdhg-gpu.")

    # Determine intrinsic problem class
    if info['has_quadratic_objective']:
        problem_class = 'QP'
    elif info['integer_variables'] > 0:
        problem_class = 'MILP'
    else:
        problem_class = 'LP'

    # Manual override handling
    if m != 'auto':
        resolved_method = m
        if m in ('pdhg-gpu', 'pdhg-cuda'):
            resolved_backend = 'pdhg-cuda'
            resolved_method = 'pdhg-gpu'
        elif m == 'pdhg-cpu':
            resolved_backend = 'pdhg-cpu'
        else:
            resolved_backend = backend

        rationale = f"User explicitly requested method '{method}' for {problem_class} model."
        return {
            'method': resolved_method,
            'backend': resolved_backend,
            'problem_class': problem_class,
            'inspection': info,
            'rationale': rationale,
        }

    # Automatic selection logic
    if problem_class == 'QP':
        resolved_method = 'ipm'
        resolved_backend = 'cpu'
        rationale = "Model has quadratic objective matrix Q; dispatched to Sovereign Primal-Dual Interior Point QP solver."
    elif problem_class == 'MILP':
        resolved_method = 'bb'
        resolved_backend = 'cpu'
        rationale = f"Model has {info['integer_variables']} integer variables; dispatched to exact rational-bound Branch-and-Bound solver."
    else:
        # Continuous LP
        if backend in ('pdhg-cuda', 'pdhg-cpu'):
            resolved_backend = backend
            resolved_method = 'pdhg-gpu' if backend == 'pdhg-cuda' else 'pdhg-cpu'
            rationale = f"Continuous LP executed with first-order PDHG on {backend}."
        else:
            resolved_method = 'dual-simplex'
            resolved_backend = 'cpu'
            rationale = "Continuous LP dispatched to Bounded-Variable Revised Dual Simplex with sparse LU refactorization, Markowitz pivoting, Devex pricing, and exact KKT certification."

    return {
        'method': resolved_method,
        'backend': resolved_backend,
        'problem_class': problem_class,
        'inspection': info,
        'rationale': rationale,
    }
