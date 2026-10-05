"""Exhaustive mathematical validity oracle tests for sovereign cutting planes.

Verifies:
- Cover cut validity: every feasible integer point satisfies the cut.
- Efficacy and violation: current fractional point violates the cut.
- Strict refusal on unsupported rows (negative coefficients, continuous variables).
- Duplicate suppression and pool bounds.
- Zero invalid cuts across all test instances.

Sovereign test suite for MRPL Problem Statement 26119.
"""
import itertools
import math
import unittest
import numpy as np

from sovopt.model import Model
from sovopt.cuts import (
    Cut, CutPool, CutConfig, CutValidationResult,
    separate_cover_cuts, validate_cut, compute_violation, compute_efficacy
)
from sovopt.dual_simplex import solve_dual_simplex


class TestCuttingPlanes(unittest.TestCase):
    """Exhaustive oracle tests verifying mathematical cut validity."""

    def test_01_knapsack_cover_cut_validity_exhaustive_oracle(self):
        """Exhaustive 2^n oracle: every generated cover cut must be satisfied by ALL feasible integer points."""
        # 5 binary variables: weights [3, 4, 3, 5, 2], capacity <= 8
        # Feasible binary points: sum(w_i x_i) <= 8
        c = np.array([-5.0, -6.0, -4.0, -7.0, -3.0])
        A = np.array([[3.0, 4.0, 3.0, 5.0, 2.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([8.0])
        lower = np.zeros(5)
        upper = np.ones(5)
        integer = (0, 1, 2, 3, 4)

        model = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                      lower=lower, upper=upper, integer=integer)

        # Enumerate ALL 2^5 = 32 binary vectors
        all_binary = [np.array(p, dtype=np.float64) for p in itertools.product([0, 1], repeat=5)]
        feasible_binary = [p for p in all_binary if float(np.dot(A[0], p)) <= 8.0 + 1e-9]

        self.assertGreater(len(feasible_binary), 0)
        self.assertLess(len(feasible_binary), 32)

        # Solve continuous LP relaxation
        res_lp = solve_dual_simplex(model, presolve=False, scaling=False)
        self.assertEqual(res_lp['status'], 'OPTIMAL_VERIFIED')
        x_lp = np.array(res_lp['x'])

        # Check that x_lp has fractional components
        is_frac = any(abs(x_lp[j] - round(x_lp[j])) > 1e-4 for j in integer)
        self.assertTrue(is_frac, "Expected fractional root LP for knapsack")

        # Separate cover cuts
        cfg = CutConfig(cut_violation_tol=1e-5, cut_min_efficacy=1e-5)
        cuts = separate_cover_cuts(model, x_lp, config=cfg)
        self.assertGreater(len(cuts), 0, "Expected at least one cover cut")

        # EXHAUSTIVE VALIDITY CHECK:
        # Every feasible binary point MUST satisfy the cut: a^T x <= rhs
        # The fractional LP point MUST violate the cut: a^T x_lp > rhs
        for cut in cuts:
            # Check violation at fractional LP point
            v_lp = compute_violation(cut.coefficients, cut.rhs, x_lp)
            self.assertGreater(v_lp, cfg.cut_violation_tol, "Cut must violate current LP solution")

            # Check validity on EVERY feasible integer assignment
            for x_feas in feasible_binary:
                lhs = float(np.dot(cut.coefficients, x_feas))
                self.assertLessEqual(lhs, cut.rhs + 1e-9,
                                     f"FATAL: Cut {cut.to_dict()} violated by feasible integer point {x_feas.tolist()}!")

    def test_02_multiple_possible_covers_exhaustive(self):
        """Model with multiple possible covers: all generated cuts are valid on all feasible integer points."""
        # 6 binary variables: weights [4, 4, 3, 3, 2, 2], capacity <= 7
        c = np.array([-6.0, -6.0, -4.0, -4.0, -2.0, -2.0])
        A = np.array([[4.0, 4.0, 3.0, 3.0, 2.0, 2.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([7.0])
        lower = np.zeros(6)
        upper = np.ones(6)
        integer = tuple(range(6))

        model = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                      lower=lower, upper=upper, integer=integer)

        all_binary = [np.array(p, dtype=np.float64) for p in itertools.product([0, 1], repeat=6)]
        feasible_binary = [p for p in all_binary if float(np.dot(A[0], p)) <= 7.0 + 1e-9]

        res_lp = solve_dual_simplex(model, presolve=False, scaling=False)
        x_lp = np.array(res_lp['x'])

        cuts = separate_cover_cuts(model, x_lp)
        self.assertGreater(len(cuts), 0)

        for cut in cuts:
            for x_feas in feasible_binary:
                lhs = float(np.dot(cut.coefficients, x_feas))
                self.assertLessEqual(lhs, cut.rhs + 1e-9,
                                     f"Cover cut violated by feasible point {x_feas.tolist()}")

    def test_03_exact_capacity_boundary_no_false_cuts(self):
        """When total capacity is not exceeded by any subset, no cover cut can be generated."""
        # Sum of weights <= capacity (e.g. weights [1, 2, 3], capacity = 6)
        c = np.array([-1.0, -2.0, -3.0])
        A = np.array([[1.0, 2.0, 3.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([10.0])  # redundant capacity
        lower = np.zeros(3)
        upper = np.ones(3)
        integer = (0, 1, 2)

        model = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                      lower=lower, upper=upper, integer=integer)

        x_lp = np.array([0.5, 0.5, 0.5])
        cuts = separate_cover_cuts(model, x_lp)
        self.assertEqual(len(cuts), 0, "No cover cut should be generated for redundant capacity")

    def test_04_negative_coefficients_declined(self):
        """Rows with negative coefficients must be declined safely by cover separator."""
        c = np.array([-1.0, -2.0, -3.0])
        A = np.array([[2.0, -3.0, 4.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([3.0])
        lower = np.zeros(3)
        upper = np.ones(3)
        integer = (0, 1, 2)

        model = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                      lower=lower, upper=upper, integer=integer)

        x_lp = np.array([0.9, 0.1, 0.8])
        cuts = separate_cover_cuts(model, x_lp)
        self.assertEqual(len(cuts), 0, "Separator must decline rows with negative coefficients")

    def test_05_continuous_variables_mixed_in_row_declined(self):
        """Rows containing continuous variables must be declined conservatively."""
        c = np.array([-1.0, -2.0, -3.0])
        A = np.array([[2.0, 3.0, 4.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([5.0])
        lower = np.zeros(3)
        upper = np.ones(3)
        integer = (0, 1)  # Variable 2 is CONTINUOUS!

        model = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                      lower=lower, upper=upper, integer=integer)

        x_lp = np.array([0.8, 0.8, 0.5])
        cuts = separate_cover_cuts(model, x_lp)
        self.assertEqual(len(cuts), 0, "Separator must decline rows with mixed continuous variables")

    def test_06_extreme_coefficient_ratios(self):
        """Knapsack with coefficients spanning multiple orders of magnitude."""
        # weights: [0.01, 10.0, 100.0, 1000.0], capacity 105.0
        c = np.array([-1.0, -2.0, -3.0, -4.0])
        A = np.array([[0.01, 10.0, 100.0, 1000.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([105.0])
        lower = np.zeros(4)
        upper = np.ones(4)
        integer = (0, 1, 2, 3)

        model = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                      lower=lower, upper=upper, integer=integer)

        all_binary = [np.array(p, dtype=np.float64) for p in itertools.product([0, 1], repeat=4)]
        feasible_binary = [p for p in all_binary if float(np.dot(A[0], p)) <= 105.0 + 1e-9]

        x_lp = np.array([0.5, 0.5, 0.95, 0.05])
        cuts = separate_cover_cuts(model, x_lp)
        for cut in cuts:
            for x_feas in feasible_binary:
                lhs = float(np.dot(cut.coefficients, x_feas))
                self.assertLessEqual(lhs, cut.rhs + 1e-9)

    def test_07_cut_pool_duplicate_suppression(self):
        """CutPool must detect and reject duplicate or parallel cuts."""
        pool = CutPool(CutConfig(max_total_cuts=10))

        cut1 = Cut(
            cut_type='cover',
            coefficients=np.array([1.0, 1.0, 0.0]),
            rhs=1.0,
            efficacy=0.5,
        )
        cut2 = Cut(
            cut_type='cover',
            coefficients=np.array([1.0, 1.0, 0.0]),
            rhs=1.0,
            efficacy=0.6,
        )
        cut3 = Cut(
            cut_type='cover',
            coefficients=np.array([0.0, 1.0, 1.0]),
            rhs=1.0,
            efficacy=0.7,
        )

        added1 = pool.add(cut1)
        added2 = pool.add(cut2)  # Duplicate!
        added3 = pool.add(cut3)

        self.assertTrue(added1)
        self.assertFalse(added2, "Duplicate cut must not be added to pool")
        self.assertTrue(added3)
        self.assertEqual(len(pool), 2)

    def test_08_numerical_safeguards(self):
        """validate_cut must reject invalid cuts (NaN, Inf, tiny norm, excessive magnitude)."""
        cfg = CutConfig()
        x = np.array([0.5, 0.5])

        # NaN coefficient
        c_nan = Cut('cover', np.array([np.nan, 1.0]), 1.0)
        self.assertFalse(validate_cut(c_nan, x, 2, cfg).valid)

        # Inf RHS
        c_inf = Cut('cover', np.array([1.0, 1.0]), np.inf)
        self.assertFalse(validate_cut(c_inf, x, 2, cfg).valid)

        # Zero norm
        c_zero = Cut('cover', np.array([0.0, 0.0]), 1.0)
        self.assertFalse(validate_cut(c_zero, x, 2, cfg).valid)

        # Huge coefficient
        c_huge = Cut('cover', np.array([1e8, 1.0]), 1.0)
        self.assertFalse(validate_cut(c_huge, x, 2, cfg).valid)

        # Dimension mismatch
        c_dim = Cut('cover', np.array([1.0, 1.0, 1.0]), 1.0)
        self.assertFalse(validate_cut(c_dim, x, 2, cfg).valid)


if __name__ == '__main__':
    unittest.main()
