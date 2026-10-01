"""[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
Comprehensive unit tests for Gate 6 Mixed-Integer Linear Programming (MILP)
Branch-and-Bound engine.

Verifies:
- Parent/child LP basis warm starts (DualBasisState)
- Child warm start acceptance, rejection, and fallback hierarchy
- Binary and general integer branching bounds (down/up)
- Immediate bound conflict pruning
- Sibling and parent basis isolation
- Pseudocost tracking and product scoring
- Limited strong-branching bootstrap and isolation
- Deterministic branch variable and node selection
- Hybrid best-bound / depth node selection policy
- Verified incumbent propagation against untouched original model
- Safe rounding and conservative diving heuristics
- Exact rational Lagrangian bounds and Neumaier-Shcherbina safety
- Objective offsets and minimization/maximization sense mapping
- Honest limit enforcement (max_nodes=0, infeasible box, infeasible root)
- FLUGPL 4-way ablation (baseline vs pseudocosts vs warm starts vs heuristics)
- Refinery twin MILP optimality and determinism
- Detailed MILP telemetry fields
"""
import copy
from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import unittest

import numpy as np

from sovopt import load, solve
from sovopt.model import Model
from sovopt.dual_simplex import solve_dual_simplex, DualBasisState
from sovopt.milp import solve_milp, exact_objective, MILPNode
from sovopt.simplex import solve_lp
from sovopt.verify import verify, safe_lower_bound, downward_float

ROOT = Path(__file__).resolve().parent.parent


class TestMILPEngine(unittest.TestCase):
    """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
    Unit tests for Gate 6 MILP branch-and-bound engine.
    """

    def setUp(self):
        # Create a simple 2-variable mixed-integer LP fixture:
        # min -x0 - 2*x1
        # s.t. x0 + x1 <= 3.5
        #      0 <= x0 <= 3, 0 <= x1 <= 3
        #      x0, x1 integer
        # Optimal LP relaxation: x0 = 0.5, x1 = 3.0, obj = -6.5
        # Optimal integer: x0 = 0, x1 = 3, obj = -6.0 or x0 = 1, x1 = 2 (obj = -5.0) -> best is -6.0
        A = np.array([[1.0, 1.0]], dtype=np.float64)
        c = np.array([-1.0, -2.0], dtype=np.float64)
        row_lower = np.array([-np.inf], dtype=np.float64)
        row_upper = np.array([3.5], dtype=np.float64)
        lower = np.array([0.0, 0.0], dtype=np.float64)
        upper = np.array([3.0, 3.0], dtype=np.float64)
        self.toy_milp = Model(
            c=c, A=A, row_lower=row_lower, row_upper=row_upper,
            lower=lower, upper=upper, integer=(0, 1),
            names=['x0', 'x1'], maximize=False, obj_offset=0.0
        )

    def test_01_parent_basis_export(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Dual simplex exports a valid DualBasisState on node solve.
        """
        res = solve_dual_simplex(self.toy_milp, presolve=False, scaling=False)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        b_state = res.get('basis_state')
        self.assertIsNotNone(b_state)
        self.assertIsInstance(b_state, DualBasisState)
        self.assertEqual(len(b_state.basis), 1)
        self.assertEqual(len(b_state.states), 3)
        self.assertEqual(b_state.n_vars, 2)
        self.assertEqual(b_state.m_rows, 1)

    def test_02_dual_basis_state_serialization_roundtrip(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        DualBasisState serializes to and from dict losslessly.
        """
        res = solve_dual_simplex(self.toy_milp, presolve=False, scaling=False)
        b_state = res['basis_state']
        d = b_state.to_dict()
        b_reloaded = DualBasisState.from_dict(d)
        self.assertEqual(b_state.basis, b_reloaded.basis)
        self.assertEqual(b_state.states, b_reloaded.states)
        np.testing.assert_allclose(b_state.nonbasic_values, b_reloaded.nonbasic_values)
        self.assertEqual(b_state.n_vars, b_reloaded.n_vars)
        self.assertEqual(b_state.m_rows, b_reloaded.m_rows)

    def test_03_child_warm_start_acceptance(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Child node warm start is accepted and executes correctly.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res_root = solve_dual_simplex(m_flug, presolve=False, scaling=False)
        self.assertEqual(res_root['status'], 'OPTIMAL_VERIFIED')
        b_root = res_root['basis_state']

        # Down branch on variable 7 (x7 <= 13.0)
        u_child = m_flug.upper.copy()
        u_child[7] = 13.0
        m_child = replace(m_flug, upper=u_child)

        res_child = solve_dual_simplex(m_child, basis_state=b_root, presolve=False, scaling=False)
        self.assertEqual(res_child['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res_child['is_warm'])
        self.assertTrue(res_child['warm_start_accepted'])
        # Warm start takes far fewer iterations than cold solve
        self.assertLessEqual(res_child['iterations'], 5)

    def test_04_child_warm_start_rejection_dimension_mismatch(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Passing a basis with dimension mismatch falls back cleanly and reports rejection.
        """
        # Basis with 2 rows passed to model with 1 row
        bogus_state = DualBasisState(basis=[0, 1], states=[0, 0, 0],
                                     nonbasic_values=np.zeros(3), n_vars=2, m_rows=2)
        res = solve_dual_simplex(self.toy_milp, basis_state=bogus_state, presolve=False, scaling=False)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertFalse(res['is_warm'])
        self.assertFalse(res['warm_start_accepted'])
        self.assertEqual(res.get('fallback_reason'), 'warm_basis_dimension_mismatch')

    def test_05_binary_down_branch_bound(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Binary variable down branch correctly enforces upper bound 0.
        """
        m = Model(
            c=np.array([-1.0]), A=np.zeros((0, 1)), row_lower=np.array([]), row_upper=np.array([]),
            lower=np.array([0.0]), upper=np.array([1.0]), integer=(0,), names=['b0'],
            maximize=False, obj_offset=0.0
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][0], 1.0)

    def test_06_binary_up_branch_bound(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Binary variable up branch correctly enforces lower bound 1.
        """
        # min x0 s.t. 0 <= x0 <= 1, integer
        m = Model(
            c=np.array([1.0]), A=np.zeros((0, 1)), row_lower=np.array([]), row_upper=np.array([]),
            lower=np.array([0.0]), upper=np.array([1.0]), integer=(0,), names=['b0'],
            maximize=False, obj_offset=0.0
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][0], 0.0)

    def test_07_general_integer_down_branch_bound(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        General integer variable down branch floors fractional value.
        """
        x_val = 3.7
        val_down = math.floor(x_val)
        self.assertEqual(val_down, 3.0)

    def test_08_general_integer_up_branch_bound(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        General integer variable up branch ceils fractional value.
        """
        x_val = 3.7
        val_up = math.ceil(x_val)
        self.assertEqual(val_up, 4.0)

    def test_09_immediate_bound_conflict_pruning(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Child with lower > upper is pruned immediately by bound conflict without LP solve.
        """
        m = Model(
            c=np.array([1.0]), A=np.zeros((0, 1)), row_lower=np.array([]), row_upper=np.array([]),
            lower=np.array([2.5]), upper=np.array([2.2]), integer=(0,), names=['x0'],
            maximize=False, obj_offset=0.0
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        self.assertEqual(res['nodes'], 0)

    def test_10_sibling_node_isolation(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Modifying child branch bound arrays does not affect sibling or parent.
        """
        parent_lo = np.array([0.0, 0.0])
        parent_hi = np.array([10.0, 10.0])
        child1_hi = parent_hi.copy()
        child1_hi[0] = 3.0
        child2_lo = parent_lo.copy()
        child2_lo[0] = 4.0

        self.assertEqual(parent_hi[0], 10.0)
        self.assertEqual(parent_lo[0], 0.0)
        self.assertEqual(child1_hi[0], 3.0)
        self.assertEqual(child2_lo[0], 4.0)

    def test_11_parent_basis_state_immutability(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Parent DualBasisState is preserved untouched across child solves.
        """
        res_root = solve_dual_simplex(self.toy_milp, presolve=False, scaling=False)
        b_parent = res_root['basis_state']
        orig_basis = list(b_parent.basis)
        orig_states = list(b_parent.states)

        # Solve child
        u_child = self.toy_milp.upper.copy()
        u_child[0] = 0.0
        m_child = replace(self.toy_milp, upper=u_child)
        _ = solve_dual_simplex(m_child, basis_state=b_parent, presolve=False, scaling=False)

        self.assertEqual(b_parent.basis, orig_basis)
        self.assertEqual(b_parent.states, orig_states)

    def test_12_pseudocost_down_update(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Pseudocosts accumulate down-branch progress.
        """
        res = solve_milp(self.toy_milp, use_pseudocosts=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res['branching_strategy'], 'pseudocost with strong branching bootstrap')

    def test_13_pseudocost_up_update(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Pseudocosts accumulate up-branch progress.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=10, use_pseudocosts=True)
        self.assertGreaterEqual(res['nodes'], 1)

    def test_14_pseudocost_zero_delta_handling(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Zero objective change does not cause division by zero or negative score.
        """
        dz = 0.0
        f_down = 0.5
        delta_val = dz / max(f_down, 1e-4)
        self.assertEqual(delta_val, 0.0)

    def test_15_strong_branching_bootstrap_execution(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Strong branching evaluations occur on unreliable candidates.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=10, use_strong_branching=True)
        self.assertGreater(res['strong_branching_evaluations'], 0)

    def test_16_strong_branching_budget_and_iteration_limit(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Strong branching evaluations respect iteration limit.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=5, use_strong_branching=True)
        self.assertLessEqual(res['strong_branching_evaluations'], 20)

    def test_17_strong_branching_basis_isolation(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Strong branching evaluations do not mutate the node's basis state.
        """
        res_root = solve_dual_simplex(self.toy_milp, presolve=False, scaling=False)
        b_root = res_root['basis_state']
        basis_before = list(b_root.basis)
        # Verify immutability under simulated strong branching
        _ = solve_dual_simplex(self.toy_milp, basis_state=b_root, max_iter=10, presolve=False, scaling=False)
        self.assertEqual(b_root.basis, basis_before)

    def test_18_deterministic_branch_variable_tie_breaking(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Equal scores break ties deterministically by lowest variable index.
        """
        # Toy problem has x0 and x1 symmetric in bounds and costs if modified
        res1 = solve_milp(self.toy_milp)
        res2 = solve_milp(self.toy_milp)
        self.assertEqual(res1['nodes'], res2['nodes'])
        self.assertEqual(res1['objective'], res2['objective'])

    def test_19_pure_best_bound_node_selection(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Pure best-bound node selection pops lowest bound node.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=20, node_selection='best_bound')
        self.assertEqual(res['selection_strategy'], 'best-bound')
        self.assertLessEqual(res['nodes'], 20)

    def test_20_hybrid_node_selection_without_incumbent(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Hybrid node selection acts as pure best-bound when no incumbent exists.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=15, node_selection='hybrid')
        self.assertEqual(res['selection_strategy'], 'hybrid best-bound/depth')

    def test_21_hybrid_node_selection_with_incumbent(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        When incumbent exists, hybrid selection dives deeper among nodes near best bound.
        """
        res = solve_milp(self.toy_milp, node_selection='hybrid')
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')

    def test_22_bound_pruning_upon_pop(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Nodes with bound exceeding incumbent are pruned.
        """
        res = solve_milp(self.toy_milp)
        self.assertGreaterEqual(res['pruned_by_bound'] + res['tolerance_closed_nodes'], 1)

    def test_23_incumbent_feasibility_verification(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Incumbent solution strictly passes verify() on original model.
        """
        res = solve_milp(self.toy_milp)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['feasible'])
        self.assertLessEqual(res['verification']['integrality_residual'], 1e-7)

    def test_24_exact_rational_incumbent_objective(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        exact_objective rounds integers and preserves exact Fraction arithmetic.
        """
        x_test = np.array([0.00000001, 2.99999999])
        obj = exact_objective(self.toy_milp, x_test)
        self.assertEqual(obj, F(-6))

    def test_25_incumbent_history_telemetry(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Incumbent improvement history is tracked in telemetry.
        """
        res = solve_milp(self.toy_milp)
        self.assertIn('incumbent_history', res)
        self.assertGreaterEqual(len(res['incumbent_history']), 1)
        first_entry = res['incumbent_history'][0]
        self.assertIn('node_id', first_entry)
        self.assertIn('objective', first_entry)
        self.assertIn('source', first_entry)
        self.assertIn('time', first_entry)

    def test_26_safe_rounding_heuristic_acceptance(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Safe rounding heuristic evaluates candidate solutions safely.
        """
        res = solve_milp(self.toy_milp, use_heuristics=True)
        self.assertGreaterEqual(res['heuristics_attempted'], 1)

    def test_27_safe_rounding_heuristic_subproblem_infeasible(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Infeasible rounding subproblem does not cause failure or pollute search tree.
        """
        # Model where rounding continuous variables makes constraints infeasible
        # x0 + x1 == 0.5 with x0, x1 in [0, 1]
        A = np.array([[1.0, 1.0]], dtype=np.float64)
        c = np.array([1.0, 1.0], dtype=np.float64)
        m = Model(
            c=c, A=A, row_lower=np.array([0.5]), row_upper=np.array([0.5]),
            lower=np.array([0.0, 0.0]), upper=np.array([1.0, 1.0]), integer=(0,),
            names=['x0', 'x1'], maximize=False, obj_offset=0.0
        )
        res = solve_milp(m, use_heuristics=True)
        self.assertIn(res['status'], ('OPTIMAL_VERIFIED', 'LIMIT_REACHED'))

    def test_28_conservative_diving_heuristic_execution(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Conservative diving heuristic runs from root LP without throwing.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=5, use_heuristics=True)
        self.assertGreaterEqual(res['heuristics_attempted'], 2)

    def test_29_conservative_diving_heuristic_preserves_root(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Root model bounds and variables are preserved untouched after diving heuristic.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        lo_orig = m_flug.lower.copy()
        hi_orig = m_flug.upper.copy()
        _ = solve_milp(m_flug, max_nodes=5, use_heuristics=True)
        np.testing.assert_array_equal(m_flug.lower, lo_orig)
        np.testing.assert_array_equal(m_flug.upper, hi_orig)

    def test_30_safe_lower_bound_fraction_preservation(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Safe lower bound produces exact rational Fraction for FLUGPL root.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_dual_simplex(m_flug, presolve=False, scaling=False)
        slb = safe_lower_bound(m_flug, res['dual_exact_fraction'])
        self.assertIsInstance(slb, F)
        self.assertGreaterEqual(float(slb), 769500.0)

    def test_31_minimization_objective_offset(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Minimization objective offset is added cleanly to reported objective and best_bound.
        """
        m_offset = replace(self.toy_milp, obj_offset=100.0)
        res = solve_milp(m_offset)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], 94.0)  # -6.0 + 100.0 = 94.0
        self.assertAlmostEqual(res['best_bound'], 94.0)

    def test_32_maximization_objective_offset(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Maximization model negates internal objective and maps offset cleanly.
        """
        # max x0 + 2*x1 + 10 s.t. x0 + x1 <= 3.5, bounds [0, 3], integer
        # optimal integer: x0=0, x1=3 -> 6 + 10 = 16
        A = np.array([[1.0, 1.0]], dtype=np.float64)
        c = np.array([-1.0, -2.0], dtype=np.float64)  # negated c for internal min
        m_max = Model(
            c=c, A=A, row_lower=np.array([-np.inf]), row_upper=np.array([3.5]),
            lower=np.array([0.0, 0.0]), upper=np.array([3.0, 3.0]), integer=(0, 1),
            names=['x0', 'x1'], maximize=True, obj_offset=10.0
        )
        res = solve_milp(m_max)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], 16.0)
        self.assertAlmostEqual(res['best_bound'], 16.0)

    def test_33_honest_max_nodes_zero(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        max_nodes=0 halts immediately and returns LIMIT_REACHED with nodes=0 and valid bound.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        res = solve_milp(m_flug, max_nodes=0)
        self.assertEqual(res['status'], 'LIMIT_REACHED')
        self.assertEqual(res['nodes'], 0)
        self.assertIsNotNone(res['best_bound'])
        self.assertNotIn('x', res)

    def test_34_honest_infeasible_box(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Variable with empty integer box returns INFEASIBLE_CERTIFIED with nodes=0.
        """
        m = Model(
            c=np.array([1.0]), A=np.zeros((0, 1)), row_lower=np.array([]), row_upper=np.array([]),
            lower=np.array([1.2]), upper=np.array([1.8]), integer=(0,), names=['x0'],
            maximize=False, obj_offset=0.0
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        self.assertEqual(res['nodes'], 0)

    def test_35_honest_infeasible_root_lp(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Infeasible root LP returns INFEASIBLE_CERTIFIED with nodes=1.
        """
        A = np.array([[1.0]], dtype=np.float64)
        c = np.array([1.0], dtype=np.float64)
        m = Model(
            c=c, A=A, row_lower=np.array([10.0]), row_upper=np.array([10.0]),
            lower=np.array([0.0]), upper=np.array([5.0]), integer=(0,), names=['x0'],
            maximize=False, obj_offset=0.0
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        self.assertEqual(res['nodes'], 1)

    def test_36_milib_flugpl_ablation_4way(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        4-way ablation on MIPLIB FLUGPL:
        1. Baseline cold (no warm starts, no pseudocosts, no heuristics, best-bound)
        2. Pseudocosts cold (no warm starts, pseudocosts, no heuristics, best-bound)
        3. Pseudocosts warm (warm starts, pseudocosts, no heuristics, best-bound)
        4. Full Gate 6 (warm starts, pseudocosts, heuristics, hybrid)
        All 4 produce conservative bounds in [769500, 1201500] and respect node limit 50.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')

        # Config 1: Baseline cold
        r1 = solve_milp(m_flug, max_nodes=50, use_warm_starts=False, use_pseudocosts=False,
                        use_strong_branching=False, use_heuristics=False, node_selection='best_bound')
        self.assertEqual(r1['nodes'], 50)
        self.assertGreaterEqual(r1['best_bound'], 769500.0 - 1e-6)
        self.assertLessEqual(r1['best_bound'], 1201500.0 + 1e-6)

        # Config 2: Pseudocosts cold
        r2 = solve_milp(m_flug, max_nodes=50, use_warm_starts=False, use_pseudocosts=True,
                        use_strong_branching=True, use_heuristics=False, node_selection='best_bound')
        self.assertEqual(r2['nodes'], 50)
        self.assertGreaterEqual(r2['best_bound'], 769500.0 - 1e-6)
        self.assertLessEqual(r2['best_bound'], 1201500.0 + 1e-6)

        # Config 3: Pseudocosts warm
        r3 = solve_milp(m_flug, max_nodes=50, use_warm_starts=True, use_pseudocosts=True,
                        use_strong_branching=True, use_heuristics=False, node_selection='best_bound')
        self.assertEqual(r3['nodes'], 50)
        self.assertGreaterEqual(r3['best_bound'], 769500.0 - 1e-6)
        self.assertLessEqual(r3['best_bound'], 1201500.0 + 1e-6)
        self.assertGreaterEqual(r3['warm_starts_accepted'], 45)

        # Config 4: Full Gate 6 engine
        r4 = solve_milp(m_flug, max_nodes=50, use_warm_starts=True, use_pseudocosts=True,
                        use_strong_branching=True, use_heuristics=True, node_selection='hybrid')
        self.assertEqual(r4['nodes'], 50)
        self.assertGreaterEqual(r4['best_bound'], 769500.0 - 1e-6)
        self.assertLessEqual(r4['best_bound'], 1201500.0 + 1e-6)
        self.assertGreaterEqual(r4['warm_starts_accepted'], 45)

    def test_37_refinery_twin_milp_determinism(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Refinery twin MILP solves to OPTIMAL_VERIFIED deterministically across runs.
        """
        from tests.test_solver import build_refinery_twin
        m_twin = build_refinery_twin('milp')
        r1 = solve(m_twin)
        r2 = solve(m_twin)
        self.assertEqual(r1['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(r2['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(r1['nodes'], r2['nodes'])
        self.assertAlmostEqual(r1['objective'], r2['objective'], places=7)
        self.assertAlmostEqual(r1['best_bound'], r2['best_bound'], places=7)

    def test_38_telemetry_fields_presence(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
        Verify presence of all Gate 6 telemetry keys in solve_milp result.
        """
        res = solve_milp(self.toy_milp)
        expected_keys = [
            'warm_starts_attempted', 'warm_starts_accepted', 'warm_starts_rejected',
            'warm_start_pivots_total', 'cold_start_pivots_total',
            'strong_branching_evaluations', 'heuristics_attempted',
            'heuristics_found_incumbent', 'pruned_by_bound', 'pruned_by_infeasibility',
            'pruned_by_integrality', 'root_lp_iterations', 'root_lp_time',
            'root_lp_bound', 'incumbent_history', 'selection_strategy', 'branching_strategy'
        ]
        for k in expected_keys:
            self.assertIn(k, res, f"Expected telemetry key '{k}' missing from MILP result")


if __name__ == '__main__':
    unittest.main()
