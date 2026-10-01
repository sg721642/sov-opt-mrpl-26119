"""Numerical stress test suite for SOV-OPT Gate 5.

All synthetic test fixtures are strictly labeled:
[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA]
[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
"""
import unittest
import numpy as np

from sovopt.model import Model
from sovopt.dual_simplex import solve_dual_simplex
from sovopt.presolve import (
    presolve_model,
    scale_model,
    presolve_and_scale,
    compute_dynamic_range,
)
from sovopt.verify import verify


def make_model(c, A, row_lower, row_upper, lower, upper, **kw):
    return Model(
        c=np.array(c, dtype=float),
        A=np.array(A, dtype=float),
        row_lower=np.array(row_lower, dtype=float),
        row_upper=np.array(row_upper, dtype=float),
        lower=np.array(lower, dtype=float),
        upper=np.array(upper, dtype=float),
        **kw,
    )


class TestNumericalStress(unittest.TestCase):

    # =========================================================================
    # 1. Ill-Conditioned Row Scales (8 Orders of Magnitude)
    # =========================================================================
    def test_01_row_scales_8_orders_of_magnitude(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Row scales spanning 8 orders of magnitude."""
        # Row 0 has magnitude ~1e-4, Row 1 has magnitude ~1e4
        A = np.array([[1e-4, 1e-4], [1e4, 2e4]])
        c = np.array([-1.0, -2.0])
        model = make_model(
            c=c,
            A=A,
            row_lower=[-np.inf, -np.inf],
            row_upper=[1e-4, 2e4],
            lower=[0.0, 0.0],
            upper=[10.0, 10.0],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertTrue(res.get('scaling_applied', False))

    # =========================================================================
    # 2. Ill-Conditioned Column Scales (8 Orders of Magnitude)
    # =========================================================================
    def test_02_column_scales_8_orders_of_magnitude(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Column scales spanning 8 orders of magnitude."""
        # Col 0 has magnitude ~1e-4, Col 1 has magnitude ~1e4
        A = np.array([[1e-4, 1e4], [2e-4, 1e4]])
        c = np.array([1e-4, 1e4])
        model = make_model(
            c=c,
            A=A,
            row_lower=[1.0, 1.0],
            row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0],
            upper=[1e8, 1e8],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 3. Near-Dependent / Parallel Rows
    # =========================================================================
    def test_03_near_dependent_rows(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Near-dependent rows with 1e-6 perturbation."""
        A = np.array([[1.0, 1.0], [1.0, 1.000001]])
        c = np.array([-1.0, -1.0])
        model = make_model(
            c=c,
            A=A,
            row_lower=[-np.inf, -np.inf],
            row_upper=[2.0, 2.000002],
            lower=[0.0, 0.0],
            upper=[5.0, 5.0],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertIn(res['status'], ('OPTIMAL_VERIFIED', 'NUMERICAL_FAILURE'))
        if res['status'] == 'OPTIMAL_VERIFIED':
            self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 4. Duplicate Rows
    # =========================================================================
    def test_04_duplicate_rows(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Identical duplicate rows handled without singularity."""
        A = np.array([[1.0, 1.0], [1.0, 1.0]])
        c = np.array([-2.0, -3.0])
        model = make_model(
            c=c,
            A=A,
            row_lower=[-np.inf, -np.inf],
            row_upper=[5.0, 5.0],
            lower=[0.0, 0.0],
            upper=[10.0, 10.0],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 5. Extreme Finite Bounds (1e14)
    # =========================================================================
    def test_05_extreme_finite_bounds_1e14(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Large finite bounds (10^14) without overflow."""
        A = np.array([[1.0, 1.0]])
        c = np.array([1.0, 2.0])
        model = make_model(
            c=c,
            A=A,
            row_lower=[1e10],
            row_upper=[np.inf],
            lower=[0.0, 0.0],
            upper=[1e14, 1e14],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertAlmostEqual(res['x'][0], 1e10, delta=1e4)

    # =========================================================================
    # 6. Tiny Nonzero Coefficients (1e-10)
    # =========================================================================
    def test_06_tiny_nonzero_coefficients(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Small matrix coefficients (10^-10) without division by zero."""
        A = np.array([[1e-10, 1.0], [1.0, 0.0]])
        c = np.array([1.0, 1.0])
        model = make_model(
            c=c,
            A=A,
            row_lower=[1.0, 2.0],
            row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0],
            upper=[10.0, 10.0],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 7. Scaling Equilibration Matrix Condition
    # =========================================================================
    def test_07_scaling_equilibration_reduces_dynamic_range(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Matrix scaling equilibrates rows and columns."""
        model = make_model(
            c=[1.0, 1.0],
            A=[[1e6, 1e6], [1e-2, 2e-2]],
            row_lower=[1.0, 1e-2],
            row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0],
            upper=[np.inf, np.inf],
        )
        dr_before = compute_dynamic_range(model.A, model.c)
        scaled, stack, tel = scale_model(model)
        dr_after = compute_dynamic_range(scaled.A, scaled.c)
        self.assertLess(dr_after, dr_before)
        # Verify row and column norms after scaling are O(1)
        row_max = np.max(np.abs(scaled.A), axis=1)
        col_max = np.max(np.abs(scaled.A), axis=0)
        np.testing.assert_allclose(row_max, 1.0, atol=0.5)
        np.testing.assert_allclose(col_max, 1.0, atol=0.5)

    # =========================================================================
    # 8. Activity Bounds with Mixed Extreme and Infinite Bounds
    # =========================================================================
    def test_08_activity_bounds_mixed_extreme(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Activity bounds with mixture of 1e14 and inf bounds."""
        # Row 0: x0 + x1 <= 1e15 (with x0 in [0, 1e14], x1 in [0, 1e14] => max activity 2e14 <= 1e15, redundant)
        # Row 1: x0 + 2*x1 >= 1.0 (finite constraint, not redundant)
        model = make_model(
            c=[1.0, 1.0],
            A=[[1.0, 1.0], [1.0, 2.0]],
            row_lower=[-np.inf, 1.0],
            row_upper=[1e15, np.inf],
            lower=[0.0, 0.0],
            upper=[1e14, 1e14],
        )
        pres_res = presolve_model(model)
        self.assertIsNone(pres_res.status)
        self.assertEqual(len(pres_res.model.A), 1)
        self.assertGreaterEqual(pres_res.telemetry.get('redundant_rows', 0), 1)

    # =========================================================================
    # 9. Multi-Decade Objective Scaling
    # =========================================================================
    def test_09_multi_decade_objective_scaling(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Objective coefficients spanning 8 orders of magnitude."""
        A = np.array([[1.0, 1.0], [0.0, 1.0]])
        c = np.array([1e-4, 1e4])
        model = make_model(
            c=c,
            A=A,
            row_lower=[1.0, 0.5],
            row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0],
            upper=[10.0, 10.0],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 10. Degenerate Vertices (Multiple Active Constraints)
    # =========================================================================
    def test_10_degenerate_vertex(self):
        """[INTERNAL NUMERICAL TESTS — NOT PUBLIC BENCHMARK DATA] Degenerate vertex with 3 constraints meeting at (1, 1)."""
        A = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
        ])
        c = np.array([1.0, 1.0])
        model = make_model(
            c=c,
            A=A,
            row_lower=[1.0, 1.0, 2.0],
            row_upper=[np.inf, np.inf, np.inf],
            lower=[0.0, 0.0],
            upper=[5.0, 5.0],
        )
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertAlmostEqual(res['x'][0], 1.0, places=6)
        self.assertAlmostEqual(res['x'][1], 1.0, places=6)
        self.assertAlmostEqual(res['objective'], 2.0, places=6)


if __name__ == '__main__':
    unittest.main()
