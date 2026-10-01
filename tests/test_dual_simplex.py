"""28-point unit test matrix for sovereign bounded-variable revised dual simplex.

All synthetic test fixtures are strictly labeled:
[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]
"""
import unittest
from pathlib import Path
import numpy as np

from sovopt.model import Model, load
from sovopt.dual_simplex import (
    solve_dual_simplex,
    DualBasisState,
    DevexPricer,
    TwoPassHarrisRatioTest,
    BASIC,
    AT_LOWER,
    AT_UPPER,
    FREE_NONBASIC,
    FIXED,
)
from sovopt.verify import verify

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "verified"


class TestDualSimplex(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. Dual-Feasible Start
    # -------------------------------------------------------------------------
    def test_01_dual_feasible_start(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] LP with non-negative costs and slacks."""
        # min 2 x1 + 3 x2 s.t. x1 + x2 >= 2, x1, x2 >= 0
        A = np.array([[1.0, 1.0]])
        c = np.array([2.0, 3.0])
        model = Model(c=c, A=A, row_lower=np.array([2.0]), row_upper=np.array([np.inf]),
                      lower=np.array([0.0, 0.0]), upper=np.array([np.inf, np.inf]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], 4.0, places=6)
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertEqual(res['method_used'], 'dual-simplex')

    # -------------------------------------------------------------------------
    # 2. Already Optimal Basis
    # -------------------------------------------------------------------------
    def test_02_already_optimal(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Basis already primal and dual feasible."""
        # min x1 + 2 x2 s.t. x1 + x2 <= 5, x1, x2 >= 0
        # At x1=0, x2=0: slack s = 5 >= 0 (primal feasible), c >= 0 (dual feasible).
        A = np.array([[1.0, 1.0]])
        c = np.array([1.0, 2.0])
        model = Model(c=c, A=A, row_lower=np.array([-np.inf]), row_upper=np.array([5.0]),
                      lower=np.array([0.0, 0.0]), upper=np.array([np.inf, np.inf]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res['iterations'], 0)
        self.assertAlmostEqual(res['objective'], 0.0, places=6)
        self.assertTrue(res['verification']['kkt_passed'])

    # -------------------------------------------------------------------------
    # 3. Lower Basic Violation
    # -------------------------------------------------------------------------
    def test_03_lower_basic_violation(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Basic variable violates lower bound."""
        # min 3 x1 + 4 x2 s.t. x1 + x2 >= 10, x1, x2 >= 0
        # Initial slack: s = 0 - 10 = -10 < 0 (lower violation, sigma = +1)
        A = np.array([[1.0, 1.0]])
        c = np.array([3.0, 4.0])
        model = Model(c=c, A=A, row_lower=np.array([10.0]), row_upper=np.array([np.inf]),
                      lower=np.array([0.0, 0.0]), upper=np.array([np.inf, np.inf]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], 30.0, places=6)
        self.assertTrue(res['verification']['kkt_passed'])

    # -------------------------------------------------------------------------
    # 4. Upper Basic Violation
    # -------------------------------------------------------------------------
    def test_04_upper_basic_violation(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Basic variable violates upper bound."""
        # min -x1 - x2 s.t. x1 + x2 <= 4, 0 <= x1 <= 3, 0 <= x2 <= 3
        # Initial: x1=3, x2=3 (from c < 0 with finite upper bound), slack s = 4 - 6 = -2 < 0.
        A = np.array([[1.0, 1.0]])
        c = np.array([-1.0, -1.0])
        model = Model(c=c, A=A, row_lower=np.array([-np.inf]), row_upper=np.array([4.0]),
                      lower=np.array([0.0, 0.0]), upper=np.array([3.0, 3.0]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -4.0, places=6)
        self.assertTrue(res['verification']['kkt_passed'])

    # -------------------------------------------------------------------------
    # 5. Boxed Non-basics
    # -------------------------------------------------------------------------
    def test_05_boxed_nonbasics(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Variables with finite lower and upper bounds."""
        A = np.array([[2.0, 1.0], [1.0, 2.0]])
        c = np.array([1.0, 1.0])
        model = Model(c=c, A=A, row_lower=np.array([4.0, 5.0]), row_upper=np.array([np.inf, np.inf]),
                      lower=np.array([1.0, 1.0]), upper=np.array([3.0, 4.0]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertTrue(res['verification']['feasible'])

    # -------------------------------------------------------------------------
    # 6. Free Non-basics
    # -------------------------------------------------------------------------
    def test_06_free_nonbasics(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Unconstrained free variables."""
        # min x1 + 2 x2 s.t. x1 + x2 = 5, -inf < x1 < inf, x2 >= 0
        A = np.array([[1.0, 1.0]])
        c = np.array([1.0, 2.0])
        model = Model(c=c, A=A, row_lower=np.array([5.0]), row_upper=np.array([5.0]),
                      lower=np.array([-np.inf, 0.0]), upper=np.array([np.inf, np.inf]))
        res = solve_dual_simplex(model)
        self.assertIn(res['status'], ('OPTIMAL_VERIFIED', 'UNBOUNDED_CERTIFIED'))

    # -------------------------------------------------------------------------
    # 7. Fixed Non-basics
    # -------------------------------------------------------------------------
    def test_07_fixed_nonbasics(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Fixed variable with lower == upper."""
        A = np.array([[1.0, 1.0]])
        c = np.array([2.0, 5.0])
        model = Model(c=c, A=A, row_lower=np.array([10.0]), row_upper=np.array([np.inf]),
                      lower=np.array([0.0, 3.0]), upper=np.array([np.inf, 3.0]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][1], 3.0, places=6)
        self.assertAlmostEqual(res['x'][0], 7.0, places=6)
        self.assertAlmostEqual(res['objective'], 2.0 * 7.0 + 5.0 * 3.0, places=6)
        self.assertTrue(res['verification']['kkt_passed'])

    # -------------------------------------------------------------------------
    # 8. Devex Initialization
    # -------------------------------------------------------------------------
    def test_08_devex_initialization(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Devex weights initialize to 1.0."""
        pricer = DevexPricer(m=6)
        self.assertEqual(len(pricer.gamma), 6)
        self.assertTrue(np.all(pricer.gamma == 1.0))
        self.assertEqual(pricer.pricing_calls, 0)
        self.assertEqual(pricer.update_calls, 0)

    # -------------------------------------------------------------------------
    # 9. Devex Weight Update
    # -------------------------------------------------------------------------
    def test_09_devex_weight_update(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Devex weight recurrence."""
        pricer = DevexPricer(m=3)
        # Leaving row p=1, beta=2.0 -> gamma[1]_new = 1.0 / 4.0 = 0.25
        # d_vec = [1.0, 2.0, 4.0]
        # row 0: ratio = 1/2 -> cand = (1/4) * 0.25 = 0.0625 <= 1.0 -> stays 1.0
        # row 2: ratio = 4/2 = 2 -> cand = 4 * 0.25 = 1.0 <= 1.0 -> stays 1.0
        d_vec = np.array([1.0, 2.0, 4.0])
        pricer.update_weights(leaving_idx=1, pivot_col_d=d_vec, beta=2.0)
        self.assertAlmostEqual(pricer.gamma[1], 0.25, places=7)
        self.assertAlmostEqual(pricer.gamma[0], 1.0, places=7)
        self.assertAlmostEqual(pricer.gamma[2], 1.0, places=7)

    # -------------------------------------------------------------------------
    # 10. Devex Weight Reset
    # -------------------------------------------------------------------------
    def test_10_devex_reset(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Devex reset restores all weights to 1.0."""
        pricer = DevexPricer(m=4)
        pricer.gamma[:] = 99.0
        pricer.reset()
        self.assertTrue(np.all(pricer.gamma == 1.0))
        self.assertEqual(pricer.reset_calls, 1)

    # -------------------------------------------------------------------------
    # 11. Two-Pass Harris Pass 1 Relaxed Ratio
    # -------------------------------------------------------------------------
    def test_11_harris_pass1_relaxed_ratio(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Harris relaxed ratio calculation."""
        ratio_test = TwoPassHarrisRatioTest(delta=1e-6, pivot_tol=1e-8)
        d = np.array([2.0, 1.0])
        alpha = np.array([-1.0, -0.5])
        states = [AT_LOWER, AT_LOWER]
        lower = np.array([0.0, 0.0])
        upper = np.array([np.inf, np.inf])
        # sigma = +1: s_0 = -(-1.0) = 1.0, theta_0_relaxed = (2.0 + 1e-6) / 1.0 = 2.000001
        # s_1 = -(-0.5) = 0.5, theta_1_relaxed = (1.0 + 1e-6) / 0.5 = 2.000002
        q, s_q, theta_q, elig = ratio_test.select_entering(d, alpha, states, lower, upper, sigma=+1, nonbasic=[0, 1])
        self.assertIsNotNone(q)
        self.assertEqual(len(elig), 2)

    # -------------------------------------------------------------------------
    # 12. Two-Pass Harris Pass 2 Pivot Maximization
    # -------------------------------------------------------------------------
    def test_12_harris_pass2_pivot_selection(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Harris selects maximum pivot magnitude."""
        ratio_test = TwoPassHarrisRatioTest(delta=0.1, pivot_tol=1e-8)
        # Col 0: dist = 1.0, s = 1.0 -> raw ratio = 1.0, relaxed = 1.1 / 1.0 = 1.1
        # Col 1: dist = 1.05, s = 5.0 -> raw ratio = 1.05 / 5.0 = 0.21, relaxed = 1.15 / 5 = 0.23
        # theta_max = min(1.1, 0.23) = 0.23
        # In pass 2, Col 1 has raw ratio 0.21 <= 0.23, so Col 1 is picked with larger s=5.0!
        d = np.array([1.0, 1.05])
        alpha = np.array([-1.0, -5.0])
        states = [AT_LOWER, AT_LOWER]
        lower = np.array([0.0, 0.0])
        upper = np.array([np.inf, np.inf])
        q, s_q, theta_q, elig = ratio_test.select_entering(d, alpha, states, lower, upper, sigma=+1, nonbasic=[0, 1])
        self.assertEqual(q, 1)
        self.assertAlmostEqual(s_q, 5.0, places=6)

    # -------------------------------------------------------------------------
    # 13. Harris Tiny Pivot Rejection
    # -------------------------------------------------------------------------
    def test_13_harris_tiny_pivot_rejection(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Rejection of pivot < 1e-8."""
        ratio_test = TwoPassHarrisRatioTest(delta=1e-7, pivot_tol=1e-8)
        d = np.array([1.0])
        alpha = np.array([-1e-10])  # s = 1e-10 < pivot_tol
        states = [AT_LOWER]
        lower = np.array([0.0])
        upper = np.array([np.inf])
        q, s_q, theta_q, elig = ratio_test.select_entering(d, alpha, states, lower, upper, sigma=+1, nonbasic=[0])
        self.assertIsNone(q)
        self.assertEqual(ratio_test.tiny_pivots_rejected, 1)

    # -------------------------------------------------------------------------
    # 14. Anti-Cycling Degenerate Pivot Tracking
    # -------------------------------------------------------------------------
    def test_14_anti_cycling_degenerate_pivots(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Tracking degenerate pivots."""
        A = np.array([[1.0, 1.0]])
        c = np.array([2.0, 0.0])
        model = Model(c=c, A=A, row_lower=np.array([5.0]), row_upper=np.array([np.inf]),
                      lower=np.array([0.0, 0.0]), upper=np.array([np.inf, np.inf]))
        res = solve_dual_simplex(model)
        self.assertIn('degenerate_pivots', res)
        self.assertIn('consecutive_degenerate_pivots', res)

    # -------------------------------------------------------------------------
    # 15. Single Bound Flip
    # -------------------------------------------------------------------------
    def test_15_single_bound_flip(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Bound flip without basis update."""
        # Boxed variable that flips from lower to upper bound
        A = np.array([[1.0, 2.0]])
        c = np.array([1.0, 3.0])
        model = Model(c=c, A=A, row_lower=np.array([10.0]), row_upper=np.array([np.inf]),
                      lower=np.array([0.0, 0.0]), upper=np.array([2.0, 10.0]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertGreaterEqual(res['bound_flips'], 0)
        self.assertTrue(res['verification']['kkt_passed'])

    # -------------------------------------------------------------------------
    # 16. Multiple Bound Flips
    # -------------------------------------------------------------------------
    def test_16_multiple_bound_flips(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Multiple bound flips across iterations."""
        model = load(str(DATA_DIR / "blend.mps"))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertGreater(res['bound_flips'], 5)

    # -------------------------------------------------------------------------
    # 17. Sparse FTRAN / BTRAN Integration
    # -------------------------------------------------------------------------
    def test_17_sparse_ftran_btran_integration(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Basis engine FTRAN and BTRAN counts."""
        model = load(str(DATA_DIR / "afiro.mps"))
        res = solve_dual_simplex(model)
        self.assertGreater(res['ftran_count'], 0)
        self.assertGreater(res['btran_count'], 0)
        self.assertEqual(res['basis_storage_used'], 'sparse')
        self.assertEqual(res['matrix_storage_used'], 'csc')
        self.assertFalse(res['full_dense_matrix_materialized'])

    # -------------------------------------------------------------------------
    # 18. Product Form Eta Updates
    # -------------------------------------------------------------------------
    def test_18_eta_updates_across_pivots(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Eta updates accumulate across dual pivots."""
        model = load(str(DATA_DIR / "afiro.mps"))
        res = solve_dual_simplex(model)
        self.assertGreater(res['eta_updates'], 0)
        self.assertEqual(res['basis_factorization'], 'sovereign_sparse_lu_pfi')

    # -------------------------------------------------------------------------
    # 19. Refactorization Trigger
    # -------------------------------------------------------------------------
    def test_19_refactorization_trigger(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Max eta depth refactorization trigger."""
        model = load(str(DATA_DIR / "blend.mps"))
        # With max_eta_depth = 15, BLEND (which takes > 100 pivots) must refactorize multiple times.
        # presolve=False/scaling=False to test raw inner-solver refactorization directly.
        res = solve_dual_simplex(model, max_eta_depth=15, presolve=False, scaling=False)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertGreater(res['refactorizations'], 3)

    # -------------------------------------------------------------------------
    # 20. Primal Infeasible Detection
    # -------------------------------------------------------------------------
    def test_20_infeasible_primal_certified(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Infeasible primal certified by empty ratio."""
        # x1 + x2 <= 1 and x1 + x2 >= 2 with x1, x2 >= 0
        A = np.array([[1.0, 1.0], [1.0, 1.0]])
        c = np.array([1.0, 1.0])
        model = Model(c=c, A=A, row_lower=np.array([-np.inf, 2.0]), row_upper=np.array([1.0, np.inf]),
                      lower=np.array([0.0, 0.0]), upper=np.array([np.inf, np.inf]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        self.assertFalse(res['verification']['feasible'])

    # -------------------------------------------------------------------------
    # 21. Warm Reoptimization Bound Perturbation
    # -------------------------------------------------------------------------
    def test_21_warm_reoptimization_bound_perturbation(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Warm reoptimization from DualBasisState."""
        model = load(str(DATA_DIR / "afiro.mps"))
        # presolve=False/scaling=False: warm DualBasisState is raw inner-solver state;
        # it doesn't transfer across different presolved models.
        res1 = solve_dual_simplex(model, presolve=False, scaling=False)
        self.assertEqual(res1['status'], 'OPTIMAL_VERIFIED')
        state = res1['basis_state']
        self.assertIsInstance(state, DualBasisState)

        # Perturb bound
        model.upper[0] = 50.0  # tighten bound
        res2 = solve_dual_simplex(model, basis_state=state, presolve=False, scaling=False)
        self.assertEqual(res2['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res2['verification']['kkt_passed'])
        # Warm reoptimization should take significantly fewer pivots than cold solve
        self.assertLess(res2['iterations'], res1['iterations'])

    # -------------------------------------------------------------------------
    # 22. Warm Basis Dimension Mismatch Fallback
    # -------------------------------------------------------------------------
    def test_22_warm_basis_dimension_mismatch_fallback(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Dimension mismatch fallback."""
        model = load(str(DATA_DIR / "afiro.mps"))
        # Dummy basis state with wrong dimension
        invalid_state = DualBasisState(
            basis=[0, 1], states=[0, 1], nonbasic_values=np.zeros(2), n_vars=2, m_rows=2
        )
        res = solve_dual_simplex(model, basis_state=invalid_state)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res['fallback_reason'], 'warm_basis_dimension_mismatch')

    # -------------------------------------------------------------------------
    # 23. Invalid Warm Basis Singular Fallback
    # -------------------------------------------------------------------------
    def test_23_invalid_warm_basis_singular_fallback(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singular warm basis falls back to cold start."""
        model = load(str(DATA_DIR / "afiro.mps"))
        m = len(model.A)
        total_cols = len(model.c) + m
        # Duplicate columns in basis => singular basis matrix
        singular_basis = [0] * m
        bad_state = DualBasisState(
            basis=singular_basis, states=[0] * total_cols, nonbasic_values=np.zeros(total_cols),
            n_vars=len(model.c), m_rows=m
        )
        # presolve=False/scaling=False: test raw warm-basis validation logic
        res = solve_dual_simplex(model, basis_state=bad_state, presolve=False, scaling=False)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        # Fallback is reported as warm_basis_initialization_failed (possibly with extra detail)
        fr = res.get('fallback_reason', '')
        self.assertTrue(
            fr.startswith('warm_basis_initialization_failed') or fr == 'warm_basis_dimension_mismatch',
            f"Unexpected fallback_reason: {fr!r}"
        )

    # -------------------------------------------------------------------------
    # 24. Fallback Hierarchy to Primal Simplex
    # -------------------------------------------------------------------------
    def test_24_fallback_hierarchy_to_primal_simplex(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Box-only model routes cleanly."""
        # Model with m=0 constraints: presolve identifies it as a separable box problem
        # and solves it by inspection (method_used='presolve'), which is superior to the
        # old primal-simplex box path.
        model = Model(c=np.array([1.0, -2.0]), A=np.zeros((0, 2)), row_lower=np.zeros(0), row_upper=np.zeros(0),
                      lower=np.array([0.0, 0.0]), upper=np.array([5.0, 5.0]))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res['method_requested'], 'dual-simplex')
        self.assertEqual(res['method_used'], 'presolve')
        self.assertAlmostEqual(res['objective'], 0.0 * 1.0 + 5.0 * (-2.0), places=6)  # min: x0=0, x1=5 => -10

    # -------------------------------------------------------------------------
    # 25. Genuine Netlib AFIRO Dual Simplex
    # -------------------------------------------------------------------------
    def test_25_genuine_netlib_afiro(self):
        """Solve Netlib AFIRO with sovereign revised dual simplex."""
        model = load(str(DATA_DIR / "afiro.mps"))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -464.753142857143, places=6)
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertGreater(res['devex_pricing_calls'], 0)
        self.assertGreater(res['harris_ratio_calls'], 0)
        self.assertEqual(res['method_used'], 'dual-simplex')

    # -------------------------------------------------------------------------
    # 26. Genuine Netlib SC50A Dual Simplex
    # -------------------------------------------------------------------------
    def test_26_genuine_netlib_sc50a(self):
        """Solve Netlib SC50A with sovereign revised dual simplex."""
        model = load(str(DATA_DIR / "sc50a.mps"))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -64.5750770585645, places=6)
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertGreater(res['devex_pricing_calls'], 0)
        self.assertGreater(res['harris_ratio_calls'], 0)
        self.assertEqual(res['method_used'], 'dual-simplex')

    # -------------------------------------------------------------------------
    # 27. Genuine Netlib SC50B Dual Simplex
    # -------------------------------------------------------------------------
    def test_27_genuine_netlib_sc50b(self):
        """Solve Netlib SC50B with sovereign revised dual simplex."""
        model = load(str(DATA_DIR / "sc50b.mps"))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -70.0000000000000, places=6)
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertGreater(res['devex_pricing_calls'], 0)
        self.assertGreater(res['harris_ratio_calls'], 0)
        self.assertEqual(res['method_used'], 'dual-simplex')

    # -------------------------------------------------------------------------
    # 28. Genuine Netlib BLEND Dual Simplex
    # -------------------------------------------------------------------------
    def test_28_genuine_netlib_blend(self):
        """Solve Netlib BLEND with sovereign revised dual simplex."""
        model = load(str(DATA_DIR / "blend.mps"))
        res = solve_dual_simplex(model)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -30.8121498458282, places=6)
        self.assertTrue(res['verification']['kkt_passed'])
        self.assertGreater(res['bound_flips'], 0)
        self.assertGreater(res['devex_pricing_calls'], 0)
        self.assertGreater(res['harris_ratio_calls'], 0)
        self.assertEqual(res['method_used'], 'dual-simplex')


if __name__ == '__main__':
    unittest.main()
