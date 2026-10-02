"""Farkas Infeasibility Certificate Constraint Lens.

Provides diagnostic ranking of original constraint contributions to an
infeasibility proof.

DISCLAIMER:
This is a diagnostic ranking — not a minimal Irreducible Infeasible Subsystem (IIS).
Never interpret this ranking as a minimal IIS.
"""

from typing import Any, Dict, List, Sequence, Union
from fractions import Fraction as F
import numpy as np

from .model import Model
from .verify import exact_farkas


def rank_farkas_contributions(
    model: Model,
    certificate: Sequence[Union[float, F]],
    top_k: int = 10,
) -> Dict[str, Any]:
    """Rank original model constraints by contribution to the Farkas infeasibility proof.

    Args:
        model: Canonical Model instance.
        certificate: Multiplier vector z on model.inequalities().
        top_k: Maximum number of top contributing constraints to return.

    Returns:
        dict: Diagnostic ranking with explicit disclaimer.
    """
    G, h, labels = model.inequalities()
    if len(certificate) != len(h):
        raise ValueError(f'Certificate dimension mismatch: got {len(certificate)}, expected {len(h)}')

    is_verified = exact_farkas(model, certificate)
    if not is_verified:
        return {
            'disclaimer': 'Diagnostic ranking — not a minimal IIS.',
            'is_minimal_iis': False,
            'certificate_verified': False,
            'diagnostic_available': False,
            'total_contradiction': None,
            'total_active_multipliers': 0,
            'top_contributions': [],
            'warning': 'Diagnostic ranking unavailable: certificate failed exact rational Farkas verification.',
        }

    # Use exact rational arithmetic for term contributions
    z_F = [v if isinstance(v, F) else F(str(v)) if isinstance(v, str) else F(float(v)) for v in certificate]
    h_F = [F(float(val)) for val in h]

    # Calculate contribution: z_i * h_i in Q (more negative = stronger contribution to h^T z < 0)
    items = []
    total_contradiction_F = F(0)
    for i in range(len(h)):
        zi = z_F[i]
        hi = h_F[i]
        contrib_F = zi * hi
        total_contradiction_F += contrib_F
        if zi > 0:
            items.append({
                'index': i,
                'label': labels[i],
                'multiplier': float(zi),
                'bound_value': float(hi),
                'contribution': float(contrib_F),
                'term_description': 'certificate term contribution',
            })

    # Sort: most negative contribution first (strongest driver of contradiction)
    items.sort(key=lambda x: x['contribution'])

    ranked = []
    for rank, item in enumerate(items[:top_k], start=1):
        item_copy = dict(item)
        item_copy['rank'] = rank
        ranked.append(item_copy)

    return {
        'disclaimer': 'Diagnostic ranking — not a minimal IIS.',
        'is_minimal_iis': False,
        'certificate_verified': True,
        'diagnostic_available': True,
        'total_contradiction': float(total_contradiction_F),
        'total_active_multipliers': len(items),
        'top_contributions': ranked,
    }
