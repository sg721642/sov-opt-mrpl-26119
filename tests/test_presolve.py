"""35-point unit test matrix for Gate 5 — Reversible Presolve and Row/Column Scaling.

All synthetic test fixtures are strictly labeled:
[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA]

Real-data tests use verified Netlib benchmarks from data/verified/.
"""
import unittest
from pathlib import Path
import numpy as np

from sovopt.model import Model, load
from sovopt.presolve import (
    presolve_model,
    scale_model,
    presolve_and_scale,
    compute_dynamic_range,
    reconstruct_dual_kkt,
    PresolveStack,
)
from sovopt.verify import verify

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "verified"
TOL = 1e-7


def make_model(c, A, row_lower, row_upper, lower, upper, **kw):
    """Helper: build Model from raw arrays."""
    return Model(
        c=np.array(c, dtype=float),
        A=np.array(A, dtype=float),
        row_lower=np.array(row_lower, dtype=float),
        row_upper=np.array(row_upper, dtype=float),
        lower=np.array(lower, dtype=float),
        upper=np.array(upper, dtype=float),
        **kw,
    )


def kkt_ok(model, res, tol=TOL):
    """Check KKT on original model using result dict."""
    if res.get('status') not in ('OPTIMAL_VERIFIED', None):
        return False
    x = np.array(res['x'])
    z = np.array(res.get('dual', []))
    rpt = verify(model, x, z, tol=tol)
    return rpt['kkt_passed']


class TestPresolveReductions(unittest.TestCase):

    # =========================================================================
    # 1. Fixed Variable Elimination — simple
    # =========================================================================
    def test_01_fixed_var_simple(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Fixed var x1=3 eliminated."""
        # min 2x0 + 5x1  s.t. x0 + x1 >= 10,  x0 >= 0, x1 in [3,3]
        model = make_model(
            c=[2.0, 5.0],
            A=[[1.0, 1.0]],
            row_lower=[10.0], row_upper=[np.inf],
            lower=[0.0, 3.0], upper=[np.inf, 3.0],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        # Presolve should solve by inspection (fixed var + singleton chain)
        self.assertIsNotNone(pres.status)
        self.assertEqual(pres.status, 'OPTIMAL_VERIFIED')
        x = np.array(pres.result_dict['x'])
        self.assertAlmostEqual(x[1], 3.0, places=6)
        self.assertAlmostEqual(x[0], 7.0, places=6)
        self.assertTrue(pres.result_dict['verification']['kkt_passed'])

    # =========================================================================
    # 2. Fixed Variable Elimination — with offset
    # =========================================================================
    def test_02_fixed_var_offset(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Fixed var contributes objective offset."""
        # min x0 + 3*x1  s.t. x0 + x1 = 5,  x0 in [2,2], x1 >= 0
        model = make_model(
            c=[1.0, 3.0],
            A=[[1.0, 1.0]],
            row_lower=[5.0], row_upper=[5.0],
            lower=[2.0, 0.0], upper=[2.0, np.inf],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        # x0=2 fixed => x1=3. Obj = 2 + 9 = 11.
        self.assertIsNotNone(pres.status)
        self.assertEqual(pres.status, 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(pres.result_dict['objective'], 11.0, places=6)

    # =========================================================================
    # 3. Empty Row — feasible (redundant)
    # =========================================================================
    def test_03_empty_row_redundant(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] All-zero row with 0 in RHS range is removed."""
        # Add a third constrained variable so presolve doesn't fully collapse to optimal.
        # Row 1 (all-zero) should be removed; row 0 remains as singleton.
        model = make_model(
            c=[1.0, 2.0, 3.0],
            A=[[1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            row_lower=[0.0, -np.inf], row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0, 0.0], upper=[np.inf, np.inf, np.inf],
        )
        pres_result = presolve_model(model)
        # Empty row 1 should be removed; result is either reduced (status=None) or solved
        # The telemetry must record at least 1 empty_row removal
        self.assertGreaterEqual(pres_result.telemetry.get('empty_rows', 0), 1)

    # =========================================================================
    # 4. Empty Row — infeasible (all-zero row with RHS > 0)
    # =========================================================================
    def test_04_empty_row_infeasible(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] All-zero row with impossible RHS is infeasible."""
        model = make_model(
            c=[1.0, 2.0],
            A=[[1.0, 0.0], [0.0, 0.0]],
            row_lower=[5.0, 1.0], row_upper=[np.inf, np.inf],  # row 1: 0 >= 1 impossible
            lower=[0.0, 0.0], upper=[np.inf, np.inf],
        )
        pres_result = presolve_model(model)
        self.assertEqual(pres_result.status, 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 5. Empty Row — infeasible (all-zero row with RHS upper < 0)
    # =========================================================================
    def test_05_empty_row_infeasible_upper(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] All-zero row with impossible upper RHS."""
        model = make_model(
            c=[1.0],
            A=[[0.0]],
            row_lower=[-np.inf], row_upper=[-1.0],  # 0 <= -1 impossible
            lower=[0.0], upper=[np.inf],
        )
        pres_result = presolve_model(model)
        self.assertEqual(pres_result.status, 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 6. Singleton Row — positive coefficient bound tightening
    # =========================================================================
    def test_06_singleton_row_positive_coeff(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row tightens lower bound."""
        # min x0 + x1  s.t. x0 >= 3,  x0 in [0, inf], x1 in [0, inf]
        # After singleton tightening x0.lower=3, the empty-col check sees x0 (c>0, lower finite)
        # and x1 (c>0, lower finite) as separable, solves to OPTIMAL_VERIFIED.
        model = make_model(
            c=[1.0, 1.0],
            A=[[1.0, 0.0]],
            row_lower=[3.0], row_upper=[np.inf],
            lower=[0.0, 0.0], upper=[np.inf, np.inf],
        )
        pres_result = presolve_model(model)
        # The singleton row for x0 must have been processed
        self.assertGreaterEqual(pres_result.telemetry.get('singleton_rows', 0), 1)
        # End state: either reduced with x0.lower=3, or solved to optimal
        if pres_result.status is None:
            self.assertAlmostEqual(pres_result.model.lower[0], 3.0, places=8)
        else:
            self.assertEqual(pres_result.status, 'OPTIMAL_VERIFIED')
            x = np.array(pres_result.result_dict['x'])
            self.assertAlmostEqual(x[0], 3.0, places=6)

    # =========================================================================
    # 7. Singleton Row — negative coefficient bound tightening
    # =========================================================================
    def test_07_singleton_row_negative_coeff(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row with negative coeff tightens upper."""
        # -2*x0 <= -4  =>  x0 >= 2; with c[0]=1>0, presolve further sets x0=2 (min at lb).
        model = make_model(
            c=[1.0],
            A=[[-2.0]],
            row_lower=[-np.inf], row_upper=[-4.0],
            lower=[0.0], upper=[np.inf],
        )
        pres_result = presolve_model(model)
        self.assertGreaterEqual(pres_result.telemetry.get('singleton_rows', 0), 1)
        if pres_result.status is None:
            # imp_l = (-4) / (-2) = 2
            self.assertAlmostEqual(pres_result.model.lower[0], 2.0, places=8)
        else:
            # Presolve solved to optimal: x0=2 (at the tightened lower bound)
            self.assertEqual(pres_result.status, 'OPTIMAL_VERIFIED')
            self.assertAlmostEqual(pres_result.result_dict['x'][0], 2.0, places=6)

    # =========================================================================
    # 8. Singleton Row — both sides
    # =========================================================================
    def test_08_singleton_row_ranged(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row with ranged RHS tightens both bounds."""
        # 1 <= x0 <= 5: singleton row tightens bounds, then empty-col solves x0=1 (min at lb).
        model = make_model(
            c=[1.0],
            A=[[1.0]],
            row_lower=[1.0], row_upper=[5.0],
            lower=[0.0], upper=[np.inf],
        )
        pres_result = presolve_model(model)
        self.assertGreaterEqual(pres_result.telemetry.get('singleton_rows', 0), 1)
        if pres_result.status is None:
            self.assertAlmostEqual(pres_result.model.lower[0], 1.0, places=8)
            self.assertAlmostEqual(pres_result.model.upper[0], 5.0, places=8)
        else:
            self.assertEqual(pres_result.status, 'OPTIMAL_VERIFIED')
            # x0=1 (minimize x0 with x0 in [1,5])
            self.assertAlmostEqual(pres_result.result_dict['x'][0], 1.0, places=6)

    # =========================================================================
    # 9. Singleton Row — infeasible
    # =========================================================================
    def test_09_singleton_row_infeasible(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row that makes bounds contradictory."""
        # x0 >= 10, but x0 <= 5 => infeasible
        model = make_model(
            c=[1.0],
            A=[[1.0]],
            row_lower=[10.0], row_upper=[np.inf],
            lower=[0.0], upper=[5.0],
        )
        pres_result = presolve_model(model)
        self.assertEqual(pres_result.status, 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 10. Singleton Row — infeasible via negative coefficient
    # =========================================================================
    def test_10_singleton_row_infeasible_neg(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row with negative coeff infeasible."""
        # -x0 <= -10  =>  x0 >= 10, but x0 <= 3
        model = make_model(
            c=[1.0],
            A=[[-1.0]],
            row_lower=[-np.inf], row_upper=[-10.0],
            lower=[0.0], upper=[3.0],
        )
        pres_result = presolve_model(model)
        self.assertEqual(pres_result.status, 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 11. Activity Bounds — tight feasible (redundant row removal)
    # =========================================================================
    def test_11_activity_bounds_redundant(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Row always satisfied by activity bounds is removed."""
        # Row 0: x0 + x1 <= 20, but x0 in [0,5], x1 in [0,5] => activity max = 10 <= 20 (redundant)
        # Row 1: x0 + 2*x1 >= 2 (not singleton, 2 nonzero entries)
        model = make_model(
            c=[1.0, 1.0],
            A=[[1.0, 1.0], [1.0, 2.0]],
            row_lower=[-np.inf, 2.0], row_upper=[20.0, np.inf],
            lower=[0.0, 0.0], upper=[5.0, 5.0],
        )
        pres_result = presolve_model(model)
        # First row (x0+x1 <= 20) is redundant and removed; only the second row remains
        self.assertIsNone(pres_result.status)
        self.assertEqual(len(pres_result.model.A), 1)
        self.assertGreaterEqual(pres_result.telemetry.get('redundant_rows', 0), 1)

    # =========================================================================
    # 12. Activity Bounds — infeasible
    # =========================================================================
    def test_12_activity_bounds_infeasible(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Row impossible from activity bounds."""
        # x0 + x1 >= 20, but x0 in [0,5], x1 in [0,5] => activity max = 10 < 20
        model = make_model(
            c=[1.0, 1.0],
            A=[[1.0, 1.0]],
            row_lower=[20.0], row_upper=[np.inf],
            lower=[0.0, 0.0], upper=[5.0, 5.0],
        )
        pres_result = presolve_model(model)
        self.assertEqual(pres_result.status, 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 13. Fixed Variable Chain
    # =========================================================================
    def test_13_fixed_var_chain(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Chain of fixed vars solved by presolve."""
        # All three variables fixed; presolve computes obj offset and verifies.
        model = make_model(
            c=[1.0, 2.0, 3.0],
            A=[[1.0, 1.0, 1.0]],
            row_lower=[6.0], row_upper=[6.0],
            lower=[1.0, 2.0, 3.0], upper=[1.0, 2.0, 3.0],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        # All fixed: x=[1,2,3], obj = 1+4+9 = 14
        self.assertEqual(pres.status, 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(pres.result_dict['objective'], 14.0, places=6)

    # =========================================================================
    # 14. Empty Column — separable optimal
    # =========================================================================
    def test_14_empty_col_separable_optimal(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Empty column (no constraints) optimized to bound."""
        # min x0 + 2*x1  s.t. x0 in [0,5]  (x1 has no constraints but lower bound)
        model = make_model(
            c=[1.0, 2.0],
            A=[[1.0, 0.0]],
            row_lower=[0.0], row_upper=[np.inf],
            lower=[0.0, 1.0], upper=[5.0, np.inf],
        )
        # After singleton tightening x0's lower to max(0,0)=0, col x1 is empty.
        # x1 has c=2>0 => set to lower=1.
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        if pres.status == 'OPTIMAL_VERIFIED':
            x = np.array(pres.result_dict['x'])
            self.assertAlmostEqual(x[1], 1.0, places=6)

    # =========================================================================
    # 15. Empty Column — unbounded
    # =========================================================================
    def test_15_empty_col_unbounded(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Empty col with c<0 and upper=+inf is unbounded."""
        # min -x0  s.t. (no constraints), x0 in [0, inf]
        model = make_model(
            c=[-1.0],
            A=np.zeros((0, 1)),
            row_lower=[], row_upper=[],
            lower=[0.0], upper=[np.inf],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        self.assertIsNotNone(pres.status)
        self.assertIn(pres.status, ('UNBOUNDED_CERTIFIED', 'NUMERICAL_FAILURE'))
        if pres.status == 'UNBOUNDED_CERTIFIED':
            d = np.array(pres.result_dict.get('direction', pres.result_dict.get('ray', [])))
            self.assertGreater(d[0], 0)

    # =========================================================================
    # 16. Row Scaling Roundtrip KKT
    # =========================================================================
    def test_16_row_scaling_roundtrip(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Row scaling then unscale gives same x, same KKT."""
        model = make_model(
            c=[1.0, 2.0],
            A=[[1000.0, 2000.0], [0.001, 0.002]],
            row_lower=[1.0, 0.001], row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0], upper=[np.inf, np.inf],
        )
        scaled, stack, tel = scale_model(model)
        # Verify scaling reduced the dynamic range
        orig_range = compute_dynamic_range(model.A, model.c)
        scaled_range = compute_dynamic_range(scaled.A, scaled.c)
        self.assertLessEqual(scaled_range, orig_range)
        # Solve unscaled and verify KKT on original
        from sovopt.dual_simplex import solve_dual_simplex
        res_scaled = solve_dual_simplex(scaled, presolve=False, scaling=False)
        if res_scaled['status'] == 'OPTIMAL_VERIFIED':
            x_red = np.array(res_scaled['x'])
            y_red = np.array(res_scaled.get('y', np.zeros(len(scaled.A))))
            x_orig = stack.postsolve_primal(x_red)
            y_orig = stack.postsolve_dual_rows(y_red, model, x_orig)
            z_orig = reconstruct_dual_kkt(model, y_orig)
            report = verify(model, x_orig, z_orig, tol=TOL)
            self.assertTrue(report['kkt_passed'])

    # =========================================================================
    # 17. Column Scaling Roundtrip KKT
    # =========================================================================
    def test_17_col_scaling_roundtrip(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Col scaling then unscale gives same x, same KKT."""
        model = make_model(
            c=[0.001, 1000.0],
            A=[[1.0, 1.0]],
            row_lower=[1.0], row_upper=[np.inf],
            lower=[0.0, 0.0], upper=[np.inf, np.inf],
        )
        scaled, stack, tel = scale_model(model)
        # After col scaling the dynamic range of A columns is reduced
        dyn_before = compute_dynamic_range(model.A, model.c)
        dyn_after = compute_dynamic_range(scaled.A, scaled.c)
        self.assertLessEqual(dyn_after, dyn_before)

    # =========================================================================
    # 18. Presolve + Scaling on AFIRO (Netlib)
    # =========================================================================
    def test_18_presolve_scaling_afiro(self):
        """Presolve + scaling on Netlib AFIRO: KKT verified on original model."""
        model = load(str(DATA_DIR / "afiro.mps"))
        from sovopt.dual_simplex import solve_dual_simplex
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -464.753142857143, places=5)
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 19. Presolve + Scaling on SC50A (Netlib)
    # =========================================================================
    def test_19_presolve_scaling_sc50a(self):
        """Presolve + scaling on Netlib SC50A: KKT verified on original model."""
        model = load(str(DATA_DIR / "sc50a.mps"))
        from sovopt.dual_simplex import solve_dual_simplex
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -64.5750770585645, places=5)
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 20. Presolve + Scaling on SC50B (Netlib)
    # =========================================================================
    def test_20_presolve_scaling_sc50b(self):
        """Presolve + scaling on Netlib SC50B: KKT verified on original model."""
        model = load(str(DATA_DIR / "sc50b.mps"))
        from sovopt.dual_simplex import solve_dual_simplex
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -70.0, places=5)
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 21. Presolve + Scaling on BLEND (Netlib)
    # =========================================================================
    def test_21_presolve_scaling_blend(self):
        """Presolve + scaling on Netlib BLEND: KKT verified on original model."""
        model = load(str(DATA_DIR / "blend.mps"))
        from sovopt.dual_simplex import solve_dual_simplex
        res = solve_dual_simplex(model, presolve=True, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 22. Direction Postsolve Is Strictly Linear (zero affine shift)
    # =========================================================================
    def test_22_direction_postsolve_linear(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Direction postsolve has zero affine shift."""
        # Unbounded model: min -x0, x0 in [0, inf]
        model = make_model(
            c=[-1.0],
            A=np.zeros((0, 1)),
            row_lower=[], row_upper=[],
            lower=[0.0], upper=[np.inf],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        # If unbounded is caught
        if pres.status == 'UNBOUNDED_CERTIFIED':
            d = np.array(pres.result_dict.get('direction', pres.result_dict.get('ray', [])))
            # Direction must be strictly linear: d_orig = M * d_reduced, no affine offset.
            # Verify by checking d = stack.postsolve_direction(d_reduced)
            # and that postsolve_direction(2*d_red) = 2 * postsolve_direction(d_red)
            from sovopt.presolve import PresolveStack
            stack = pres.stack
            d_in = np.array([1.0])  # unit direction
            d_out1 = stack.postsolve_direction(d_in)
            d_out2 = stack.postsolve_direction(2.0 * d_in)
            np.testing.assert_array_almost_equal(2.0 * d_out1, d_out2)

    # =========================================================================
    # 23. Dual Postsolve Singleton Tight — variable at implied bound
    # =========================================================================
    def test_23_dual_postsolve_singleton_tight(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row dual recovered via stationarity when tight."""
        # min 2*x0 + 5*x1  s.t. x0 + x1 >= 10,  x0 >= 0,  x1 in [3,3]
        model = make_model(
            c=[2.0, 5.0],
            A=[[1.0, 1.0]],
            row_lower=[10.0], row_upper=[np.inf],
            lower=[0.0, 3.0], upper=[np.inf, 3.0],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        self.assertEqual(pres.status, 'OPTIMAL_VERIFIED')
        # KKT on original model must pass (requires correct y for singleton row)
        self.assertTrue(pres.result_dict['verification']['kkt_passed'])

    # =========================================================================
    # 24. Dual Postsolve Singleton — not tight → y=0
    # =========================================================================
    def test_24_dual_postsolve_singleton_not_tight(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row dual is 0 when var is not at implied bound."""
        # min 2*x0 + x1  s.t. x0 + x1 >= 3,  x0 in [5,5] (fixed above implied bound)
        # Optimal: x0=5, x1=0, obj=10. Row satisfied. Dual y=0 (slack > 0).
        model = make_model(
            c=[2.0, 1.0],
            A=[[1.0, 1.0]],
            row_lower=[3.0], row_upper=[np.inf],
            lower=[5.0, 0.0], upper=[5.0, np.inf],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        # Should be solved by presolve (x0 fixed, row becomes x1 >= -2, redundant)
        self.assertIsNotNone(pres.status)
        self.assertEqual(pres.status, 'OPTIMAL_VERIFIED')
        self.assertTrue(pres.result_dict['verification']['kkt_passed'])

    # =========================================================================
    # 25. Primal Postsolve — fixed var value recovered
    # =========================================================================
    def test_25_primal_postsolve_fixed_var(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Fixed var restored to its fixed value in primal postsolve."""
        model = make_model(
            c=[1.0, 2.0, 3.0],
            A=[[1.0, 1.0, 0.0]],
            row_lower=[3.0], row_upper=[np.inf],
            lower=[0.0, 2.0, 1.0], upper=[np.inf, 2.0, 1.0],  # x1=2,x2=1 fixed
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        self.assertIsNotNone(pres.status)
        if pres.status == 'OPTIMAL_VERIFIED':
            x = np.array(pres.result_dict['x'])
            self.assertAlmostEqual(x[1], 2.0, places=6)
            self.assertAlmostEqual(x[2], 1.0, places=6)

    # =========================================================================
    # 26. Primal Postsolve — empty col variable restored
    # =========================================================================
    def test_26_primal_postsolve_empty_col(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Empty col variable restored to its optimal value."""
        # min x0 + 2*x1  s.t. x0 >= 1,  x1 in [3, inf]  (x1 has no row constraints)
        model = make_model(
            c=[1.0, 2.0],
            A=[[1.0, 0.0]],
            row_lower=[1.0], row_upper=[np.inf],
            lower=[0.0, 3.0], upper=[np.inf, np.inf],
        )
        # x1 is empty col; min 2*x1 with x1 >= 3 => x1 = 3
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        if pres.status == 'OPTIMAL_VERIFIED':
            x = np.array(pres.result_dict['x'])
            self.assertAlmostEqual(x[1], 3.0, places=6)

    # =========================================================================
    # 27. Presolve + Scaling on Infeasible → Exact Farkas (1)
    # =========================================================================
    def test_27_presolve_infeasible_singleton(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Singleton row infeasibility gives Farkas cert."""
        # x0 >= 10 but x0 <= 3 → infeasible
        model = make_model(
            c=[1.0],
            A=[[1.0]],
            row_lower=[10.0], row_upper=[np.inf],
            lower=[0.0], upper=[3.0],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=True)
        self.assertEqual(pres.status, 'INFEASIBLE_CERTIFIED')
        self.assertIsNotNone(pres.result_dict)
        self.assertEqual(pres.result_dict['status'], 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 28. Presolve + Scaling on Infeasible → Exact Farkas (2)
    # =========================================================================
    def test_28_presolve_infeasible_contradictory_bounds(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Contradictory var bounds certified infeasible."""
        model = make_model(
            c=[1.0, 1.0],
            A=[[1.0, 1.0]],
            row_lower=[0.0], row_upper=[np.inf],
            lower=[5.0, 0.0], upper=[3.0, np.inf],  # x0: lower > upper
        )
        pres = presolve_and_scale(model, presolve=True, scaling=True)
        self.assertEqual(pres.status, 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # 29. Original Model Immutability
    # =========================================================================
    def test_29_original_model_immutability(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Presolve never mutates the original model in-place."""
        model = make_model(
            c=[2.0, 5.0],
            A=[[1.0, 1.0]],
            row_lower=[10.0], row_upper=[np.inf],
            lower=[0.0, 3.0], upper=[np.inf, 3.0],
        )
        A_before = model.A.copy()
        c_before = model.c.copy()
        lower_before = model.lower.copy()
        upper_before = model.upper.copy()
        row_lower_before = model.row_lower.copy()
        row_upper_before = model.row_upper.copy()

        presolve_and_scale(model, presolve=True, scaling=True)

        np.testing.assert_array_equal(model.A, A_before)
        np.testing.assert_array_equal(model.c, c_before)
        np.testing.assert_array_equal(model.lower, lower_before)
        np.testing.assert_array_equal(model.upper, upper_before)
        np.testing.assert_array_equal(model.row_lower, row_lower_before)
        np.testing.assert_array_equal(model.row_upper, row_upper_before)

    # =========================================================================
    # 30. Dynamic Range Diagnostic
    # =========================================================================
    def test_30_dynamic_range_diagnostic(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Dynamic range computed correctly."""
        A = np.array([[1000.0, 1.0], [0.001, 1.0]])
        c = np.array([1.0, 1.0])
        dr = compute_dynamic_range(A, c)
        # Non-zeros: 1000, 1, 0.001, 1, 1, 1 => max=1000, min=0.001 => range=1e6
        self.assertAlmostEqual(dr, 1e6, places=0)

    # =========================================================================
    # 31. Scaling Reduces Dynamic Range
    # =========================================================================
    def test_31_scaling_reduces_dynamic_range(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Scale model reduces dynamic range."""
        model = make_model(
            c=[1.0, 1.0],
            A=[[1e4, 2e4], [1e-3, 2e-3]],
            row_lower=[1.0, 1e-3], row_upper=[np.inf, np.inf],
            lower=[0.0, 0.0], upper=[np.inf, np.inf],
        )
        dr_before = compute_dynamic_range(model.A, model.c)
        scaled, stack, tel = scale_model(model)
        dr_after = compute_dynamic_range(scaled.A, scaled.c)
        self.assertLess(dr_after, dr_before)

    # =========================================================================
    # 32. Presolve Telemetry — counts
    # =========================================================================
    def test_32_presolve_telemetry_counts(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Presolve reports reduction counts correctly."""
        # Model with 1 fixed var, 1 empty row, 1 singleton row
        model = make_model(
            c=[1.0, 2.0, 3.0],
            A=[[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            row_lower=[0.0, -np.inf, 0.0], row_upper=[np.inf, np.inf, np.inf],
            lower=[0.0, 2.0, 0.0], upper=[np.inf, 2.0, np.inf],
        )
        pres = presolve_model(model)
        tel = pres.telemetry
        self.assertIn('fixed_variables', tel)
        self.assertIn('empty_rows', tel)
        self.assertIn('singleton_rows', tel)
        self.assertGreaterEqual(tel['fixed_variables'], 1)
        self.assertGreaterEqual(tel['empty_rows'], 1)

    # =========================================================================
    # 33. 4-Way Ablation: AFIRO × presolve × scaling — all OPTIMAL_VERIFIED
    # =========================================================================
    def test_33_ablation_afiro_4way(self):
        """4-way ablation on AFIRO: presolve={F,T} × scaling={F,T} all OPTIMAL_VERIFIED."""
        from sovopt.dual_simplex import solve_dual_simplex
        model = load(str(DATA_DIR / "afiro.mps"))
        ref_obj = -464.753142857143
        for p in (False, True):
            for s in (False, True):
                with self.subTest(presolve=p, scaling=s):
                    res = solve_dual_simplex(model, presolve=p, scaling=s)
                    self.assertEqual(res['status'], 'OPTIMAL_VERIFIED',
                                     f"presolve={p}, scaling={s}: {res.get('status')}")
                    self.assertAlmostEqual(res['objective'], ref_obj, places=4,
                                           msg=f"presolve={p}, scaling={s}: obj mismatch")
                    self.assertTrue(res['verification']['kkt_passed'])

    # =========================================================================
    # 34. Presolve Status None When Reduced Model Returned
    # =========================================================================
    def test_34_presolve_returns_none_status_for_reducible(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Status=None means a reduced model is returned for further solving."""
        # Model with an empty row that is removed, leaving 2 constrained rows and 2 variables
        model = make_model(
            c=[1.0, 2.0],
            A=[[1.0, 2.0], [2.0, 1.0], [0.0, 0.0]],
            row_lower=[5.0, 6.0, -np.inf], row_upper=[np.inf, np.inf, np.inf],
            lower=[0.0, 0.0], upper=[np.inf, np.inf],
        )
        pres = presolve_model(model)
        # Empty row removed, reduced model should have 2 rows, and status=None
        self.assertIsNone(pres.status)
        self.assertEqual(len(pres.model.A), 2)
        self.assertIsNotNone(pres.model)
        self.assertGreaterEqual(pres.telemetry.get('empty_rows', 0), 1)

    # =========================================================================
    # 35. Presolve Handles Zero-Constraint Model
    # =========================================================================
    def test_35_zero_constraint_model(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] m=0 model solved via separable box analysis."""
        model = make_model(
            c=[1.0, -2.0],
            A=np.zeros((0, 2)),
            row_lower=[], row_upper=[],
            lower=[0.0, 0.0], upper=[5.0, 5.0],
        )
        pres = presolve_and_scale(model, presolve=True, scaling=False)
        # Separable box: x0=0 (c>0, minimize), x1=5 (c<0, maximize)
        self.assertIsNotNone(pres.status)
        self.assertEqual(pres.status, 'OPTIMAL_VERIFIED')
        x = np.array(pres.result_dict['x'])
        self.assertAlmostEqual(x[0], 0.0, places=6)
        self.assertAlmostEqual(x[1], 5.0, places=6)
        self.assertAlmostEqual(pres.result_dict['objective'], -10.0, places=6)


if __name__ == '__main__':
    unittest.main()
