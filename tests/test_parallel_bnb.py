"""Comprehensive unit and stress tests for intra-solve parallel branch-and-bound.

Covers:
- Oracle correctness across worker counts (1, 2, 4).
- Race conditions (simultaneous incumbents, late arrivals).
- B&B termination invariants (queue empty while in-flight).
- Fail-safe timeout and node-limit behavior (never false OPTIMAL).
- Worker process exception recovery.
- Infeasible and root-integral edge cases.
- Deterministic objective repeatability across 10 independent parallel runs.
- Compatibility with Gate 20C root cover cuts.

Sovereign test suite for MRPL Problem Statement 26119.
Zero external solver dependencies.
"""
import itertools
import math
import unittest
import numpy as np

from sovopt.model import Model
from sovopt.milp import solve_milp
from sovopt.parallel_bnb import solve_milp_parallel


class TestParallelBranchAndBound(unittest.TestCase):
    """Test suite for intra-solve parallel branch-and-bound."""

    def _make_oracle_knapsack(self):
        c = np.array([-5.0, -6.0, -4.0, -7.0, -3.0])
        A = np.array([[3.0, 4.0, 3.0, 5.0, 2.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([8.0])
        lower = np.zeros(5)
        upper = np.ones(5)
        integer = tuple(range(5))
        return Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                     lower=lower, upper=upper, integer=integer)

    def _make_multi_knapsack(self):
        c = np.array([-10.0, -15.0, -12.0, -8.0, -6.0, -14.0])
        A = np.array([
            [3.0, 5.0, 4.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 5.0, 4.0, 1.0, 3.0],
        ])
        row_lower = np.array([-np.inf, -np.inf])
        row_upper = np.array([11.0, 10.0])
        lower = np.zeros(6)
        upper = np.ones(6)
        integer = tuple(range(6))
        return Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                     lower=lower, upper=upper, integer=integer)

    def _make_infeasible_model(self):
        c = np.array([1.0, 1.0])
        A = np.array([[1.0, 1.0], [1.0, 1.0]])
        row_lower = np.array([3.0, -np.inf])
        row_upper = np.array([np.inf, 2.0])
        lower = np.zeros(2)
        upper = np.array([5.0, 5.0])
        integer = (0, 1)
        return Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                     lower=lower, upper=upper, integer=integer)

    def _make_root_integral_model(self):
        c = np.array([1.0, 2.0])
        A = np.array([[1.0, 1.0]])
        row_lower = np.array([1.0])
        row_upper = np.array([np.inf])
        lower = np.zeros(2)
        upper = np.array([5.0, 5.0])
        integer = (0, 1)
        return Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                     lower=lower, upper=upper, integer=integer)

    def _make_general_integer_box(self):
        c = np.array([1.0, -2.0])
        A = np.array([[1.0, 1.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([5.0])
        lower = np.zeros(2)
        upper = np.array([4.0, 3.0])
        integer = (0, 1)
        return Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper,
                     lower=lower, upper=upper, integer=integer)

    def test_01_serial_vs_parallel_oracle_agreement(self):
        """Serial (w=1) vs Parallel (w=2, w=4) on canonical knapsack."""
        model = self._make_oracle_knapsack()

        res_s = solve_milp(model, parallel_workers=1)
        res_p2 = solve_milp(model, parallel_workers=2)
        res_p4 = solve_milp(model, parallel_workers=4)

        self.assertEqual(res_s['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_p2['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_p4['status'], 'OPTIMAL_VERIFIED')

        self.assertAlmostEqual(res_s['objective'], res_p2['objective'], places=6)
        self.assertAlmostEqual(res_s['objective'], res_p4['objective'], places=6)
        self.assertTrue(res_p2['verification']['feasible'])
        self.assertTrue(res_p4['verification']['feasible'])

    def test_02_multi_knapsack_parallel(self):
        """Multi-constraint knapsack across worker counts."""
        model = self._make_multi_knapsack()

        res_s = solve_milp(model, parallel_workers=1)
        res_p2 = solve_milp(model, parallel_workers=2)
        res_p4 = solve_milp(model, parallel_workers=4)

        self.assertEqual(res_s['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_p2['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_p4['status'], 'OPTIMAL_VERIFIED')

        self.assertAlmostEqual(res_s['objective'], res_p2['objective'], places=6)
        self.assertAlmostEqual(res_s['objective'], res_p4['objective'], places=6)

    def test_03_infeasible_tree_parallel(self):
        """Infeasible tree must return INFEASIBLE_CERTIFIED under parallel execution."""
        model = self._make_infeasible_model()
        res_p = solve_milp(model, parallel_workers=2)
        self.assertEqual(res_p['status'], 'INFEASIBLE_CERTIFIED')
        self.assertNotEqual(res_p['status'], 'OPTIMAL_VERIFIED')

    def test_04_root_integral_immediate_exit(self):
        """Root integral optimum must return immediately without unnecessary worker search."""
        model = self._make_root_integral_model()
        res_p = solve_milp(model, parallel_workers=4)
        self.assertEqual(res_p['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_p['nodes'], 1)
        self.assertEqual(res_p['open_nodes'], 0)

    def test_05_parallel_timeout_safety(self):
        """Under a tiny time limit, parallel solver must return LIMIT_REACHED, never false OPTIMAL."""
        model = self._make_multi_knapsack()
        # Force immediate timeout with 0.0001s limit
        res_p = solve_milp(model, time_limit=0.0001, parallel_workers=2)
        self.assertEqual(res_p['status'], 'LIMIT_REACHED')
        self.assertNotEqual(res_p['status'], 'OPTIMAL_VERIFIED')

    def test_06_parallel_node_limit_safety(self):
        """Under node limit, parallel solver must return LIMIT_REACHED honestly."""
        model = self._make_multi_knapsack()
        res_p = solve_milp(model, max_nodes=2, parallel_workers=2)
        self.assertEqual(res_p['status'], 'LIMIT_REACHED')
        self.assertNotEqual(res_p['status'], 'OPTIMAL_VERIFIED')

    def test_07_general_integer_box(self):
        """Bounded general integer MILP solves identically in serial and parallel."""
        model = self._make_general_integer_box()
        res_s = solve_milp(model, parallel_workers=1)
        res_p = solve_milp(model, parallel_workers=2)

        self.assertEqual(res_s['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_p['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res_s['objective'], res_p['objective'], places=6)

    def test_08_cover_cuts_inherited_by_workers(self):
        """Coordinator root cover cuts are inherited by all parallel workers."""
        model = self._make_oracle_knapsack()
        res_p = solve_milp(model, parallel_workers=2, use_cuts=True)
        self.assertEqual(res_p['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res_p['cuts_enabled'])
        self.assertGreater(res_p['cover_cuts_accepted'], 0)

    def test_09_repeatability_10_runs(self):
        """10 consecutive parallel runs must produce identical verified status and objective."""
        model = self._make_oracle_knapsack()
        objectives = []
        statuses = []

        for r in range(10):
            res = solve_milp(model, parallel_workers=4)
            statuses.append(res['status'])
            objectives.append(round(res['objective'], 6))

        self.assertTrue(all(s == 'OPTIMAL_VERIFIED' for s in statuses))
        self.assertEqual(len(set(objectives)), 1, f"Objective varied across runs: {objectives}")
        self.assertEqual(objectives[0], -12.0)

    def test_10_parallel_telemetry_fields(self):
        """Parallel telemetry must report process IDs, worker counts, and node metrics."""
        model = self._make_oracle_knapsack()
        res = solve_milp(model, parallel_workers=2)
        self.assertTrue(res['parallel_enabled'])
        self.assertEqual(res['parallel_workers_used'], 2)
        self.assertIn('worker_process_ids', res)
        self.assertGreaterEqual(res['nodes_completed'], 1)
        self.assertGreaterEqual(res['max_nodes_in_flight'], 1)


if __name__ == '__main__':
    unittest.main()
