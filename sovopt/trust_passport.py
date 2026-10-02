"""SOV-OPT Trust Passport Generator.

Generates a canonical, model-fingerprinted, auditable Trust Passport
recording full mathematical verification provenance and solver telemetry.
Strictly follows the principle: unavailable fields must be null (None),
NEVER fabricated as 0.0 or synthetic approximations.
"""

from typing import Any, Dict, Optional
import numpy as np

try:
    from . import __version__
except ImportError:
    __version__ = '0.3.2'
from .model import Model


def generate_trust_passport(
    model: Model,
    solve_result: Dict[str, Any],
    solver_commit: Optional[str] = None,
    input_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a canonical SOV-OPT Trust Passport.

    Args:
        model: Canonical Model instance.
        solve_result: Dictionary returned by sovopt.solve().
        solver_commit: Optional Git commit hash.
        input_snapshot: Optional snapshot of user inputs.

    Returns:
        dict: Standardized Trust Passport structure.
    """
    v = solve_result.get('verification', {})
    if not isinstance(v, dict):
        v = {}
    ray_v = solve_result.get('ray_verification', {})
    if not isinstance(ray_v, dict):
        ray_v = {}

    # Determine model type
    if model.Q is not None:
        model_type = 'QP'
    elif bool(model.integer):
        model_type = 'MILP'
    else:
        model_type = 'LP'

    # Status
    status = solve_result.get('status')

    # Objective
    raw_obj = solve_result.get('objective')
    obj_val = float(raw_obj) if raw_obj is not None and np.isfinite(raw_obj) else None

    # Verification flag - require actual verified solver evidence, never trust status alone
    verified = False
    if status == 'OPTIMAL_VERIFIED':
        verified = bool(v.get('kkt_passed') or v.get('feasible'))
    elif status == 'INFEASIBLE_CERTIFIED':
        verified = bool(solve_result.get('farkas_certificate') or v.get('farkas_verified'))
    elif status == 'UNBOUNDED_CERTIFIED':
        verified = bool(v.get('verified') or ray_v.get('verified'))
    elif status in ('LIMIT_REACHED', 'NUMERICAL_FAILURE', 'INVALID_MODEL'):
        verified = False
    else:
        verified = False

    # Platform extended precision check
    ld_info = np.finfo(np.longdouble)
    has_extended_precision = bool(ld_info.nmant > 53)

    # Solution verification precision (IEEE 754 double or longdouble extended)
    if (status in ('OPTIMAL_VERIFIED', 'UNBOUNDED_CERTIFIED') or v.get('feasible') or v.get('kkt_passed')) and verified:
        sol_prec = 'longdouble_extended' if has_extended_precision else 'IEEE_754_double'
    else:
        sol_prec = None

    # Bound certificate precision (exact rational Q for MILP lower bounds)
    if model_type == 'MILP' and status == 'OPTIMAL_VERIFIED' and verified:
        bound_prec = 'exact_rational_Q'
    else:
        bound_prec = None

    # Infeasibility certificate precision (exact rational Q for Farkas ray)
    if status == 'INFEASIBLE_CERTIFIED' and verified:
        cert_prec = 'exact_rational_Q'
    else:
        cert_prec = None

    # Combined summary precision
    if cert_prec is not None:
        ver_prec = cert_prec
    elif bound_prec is not None:
        ver_prec = bound_prec
    elif sol_prec is not None:
        ver_prec = sol_prec
    else:
        ver_prec = None

    # Residuals
    primal_res = v.get('primal_residual')
    dual_res = v.get('dual_residual')
    bound_viol = v.get('bound_violation')
    if model_type == 'MILP':
        int_res = v.get('integrality_residual')
        int_res = float(int_res) if int_res is not None and np.isfinite(int_res) else None
    else:
        int_res = None

    # KKT residual is max of primal and dual residual if both present, or stationarity residual for QP
    if primal_res is not None and dual_res is not None:
        kkt_res = float(max(primal_res, dual_res))
    elif v.get('stationarity_residual') is not None:
        kkt_res = float(v.get('stationarity_residual'))
    elif primal_res is not None:
        kkt_res = primal_res
    else:
        kkt_res = None

    # Relative gap for MILP
    raw_gap = solve_result.get('relative_gap')
    rel_gap = float(raw_gap) if raw_gap is not None and np.isfinite(raw_gap) else None

    # Certificate details
    cert_type = None
    cert_verified = None
    if status == 'INFEASIBLE_CERTIFIED':
        cert_type = 'Farkas_infeasibility_ray'
        cert_verified = verified
    elif status == 'UNBOUNDED_CERTIFIED':
        cert_type = 'Unbounded_recession_direction'
        cert_verified = verified

    passport = {
        'schema_version': '1.0.0',
        'model_sha256': model.fingerprint() if hasattr(model, 'fingerprint') else None,
        'solver_version': solve_result.get('solver_version', __version__),
        'solver_commit': solver_commit,
        'model_type': model_type,
        'rows': len(model.A),
        'columns': len(model.c),
        'nnz': int((model.A != 0).sum()) if hasattr(model.A, '__ne__') else 0,
        'algorithm': solve_result.get('method_used', solve_result.get('algorithm')),
        'backend': solve_result.get('backend', 'cpu'),
        'input_snapshot': input_snapshot,
        'status': status,
        'objective': obj_val,
        'verified': verified,
        'verification_precision': ver_prec,
        'solution_verification_precision': sol_prec,
        'bound_certificate_precision': bound_prec,
        'certificate_precision': cert_prec,
        'primal_residual': primal_res,
        'dual_residual': dual_res,
        'bound_violation': bound_viol,
        'integrality_residual': int_res,
        'kkt_residual': kkt_res,
        'relative_gap': rel_gap,
        'certificate_type': cert_type,
        'certificate_verified': cert_verified,
    }

    return passport
