"""Internal unit tests for equality-aware primal-dual convex QP solver.

[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
All models in this module are synthetic mathematical unit fixtures designed
to test correctness of the equality-aware interior-point solver across 20
specific mathematical cases specified in Gate 7.2.
"""

import unittest
import numpy as np
from sovopt import Model
from sovopt.qp import solve_qp, canonicalize_qp


class TestQPInternalFixtures(unittest.TestCase):
    """20 required internal unit test fixtures for convex QP interior-point hardening."""

    def test_01_unconstrained_positive_definite_qp(self):
        """1. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] unconstrained positive-definite QP."""
        # min 1/2 (2 x0^2 + 4 x1^2) - 2 x0 - 4 x1
        # Minimizer x* = [1, 1], Obj = 1/2(2 + 4) - 2 - 4 = -3.0
        m = Model(
            c=np.array([-2.0, -4.0]),
            A=np.zeros((0, 2)),
            row_lower=np.zeros(0),
            row_upper=np.zeros(0),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.array([[2.0, 0.0], [0.0, 4.0]]),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], -3.0, places=6)
        self.assertAlmostEqual(r['x'][0], 1.0, places=6)
        self.assertAlmostEqual(r['x'][1], 1.0, places=6)

    def test_02_one_equality_qp(self):
        """2. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] one equality QP."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 2
        # Minimizer x* = [1, 1], Obj = 1.0
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([2.0]),
            row_upper=np.array([2.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 1.0, places=6)
        self.assertAlmostEqual(r['x'][0], 1.0, places=6)
        self.assertAlmostEqual(r['x'][1], 1.0, places=6)

    def test_03_multiple_equalities(self):
        """3. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] multiple equalities."""
        # min 1/2 (x0^2 + x1^2 + x2^2) s.t. x0 + x1 + x2 = 3 and x0 - x1 = 0
        # Minimizer x* = [1, 1, 1], Obj = 1.5
        m = Model(
            c=np.zeros(3),
            A=np.array([[1.0, 1.0, 1.0], [1.0, -1.0, 0.0]]),
            row_lower=np.array([3.0, 0.0]),
            row_upper=np.array([3.0, 0.0]),
            lower=np.full(3, -np.inf),
            upper=np.full(3, np.inf),
            Q=np.eye(3),
            names=('x0', 'x1', 'x2'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 1.5, places=6)
        for j in range(3):
            self.assertAlmostEqual(r['x'][j], 1.0, places=6)

    def test_04_equality_plus_le_inequality(self):
        """4. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality + <= inequality."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 4, x0 <= 1
        # Minimizer x* = [1, 3], Obj = 1/2(1 + 9) = 5.0
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0], [1.0, 0.0]]),
            row_lower=np.array([4.0, -np.inf]),
            row_upper=np.array([4.0, 1.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 5.0, places=6)
        self.assertAlmostEqual(r['x'][0], 1.0, places=6)
        self.assertAlmostEqual(r['x'][1], 3.0, places=6)

    def test_05_equality_plus_ge_inequality(self):
        """5. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality + >= inequality."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 4, x0 >= 3
        # Minimizer x* = [3, 1], Obj = 1/2(9 + 1) = 5.0
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0], [1.0, 0.0]]),
            row_lower=np.array([4.0, 3.0]),
            row_upper=np.array([4.0, np.inf]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 5.0, places=6)
        self.assertAlmostEqual(r['x'][0], 3.0, places=6)
        self.assertAlmostEqual(r['x'][1], 1.0, places=6)

    def test_06_equality_plus_ranged_row(self):
        """6. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality + ranged row."""
        # min 1/2 (x0^2 + x1^2 + x2^2) s.t. x0 + x1 = 4, 1 <= x1 + x2 <= 2
        m = Model(
            c=np.zeros(3),
            A=np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0]]),
            row_lower=np.array([4.0, 1.0]),
            row_upper=np.array([4.0, 2.0]),
            lower=np.full(3, -np.inf),
            upper=np.full(3, np.inf),
            Q=np.eye(3),
            names=('x0', 'x1', 'x2'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])

    def test_07_equality_plus_lower_variable_bounds(self):
        """7. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality + lower variable bounds."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 1, x0 >= 2, x1 >= -5
        # Minimizer x* = [2, -1], Obj = 1/2(4 + 1) = 2.5
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([1.0]),
            row_upper=np.array([1.0]),
            lower=np.array([2.0, -5.0]),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 2.5, places=6)
        self.assertAlmostEqual(r['x'][0], 2.0, places=6)
        self.assertAlmostEqual(r['x'][1], -1.0, places=6)

    def test_08_equality_plus_upper_variable_bounds(self):
        """8. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality + upper variable bounds."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 4, x0 <= 1
        # Minimizer x* = [1, 3], Obj = 5.0
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([4.0]),
            row_upper=np.array([4.0]),
            lower=np.full(2, -np.inf),
            upper=np.array([1.0, 10.0]),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 5.0, places=6)
        self.assertAlmostEqual(r['x'][0], 1.0, places=6)
        self.assertAlmostEqual(r['x'][1], 3.0, places=6)

    def test_09_equality_plus_box_bounds(self):
        """9. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality + box bounds."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 5, 0 <= x0 <= 2, 0 <= x1 <= 4
        # Active at x0 = 2 -> x1 = 3. Obj = 1/2(4 + 9) = 6.5
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([5.0]),
            row_upper=np.array([5.0]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([2.0, 4.0]),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 6.5, places=6)
        self.assertAlmostEqual(r['x'][0], 2.0, places=6)
        self.assertAlmostEqual(r['x'][1], 3.0, places=6)

    def test_10_fixed_variable(self):
        """10. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] fixed variable."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 5, x0 fixed to 2 (lower=2, upper=2)
        # x0 = 2, x1 = 3. Obj = 6.5
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([5.0]),
            row_upper=np.array([5.0]),
            lower=np.array([2.0, 0.0]),
            upper=np.array([2.0, 10.0]),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 6.5, places=6)
        self.assertAlmostEqual(r['x'][0], 2.0, places=6)
        self.assertAlmostEqual(r['x'][1], 3.0, places=6)

    def test_11_redundant_equality(self):
        """11. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] redundant equality."""
        # min 1/2 (x0^2 + x1^2) s.t. x0 + x1 = 2 and 2 x0 + 2 x1 = 4
        # Regularized saddle-point solves rank deficiency smoothly
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0], [2.0, 2.0]]),
            row_lower=np.array([2.0, 4.0]),
            row_upper=np.array([2.0, 4.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 1.0, places=5)
        self.assertAlmostEqual(r['x'][0], 1.0, places=5)
        self.assertAlmostEqual(r['x'][1], 1.0, places=5)

    def test_12_near_dependent_equality_rows(self):
        """12. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] near-dependent equality rows."""
        eps = 1e-8
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0], [1.0, 1.0 + eps]]),
            row_lower=np.array([2.0, 2.0 + eps]),
            row_upper=np.array([2.0, 2.0 + eps]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 1.0, places=4)

    def test_13_zero_row_valid_equality(self):
        """13. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] zero-row valid equality."""
        # 0 x0 + 0 x1 = 0
        m = Model(
            c=np.array([-2.0, -4.0]),
            A=np.array([[0.0, 0.0]]),
            row_lower=np.array([0.0]),
            row_upper=np.array([0.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.array([[2.0, 0.0], [0.0, 4.0]]),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], -3.0, places=6)

    def test_14_infeasible_equality(self):
        """14. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] infeasible equality."""
        # x0 + x1 = 1 and x0 + x1 = 2 (incompatible)
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0], [1.0, 1.0]]),
            row_lower=np.array([1.0, 2.0]),
            row_upper=np.array([1.0, 2.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertIn(r['status'], ('LIMIT_REACHED', 'NUMERICAL_FAILURE'))
        self.assertFalse(r['verification']['feasible'])

    def test_15_semidefinite_q(self):
        """15. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] semidefinite Q."""
        # min 1/2 x0^2 + x1 s.t. x0 + x1 = 3, x1 >= 0
        # Q = diag([1, 0]), min at x0 = 1, x1 = 2. Obj = 0.5 + 2.0 = 2.5
        m = Model(
            c=np.array([0.0, 1.0]),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([3.0]),
            row_upper=np.array([3.0]),
            lower=np.array([-np.inf, 0.0]),
            upper=np.full(2, np.inf),
            Q=np.array([[1.0, 0.0], [0.0, 0.0]]),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 2.5, places=6)
        self.assertAlmostEqual(r['x'][0], 1.0, places=6)
        self.assertAlmostEqual(r['x'][1], 2.0, places=6)

    def test_16_diagonal_q(self):
        """16. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] diagonal Q."""
        # Different diagonal scales: Q = diag([100, 1]), c = [-10, -10]
        # x* = [0.1, 10.0]
        m = Model(
            c=np.array([-10.0, -10.0]),
            A=np.zeros((0, 2)),
            row_lower=np.zeros(0),
            row_upper=np.zeros(0),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.array([[100.0, 0.0], [0.0, 1.0]]),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['x'][0], 0.1, places=6)
        self.assertAlmostEqual(r['x'][1], 10.0, places=6)

    def test_17_off_diagonal_q(self):
        """17. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] off-diagonal Q."""
        # Q = [[4, 2], [2, 4]], c = [-6, -6], x0 + x1 = 2
        # x* = [1, 1], Obj = 1/2(12) - 12 = -6.0
        Q17 = np.array([[4.0, 2.0], [2.0, 4.0]])
        m = Model(
            c=np.array([-6.0, -6.0]),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([2.0]),
            row_upper=np.array([2.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=Q17,
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], -6.0, places=6)
        self.assertAlmostEqual(r['x'][0], 1.0, places=6)
        self.assertAlmostEqual(r['x'][1], 1.0, places=6)

    def test_18_nonzero_objective_offset(self):
        """18. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] nonzero objective offset."""
        # Offset 42.0 added to objective 1.0 gives reported 43.0
        m = Model(
            c=np.zeros(2),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([2.0]),
            row_upper=np.array([2.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            obj_offset=42.0,
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertAlmostEqual(r['objective'], 43.0, places=6)

    def test_19_feasible_infeasible_start_initialization(self):
        """19. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] feasible infeasible-start initialization."""
        # Nonzero initial equality residual is reduced during IPM iterations
        m = Model(
            c=np.array([1.0, 2.0]),
            A=np.array([[1.0, 2.0]]),
            row_lower=np.array([5.0]),
            row_upper=np.array([5.0]),
            lower=np.zeros(2),
            upper=np.full(2, 10.0),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        r = solve_qp(m)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(r['verification']['kkt_passed'])
        self.assertEqual(r['initialization_source'], 'SOVOPT_INTERNAL')
        self.assertFalse(r['reference_solution_used_as_initialization'])

    def test_20_equality_multiplier_unrestricted_sign(self):
        """20. [INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] equality multiplier unrestricted sign."""
        # Case A: y* < 0
        mA = Model(
            c=np.array([10.0, 0.0]),
            A=np.array([[1.0, 0.0]]),
            row_lower=np.array([1.0]),
            row_upper=np.array([1.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        rA = solve_qp(mA)
        # Case B: y* > 0
        mB = Model(
            c=np.array([-10.0, 0.0]),
            A=np.array([[1.0, 0.0]]),
            row_lower=np.array([1.0]),
            row_upper=np.array([1.0]),
            lower=np.full(2, -np.inf),
            upper=np.full(2, np.inf),
            Q=np.eye(2),
            names=('x0', 'x1'),
        )
        rB = solve_qp(mB)
        self.assertEqual(rA['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(rB['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(rA['verification']['kkt_passed'])
        self.assertTrue(rB['verification']['kkt_passed'])


if __name__ == '__main__':
    unittest.main()
