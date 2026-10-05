"""Sovereign Cutting Planes Infrastructure for SOV-OPT.

Implements safe, mathematically rigorous cutting-plane separation:
- Internal Cut and CutPool data structures with duplicate detection and efficacy ranking.
- Strict numerical validation layer (finite coefficients, magnitude bounds, efficacy).
- Binary Cover Cuts separator with greedy detection and minimal-cover reduction.
- Zero external solver dependencies (NumPy and Python stdlib only).

Sovereign implementation for MRPL Problem Statement 26119.
"""
from dataclasses import dataclass, field
import math
from typing import List, Dict, Any, Tuple, Optional, Set
import numpy as np

from .model import Model


@dataclass
class CutConfig:
    """Configuration and numerical safeguards for cutting plane separation."""
    cut_violation_tol: float = 1e-4
    cut_coeff_abs_max: float = 1e6
    cut_min_efficacy: float = 1e-4
    max_cuts_per_round: int = 20
    max_cut_rounds_root: int = 5
    max_cut_rounds_node: int = 0
    max_total_cuts: int = 100
    min_cover_size: int = 2


@dataclass
class Cut:
    """Represents a mathematically valid cutting plane inequality: a^T x <= rhs."""
    cut_type: str                   # 'cover', 'knapsack', etc.
    coefficients: np.ndarray        # shape (n,), float64
    rhs: float                      # scalar float
    sense: str = '<='               # standardized to '<='
    source_node: int = 1            # 1 = root node
    source_row: Optional[int] = None # original constraint row index if derived from a row
    violation_at_generation: float = 0.0
    integer_support: Tuple[int, ...] = ()
    efficacy: float = 0.0           # Euclidean normalized distance to half-space
    generation_tolerance: float = 1e-4
    accepted: bool = True
    status_reason: str = 'VALID'
    is_global: bool = True          # True if valid across entire B&B search tree

    def to_dict(self) -> Dict[str, Any]:
        return {
            'cut_type': self.cut_type,
            'source_node': self.source_node,
            'source_row': self.source_row,
            'rhs': float(self.rhs),
            'sense': self.sense,
            'violation': float(self.violation_at_generation),
            'efficacy': float(self.efficacy),
            'integer_support_size': len(self.integer_support),
            'integer_support': list(self.integer_support),
            'status_reason': self.status_reason,
            'is_global': self.is_global,
        }


@dataclass
class CutValidationResult:
    """Diagnostic result of validating a cut against numerical and feasibility rules."""
    valid: bool
    reason: str
    violation: float = 0.0
    efficacy: float = 0.0
    norm: float = 0.0


def compute_violation(coefficients: np.ndarray, rhs: float, x: np.ndarray) -> float:
    """Compute violation of a^T x <= rhs by point x. Returns max(0, a^T x - rhs)."""
    val = float(np.dot(coefficients, x))
    return max(0.0, val - rhs)


def compute_efficacy(coefficients: np.ndarray, rhs: float, x: np.ndarray) -> Tuple[float, float]:
    """Compute Euclidean norm of coefficients and normalized efficacy (distance to half-space).
    Returns (efficacy, norm).
    """
    norm = float(np.linalg.norm(coefficients))
    if norm < 1e-12:
        return 0.0, norm
    violation = compute_violation(coefficients, rhs, x)
    efficacy = violation / norm
    return efficacy, norm


def validate_cut(cut: Cut, x: np.ndarray, n_vars: int, config: CutConfig) -> CutValidationResult:
    """Validate a candidate cut against strict numerical safety and violation requirements.

    Requirements:
    - Exactly matches variable dimension n_vars.
    - All coefficients and RHS are finite numbers (no NaN, no Inf).
    - Euclidean norm is strictly positive (norm >= 1e-12).
    - Absolute coefficients do not exceed cut_coeff_abs_max.
    - Cut is actually violated by point x by at least cut_violation_tol.
    - Normalized efficacy is at least cut_min_efficacy.
    """
    if len(cut.coefficients) != n_vars:
        return CutValidationResult(False, f"Dimension mismatch: expected {n_vars}, got {len(cut.coefficients)}")

    if not np.all(np.isfinite(cut.coefficients)):
        return CutValidationResult(False, "Non-finite coefficient (NaN or Inf) detected")

    if not math.isfinite(cut.rhs):
        return CutValidationResult(False, "Non-finite RHS (NaN or Inf) detected")

    efficacy, norm = compute_efficacy(cut.coefficients, cut.rhs, x)
    if norm < 1e-12:
        return CutValidationResult(False, f"Zero or near-zero coefficient norm ({norm:.2e})", 0.0, 0.0, norm)

    max_c = float(np.max(np.abs(cut.coefficients)))
    if max_c > config.cut_coeff_abs_max:
        return CutValidationResult(False, f"Coefficient magnitude {max_c:.2e} exceeds max {config.cut_coeff_abs_max:.2e}", 0.0, 0.0, norm)

    violation = compute_violation(cut.coefficients, cut.rhs, x)
    if violation < config.cut_violation_tol:
        return CutValidationResult(False, f"Insufficient violation {violation:.2e} < {config.cut_violation_tol:.2e}", violation, efficacy, norm)

    if efficacy < config.cut_min_efficacy:
        return CutValidationResult(False, f"Insufficient efficacy {efficacy:.2e} < {config.cut_min_efficacy:.2e}", violation, efficacy, norm)

    return CutValidationResult(True, "VALID", violation, efficacy, norm)


class CutPool:
    """Maintains a bounded collection of globally valid cuts with duplicate suppression."""
    def __init__(self, config: Optional[CutConfig] = None):
        self.config = config or CutConfig()
        self.cuts: List[Cut] = []
        self._signatures: Set[Tuple[Any, ...]] = set()

    def _signature(self, cut: Cut) -> Tuple[Any, ...]:
        """Compute canonical hashable signature of a cut to detect duplicates."""
        nz_indices = np.flatnonzero(np.abs(cut.coefficients) > 1e-9)
        nz_vals = tuple(round(float(cut.coefficients[j]), 6) for j in nz_indices)
        return (tuple(nz_indices), nz_vals, round(float(cut.rhs), 6))

    def is_duplicate(self, cut: Cut) -> bool:
        """Check if identical or parallel cut is already in pool."""
        sig = self._signature(cut)
        return sig in self._signatures

    def add(self, cut: Cut) -> bool:
        """Add cut if valid and not duplicate. Returns True if added."""
        if len(self.cuts) >= self.config.max_total_cuts:
            return False
        if self.is_duplicate(cut):
            return False
        sig = self._signature(cut)
        self._signatures.add(sig)
        self.cuts.append(cut)
        return True

    def filter_and_select(self, max_cuts: int) -> List[Cut]:
        """Sort cuts by efficacy descending and select up to max_cuts."""
        sorted_cuts = sorted(self.cuts, key=lambda c: c.efficacy, reverse=True)
        return sorted_cuts[:max_cuts]

    def clear(self):
        self.cuts.clear()
        self._signatures.clear()

    def __len__(self) -> int:
        return len(self.cuts)


def separate_cover_cuts(model: Model, x_lp: np.ndarray,
                        config: Optional[CutConfig] = None,
                        source_node: int = 1,
                        integer_vars: Optional[Tuple[int, ...]] = None) -> List[Cut]:
    """Separate binary cover cuts from knapsack-structured constraints.

    Given a constraint of the form sum_{j in B} a_j x_j <= b with x_j in {0, 1} and a_j > 0,
    find a cover C subset of B such that sum_{j in C} a_j > b.
    Then the canonical cover inequality is:
        sum_{j in C} x_j <= |C| - 1.

    A violated cover satisfies:
        sum_{j in C} (1 - x_lp[j]) < 1.

    We use deterministic greedy selection followed by minimal-cover reduction.
    """
    cfg = config or CutConfig()
    n = len(model.c)
    m = model.A.shape[0] if hasattr(model.A, 'shape') else len(model.A)
    int_vars = integer_vars if integer_vars is not None else model.integer
    if m == 0 or len(int_vars) == 0:
        return []

    # Identify declared binary variables
    binary_set = set()
    for j in int_vars:
        if abs(model.lower[j]) < 1e-7 and abs(model.upper[j] - 1.0) < 1e-7:
            binary_set.add(j)

    if len(binary_set) < cfg.min_cover_size:
        return []

    from .sparse import CSRMatrix
    is_sparse = isinstance(model.A, CSRMatrix)
    cuts_found: List[Cut] = []

    for i in range(m):
        # Extract row coefficients and finite upper bound
        # Consider both <= rows and negated >= rows
        row_bounds_to_check = []
        u_i = model.row_upper[i]
        l_i = model.row_lower[i]

        if math.isfinite(u_i):
            row_bounds_to_check.append((+1.0, float(u_i)))
        if math.isfinite(l_i) and not math.isfinite(u_i):
            # l_i <= a^T x  <=>  -a^T x <= -l_i
            row_bounds_to_check.append((-1.0, -float(l_i)))

        for sign, b in row_bounds_to_check:
            if b <= 0.0:
                # If b <= 0, cover logic on nonnegative coefficients is degenerate
                continue

            # Extract row coefficients
            if is_sparse:
                start = model.A.indptr[i]
                end = model.A.indptr[i + 1]
                cols = model.A.indices[start:end]
                vals = model.A.data[start:end] * sign
            else:
                row_vals = model.A[i] * sign
                cols = np.flatnonzero(np.abs(row_vals) > 1e-9)
                vals = row_vals[cols]

            if len(cols) < cfg.min_cover_size:
                continue

            # Strict verification: ALL active variables in row must be binary with a_j > 0
            # If continuous variables exist, decline conservatively unless proven safe
            row_supported = True
            for c_idx, val in zip(cols, vals):
                if c_idx not in binary_set:
                    row_supported = False
                    break
                if val <= 1e-9:
                    row_supported = False
                    break

            if not row_supported:
                continue

            # Total capacity check: if sum(a_j) <= b, no cover exists
            total_weight = float(np.sum(vals))
            if total_weight <= b + 1e-7:
                continue

            # Greedy search for violated cover:
            # Violated cover condition: sum_{j in C} (1 - x_lp[j]) < 1
            # Sort candidate binary variables in ascending order of (1 - x_lp[j])
            cand_list = []
            for c_idx, val in zip(cols, vals):
                xj = float(x_lp[c_idx])
                slack_j = max(0.0, 1.0 - xj)
                cand_list.append((slack_j, c_idx, float(val)))

            # Deterministic sort: primary = slack ascending, secondary = c_idx ascending
            cand_list.sort(key=lambda t: (t[0], t[1]))

            # Greedy accumulate until sum of weights > b
            cover: List[int] = []
            cover_weight = 0.0
            cover_slack_sum = 0.0

            for slack_j, c_idx, val in cand_list:
                cover.append(c_idx)
                cover_weight += val
                cover_slack_sum += slack_j
                if cover_weight > b + 1e-7:
                    break

            if cover_weight <= b + 1e-7:
                continue

            # Check if cover is violated: cover_slack_sum < 1.0 - cfg.cut_violation_tol
            if cover_slack_sum >= 1.0 - cfg.cut_violation_tol:
                continue

            # Minimal Cover Reduction:
            # Remove any variable whose removal leaves the remaining set a valid cover
            # Try removing in descending order of slack_j (smallest x_j first)
            cover_weights_map = {c_idx: val for _, c_idx, val in cand_list}
            cover_slack_map = {c_idx: slack_j for slack_j, c_idx, _ in cand_list}

            sorted_cover_for_pruning = sorted(cover, key=lambda c_idx: (-cover_slack_map[c_idx], -c_idx))
            for c_idx in sorted_cover_for_pruning:
                w_drop = cover_weights_map[c_idx]
                if cover_weight - w_drop > b + 1e-7:
                    cover.remove(c_idx)
                    cover_weight -= w_drop
                    cover_slack_sum -= cover_slack_map[c_idx]

            card = len(cover)
            if card < cfg.min_cover_size:
                continue

            # Basic cover inequality: sum_{j in C} x_j <= card - 1
            rhs_cut = float(card - 1)
            coeff_cut = np.zeros(n, dtype=np.float64)
            coeff_cut[cover] = 1.0

            cand_cut = Cut(
                cut_type='cover',
                coefficients=coeff_cut,
                rhs=rhs_cut,
                sense='<=',
                source_node=source_node,
                source_row=i,
                violation_at_generation=1.0 - cover_slack_sum,
                integer_support=tuple(sorted(cover)),
                generation_tolerance=cfg.cut_violation_tol,
                is_global=True,
            )

            # Validate candidate cut
            v_res = validate_cut(cand_cut, x_lp, n, cfg)
            if v_res.valid:
                cand_cut.violation_at_generation = v_res.violation
                cand_cut.efficacy = v_res.efficacy
                cuts_found.append(cand_cut)

    return cuts_found


def append_rows_to_matrix(A: Any, new_rows: np.ndarray) -> Any:
    """Safely append row inequalities to a dense numpy array or sovereign CSRMatrix."""
    from .sparse import CSRMatrix
    if isinstance(A, CSRMatrix):
        k, n = new_rows.shape
        r_nz, c_nz = np.nonzero(new_rows)
        v_nz = new_rows[r_nz, c_nz]

        last_ptr = A.indptr[-1]
        extra_ptrs = []
        for i in range(k):
            count = int(np.count_nonzero(new_rows[i]))
            last_ptr += count
            extra_ptrs.append(last_ptr)
        combined_indptr = np.concatenate([A.indptr, np.array(extra_ptrs, dtype=A.indptr.dtype)])
        combined_indices = np.concatenate([A.indices, c_nz.astype(A.indices.dtype)])
        combined_data = np.concatenate([A.data, v_nz.astype(A.data.dtype)])
        return CSRMatrix(A.n_rows + k, n, combined_indptr, combined_indices, combined_data, validate=False)
    else:
        return np.vstack([A, new_rows])
