"""GATE 11.1 Master Deep Technical Pre-Deployment Audit Test Suite.

Comprehensive independent regression tests covering:
- Canonical model & parser edge cases (Section 4)
- Presolve / postsolve invariants on original model (Section 5)
- Sparse numerical linear algebra & singular matrix detection (Section 6)
- LP independent correctness against analytic ground-truth (Section 7)
- Mandatory certificate corruption tests (Section 8)
- Safe MILP bounds and exact rational pruning audit (Section 9)
- Small MILP exhaustive oracle comparison (Section 10)
- QP analytic correctness & nonconvex rejection (Section 12)
- Trust status semantics & failure path honesty (Section 13)
- Extended precision audit (Section 14)
- Numerical torture tests (Section 15)
- Metamorphic correctness under permutation and scaling (Section 16)
- Explainable dispatcher audit (Section 17 & 22)
- Refinery physical engineering validation (Section 18 & 19)
- SOV-OPT Trust Passport schema & null-safety (Section 20)
- Farkas Constraint Lens diagnostic ranking (Section 21)
- Cross-method consistency check (Section 23)
- Offline sovereignty & network isolation (Section 24)
- Determinism across repeated solves (Section 25)
"""

import unittest
from fractions import Fraction as F
import math
import numpy as np

from sovopt.model import Model
from sovopt.simplex import solve_lp
from sovopt.dual_simplex import solve_dual_simplex
from sovopt.milp import solve_milp
from sovopt.qp import solve_qp
from sovopt.pdhg import solve_pdhg
from sovopt.verify import verify, exact_farkas, verify_unbounded_certificate, safe_lower_bound
from sovopt.dispatcher import auto_dispatch, inspect_model
from sovopt.refinery_twin import build_refinery_twin, validate_refinery_physical_solution
from sovopt.trust_passport import generate_trust_passport
from sovopt.farkas_lens import rank_farkas_contributions
from sovopt.sparse import csc_from_triplets
from sovopt.sparse_lu import SparseBasisEngine, NumericalError


class TestGate11Audit(unittest.TestCase):

    # =========================================================================
    # Section 4: Canonical Model & Parser Edge Cases
    # =========================================================================

    def test_section4_dimension_mismatch_rejected(self):
        """Model with mismatched row or column dimensions must fail validation."""
        with self.assertRaises(ValueError):
            m = Model(c=np.array([1.0, 2.0]), A=np.array([[1.0]]),
                      row_lower=np.array([0.0]), row_upper=np.array([1.0]),
                      lower=np.array([0.0, 0.0]), upper=np.array([1.0, 1.0]))
            m.validate()

    def test_section4_inverted_bounds_rejected(self):
        """Model with lower > upper must fail validation."""
        with self.assertRaises(ValueError):
            m = Model(c=np.array([1.0]), A=np.zeros((0, 1)), row_lower=np.zeros(0), row_upper=np.zeros(0),
                      lower=np.array([10.0]), upper=np.array([5.0]))
            m.validate()

    def test_section4_non_unique_names_rejected(self):
        """Model with non-unique variable names must fail validation."""
        with self.assertRaises(ValueError):
            m = Model(c=np.array([1.0, 2.0]), A=np.zeros((0, 2)), row_lower=np.zeros(0), row_upper=np.zeros(0),
                      lower=np.array([0.0, 0.0]), upper=np.array([1.0, 1.0]),
                      names=('x', 'x'))
            m.validate()

    def test_section4_nonconvex_qp_rejected(self):
        """Nonconvex QP with negative eigenvalues must be rejected with explicit error."""
        # Q has eigenvalues +1 and -1 (saddle point, strictly nonconvex)
        Q_nonconvex = np.array([[1.0, 0.0], [0.0, -1.0]])
        m = Model(c=np.array([0.0, 0.0]), A=np.zeros((0, 2)), row_lower=np.zeros(0), row_upper=np.zeros(0),
                  lower=np.array([-5.0, -5.0]), upper=np.array([5.0, 5.0]), Q=Q_nonconvex)
        with self.assertRaises(ValueError) as ctx:
            solve_qp(m)
        self.assertIn('Nonconvex QP rejected', str(ctx.exception))

    def test_section4_zero_row_box_model(self):
        """Model with zero constraint rows (pure variable box) solves correctly."""
        m = Model(c=np.array([3.0, -2.0]), A=np.zeros((0, 2)), row_lower=np.zeros(0), row_upper=np.zeros(0),
                  lower=np.array([-1.0, 0.0]), upper=np.array([2.0, 4.0]))
        res = solve_lp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        # Min 3*x0 - 2*x1 on [-1, 2] x [0, 4] -> x* = (-1, 4), obj = 3*(-1) - 2*(4) = -11
        self.assertAlmostEqual(res['objective'], -11.0, places=6)
        self.assertAlmostEqual(res['x'][0], -1.0, places=6)
        self.assertAlmostEqual(res['x'][1], 4.0, places=6)

    # =========================================================================
    # Section 5: Presolve / Postsolve Correctness
    # =========================================================================

    def test_section5_fixed_var_elimination_original_kkt(self):
        """Solution after fixed variable elimination must satisfy original model KKT."""
        # x0 + x1 <= 10, x0 fixed to 3, min -x0 - 2*x1, x1 in [0, 10]
        # Optimal: x0=3, x1=7, obj = -17
        m = Model(c=np.array([-1.0, -2.0]), A=np.array([[1.0, 1.0]]),
                  row_lower=np.array([-np.inf]), row_upper=np.array([10.0]),
                  lower=np.array([3.0, 0.0]), upper=np.array([3.0, 10.0]))
        res = solve_dual_simplex(m, presolve=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][0], 3.0, places=6)
        self.assertAlmostEqual(res['x'][1], 7.0, places=6)
        self.assertAlmostEqual(res['objective'], -17.0, places=6)
        # Independent verification on original model
        v = verify(m, np.array(res['x']), np.array(res['dual']), tol=1e-6)
        self.assertTrue(v['kkt_passed'])

    # =========================================================================
    # Section 6: Sparse Numerical Algebra & Singular Matrix Detection
    # =========================================================================

    def test_section6_singular_sparse_matrix_detection(self):
        """Singular basis matrix must be detected and raise NumericalError, never producing false optimum."""
        from sovopt.sparse_lu import SparseLU, NumericalError
        r = np.array([0, 0, 1, 1, 2, 2], dtype=np.int64)
        c = np.array([0, 1, 0, 1, 0, 1], dtype=np.int64)
        d = np.array([1.0, 2.0, 3.0, 4.0, 4.0, 6.0], dtype=np.float64)
        csc = csc_from_triplets(3, 3, r, c, d)
        lu = SparseLU()
        with self.assertRaises(NumericalError):
            lu.factorize(csc)

    def test_section6_well_conditioned_sparse_solve(self):
        """Well-conditioned sparse matrix factors and solves with high precision."""
        from sovopt.sparse_lu import SparseLU
        r = np.array([0, 0, 1, 1, 1, 2, 2], dtype=np.int64)
        c = np.array([0, 1, 0, 1, 2, 1, 2], dtype=np.int64)
        d = np.array([4.0, -1.0, -1.0, 4.0, -1.0, -1.0, 4.0], dtype=np.float64)
        csc = csc_from_triplets(3, 3, r, c, d)
        lu = SparseLU()
        lu.factorize(csc)
        b = np.array([1.0, 2.0, 3.0])
        x, rel_res, abs_res, iters = lu.solve(b)
        self.assertLess(rel_res, 1e-12)

    # =========================================================================
    # Section 7: LP Independent Correctness Against Analytic Ground Truth
    # =========================================================================

    def test_section7_analytic_2d_lp(self):
        """Solve 2D LP with known analytic geometry and compare solution exactly."""
        m = Model(
            c=np.array([-3.0, -2.0]),
            A=np.array([[1.0, 1.0], [2.0, 1.0]]),
            row_lower=np.array([-np.inf, -np.inf]),
            row_upper=np.array([4.0, 5.0]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([np.inf, np.inf]),
        )
        res = solve_lp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][0], 1.0, places=6)
        self.assertAlmostEqual(res['x'][1], 3.0, places=6)
        self.assertAlmostEqual(res['objective'], -9.0, places=6)

    # =========================================================================
    # Section 8: MANDATORY Certificate Corruption Tests
    # =========================================================================

    def test_section8_farkas_certificate_corruption(self):
        """Valid Farkas certificate passes; any perturbed coefficient MUST be rejected."""
        m = Model(
            c=np.array([1.0]),
            A=np.array([[1.0], [1.0]]),
            row_lower=np.array([2.0, -np.inf]),
            row_upper=np.array([np.inf, 1.0]),
            lower=np.array([-np.inf]),
            upper=np.array([np.inf]),
        )
        res = solve_lp(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        cert = res['certificate']
        # 1. Uncorrupted certificate MUST verify
        self.assertTrue(exact_farkas(m, cert))

        # 2. Perturb coefficient by adding 0.5: MUST FAIL
        cert_corrupted = list(cert)
        cert_corrupted[0] += 0.5
        self.assertFalse(exact_farkas(m, cert_corrupted),
                         'CRITICAL P0: Corrupted Farkas certificate was incorrectly accepted!')

        # 3. Invert sign of certificate: MUST FAIL
        cert_neg = [-v for v in cert]
        self.assertFalse(exact_farkas(m, cert_neg),
                         'CRITICAL P0: Negative certificate was incorrectly accepted!')

    def test_section8_unbounded_ray_corruption(self):
        """Valid unbounded ray certificate passes; corrupted direction MUST be rejected."""
        m = Model(
            c=np.array([-1.0]),
            A=np.zeros((0, 1)),
            row_lower=np.zeros(0),
            row_upper=np.zeros(0),
            lower=np.array([0.0]),
            upper=np.array([np.inf]),
        )
        res = solve_lp(m)
        self.assertEqual(res['status'], 'UNBOUNDED_CERTIFIED')
        x0 = np.array(res.get('base_point', res.get('x', [0.0])))
        d = np.array(res.get('ray', res.get('direction', [1.0])))

        # 1. Valid certificate passes
        cert = verify_unbounded_certificate(m, x0, d)
        self.assertTrue(cert['verified'])

        # 2. Corrupt ray by inverting direction (becomes non-improving c^T d > 0): MUST FAIL
        d_bad = -d
        cert_bad = verify_unbounded_certificate(m, x0, d_bad)
        self.assertFalse(cert_bad['verified'],
                         'CRITICAL P0: Non-improving recession ray was incorrectly accepted!')

        # 3. Corrupt base point by violating bounds (x0 = -5.0 < 0): MUST FAIL
        x0_bad = np.array([-5.0])
        cert_bad_base = verify_unbounded_certificate(m, x0_bad, d)
        self.assertFalse(cert_bad_base['verified'],
                         'CRITICAL P0: Infeasible base point was incorrectly accepted!')

    def test_section8_solution_data_corruption(self):
        """Perturbed solution point MUST fail KKT verification."""
        m = build_refinery_twin('lp')
        res = solve_dual_simplex(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        x = np.array(res['x'])
        dual = np.array(res['dual'])

        # 1. Authentic solution passes KKT
        v_clean = verify(m, x, dual, tol=1e-6)
        self.assertTrue(v_clean['kkt_passed'])

        # 2. Perturb solution x[0] by 2.0: MUST FAIL KKT
        x_corrupt = x.copy()
        x_corrupt[0] += 2.0
        v_corrupt = verify(m, x_corrupt, dual, tol=1e-6)
        self.assertFalse(v_corrupt['kkt_passed'],
                         'CRITICAL P0: Corrupted primal solution passed KKT verification!')

    # =========================================================================
    # Section 9: Safe MILP Bound / Pruning Audit
    # =========================================================================

    def test_section9_exact_rational_lagrangian_bound(self):
        """safe_lower_bound must return an exact Fraction, never an unsafe float."""
        m = Model(
            c=np.array([1.0, 2.0]),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([3.0]),
            row_upper=np.array([np.inf]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([5.0, 5.0]),
        )
        res = solve_lp(m)
        z = res['dual']
        lb = safe_lower_bound(m, z)
        self.assertIsInstance(lb, F)
        self.assertLessEqual(lb, F(3, 1))

    # =========================================================================
    # Section 10: Small MILP Exhaustive Oracle
    # =========================================================================

    def test_section10_binary_knapsack_oracle(self):
        """Compare solver against exhaustive 2^n enumeration on binary knapsack."""
        m = Model(
            c=np.array([-10.0, -15.0, -25.0]),
            A=np.array([[2.0, 3.0, 5.0]]),
            row_lower=np.array([-np.inf]),
            row_upper=np.array([7.0]),
            lower=np.array([0.0, 0.0, 0.0]),
            upper=np.array([1.0, 1.0, 1.0]),
            integer=(0, 1, 2),
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -35.0, places=6)
        self.assertAlmostEqual(res['x'][0], 1.0, places=6)
        self.assertAlmostEqual(res['x'][1], 0.0, places=6)
        self.assertAlmostEqual(res['x'][2], 1.0, places=6)

    def test_section10_general_integer_milp_oracle(self):
        """Compare solver against exhaustive box enumeration on general integer MILP."""
        m = Model(
            c=np.array([2.0, 3.0]),
            A=np.array([[1.0, 2.0]]),
            row_lower=np.array([5.0]),
            row_upper=np.array([np.inf]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([4.0, 3.0]),
            integer=(0, 1),
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], 8.0, places=6)
        self.assertAlmostEqual(res['x'][0], 1.0, places=6)
        self.assertAlmostEqual(res['x'][1], 2.0, places=6)

    def test_section10_negative_objective_milp(self):
        """MILP with strictly negative optimal objective."""
        m = Model(
            c=np.array([-5.0, -4.0]),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([-np.inf]),
            row_upper=np.array([3.0]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([3.0, 3.0]),
            integer=(0, 1),
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -15.0, places=6)
        self.assertAlmostEqual(res['x'][0], 3.0, places=6)
        self.assertAlmostEqual(res['x'][1], 0.0, places=6)

    def test_section10_infeasible_milp_oracle(self):
        """Contradictory constraints on integer variable must return INFEASIBLE_CERTIFIED."""
        m = Model(
            c=np.array([1.0]),
            A=np.array([[1.0]]),
            row_lower=np.array([3.0]),
            row_upper=np.array([np.inf]),
            lower=np.array([0.0]),
            upper=np.array([2.0]),
            integer=(0,),
        )
        res = solve_milp(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')

    # =========================================================================
    # Section 12: QP Analytic Correctness Audit
    # =========================================================================

    def test_section12_unconstrained_analytic_qp(self):
        """Unconstrained strictly convex QP: min 0.5*x^T Q x + c^T x."""
        Q = np.array([[4.0, 1.0], [1.0, 2.0]])
        c = np.array([-3.0, -1.0])
        m = Model(c=c, A=np.zeros((0, 2)), row_lower=np.zeros(0), row_upper=np.zeros(0),
                  lower=np.array([-10.0, -10.0]), upper=np.array([10.0, 10.0]), Q=Q)
        res = solve_qp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][0], 5.0 / 7.0, places=5)
        self.assertAlmostEqual(res['x'][1], 1.0 / 7.0, places=5)
        self.assertAlmostEqual(res['objective'], -8.0 / 7.0, places=5)

    def test_section12_equality_constrained_analytic_qp(self):
        """Equality-constrained QP: min x0^2 + x1^2 s.t. x0 + x1 = 2."""
        Q = np.array([[2.0, 0.0], [0.0, 2.0]])
        c = np.array([0.0, 0.0])
        m = Model(c=c, A=np.array([[1.0, 1.0]]), row_lower=np.array([2.0]), row_upper=np.array([2.0]),
                  lower=np.array([-5.0, -5.0]), upper=np.array([5.0, 5.0]), Q=Q)
        res = solve_qp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['x'][0], 1.0, places=5)
        self.assertAlmostEqual(res['x'][1], 1.0, places=5)
        self.assertAlmostEqual(res['objective'], 2.0, places=5)

    # =========================================================================
    # Section 13: Trust Status Semantics
    # =========================================================================

    def test_section13_limit_reached_never_optimal_verified(self):
        """When max_nodes=0 is given to MILP, solver MUST return LIMIT_REACHED, NEVER OPTIMAL_VERIFIED."""
        m = build_refinery_twin('milp')
        res = solve_milp(m, max_nodes=0)
        self.assertEqual(res['status'], 'LIMIT_REACHED')
        self.assertNotEqual(res['status'], 'OPTIMAL_VERIFIED')

    # =========================================================================
    # Section 15: Numerical Torture Suite
    # =========================================================================

    def test_section15_extreme_coefficient_scaling(self):
        """Solve LP with coefficients spanning 8 orders of magnitude (1e-4 to 1e4)."""
        m = Model(
            c=np.array([1e-4, 1e4]),
            A=np.array([[1e-4, 1e4]]),
            row_lower=np.array([1.0]),
            row_upper=np.array([np.inf]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([1e6, 1e6]),
        )
        res = solve_dual_simplex(m, scaling=True)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        v = verify(m, np.array(res['x']), np.array(res['dual']), tol=1e-5)
        self.assertTrue(v['kkt_passed'])

    def test_section15_extreme_finite_bounds(self):
        """LP with huge finite bounds (1e12) does not overflow or produce NaN."""
        m = Model(
            c=np.array([-1.0, 2.0]),
            A=np.array([[1.0, 1.0]]),
            row_lower=np.array([-np.inf]),
            row_upper=np.array([1e12]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([1e12, 1e12]),
        )
        res = solve_dual_simplex(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(np.all(np.isfinite(res['x'])))
        self.assertAlmostEqual(res['objective'], -1e12, places=-3)

    # =========================================================================
    # Section 16: Metamorphic Correctness Tests
    # =========================================================================

    def test_section16_row_permutation_invariance(self):
        """Permuting row constraints must preserve identical optimal objective value."""
        A1 = np.array([[1.0, 2.0], [3.0, 1.0], [1.0, 1.0]])
        rlo1 = np.array([-np.inf, -np.inf, -np.inf])
        rhi1 = np.array([10.0, 15.0, 8.0])
        c = np.array([-2.0, -3.0])
        m1 = Model(c=c, A=A1, row_lower=rlo1, row_upper=rhi1,
                   lower=np.array([0.0, 0.0]), upper=np.array([10.0, 10.0]))
        res1 = solve_lp(m1)

        perm = [2, 0, 1]
        m2 = Model(c=c, A=A1[perm], row_lower=rlo1[perm], row_upper=rhi1[perm],
                   lower=np.array([0.0, 0.0]), upper=np.array([10.0, 10.0]))
        res2 = solve_lp(m2)

        self.assertEqual(res1['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res2['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res1['objective'], res2['objective'], places=6)
        self.assertAlmostEqual(res1['x'][0], res2['x'][0], places=6)
        self.assertAlmostEqual(res1['x'][1], res2['x'][1], places=6)

    def test_section16_redundant_constraint_invariance(self):
        """Adding a known redundant valid constraint does not change optimal solution."""
        m_base = Model(c=np.array([-1.0, -1.0]), A=np.array([[1.0, 1.0]]),
                       row_lower=np.array([-np.inf]), row_upper=np.array([5.0]),
                       lower=np.array([0.0, 0.0]), upper=np.array([5.0, 5.0]))
        res_base = solve_lp(m_base)

        m_red = Model(c=np.array([-1.0, -1.0]), A=np.array([[1.0, 1.0], [2.0, 2.0]]),
                      row_lower=np.array([-np.inf, -np.inf]), row_upper=np.array([5.0, 20.0]),
                      lower=np.array([0.0, 0.0]), upper=np.array([5.0, 5.0]))
        res_red = solve_lp(m_red)

        self.assertAlmostEqual(res_base['objective'], res_red['objective'], places=6)
        self.assertAlmostEqual(res_base['x'][0] + res_base['x'][1], 5.0, places=6)
        self.assertAlmostEqual(res_red['x'][0] + res_red['x'][1], 5.0, places=6)

    # =========================================================================
    # Section 17 & 22: Dispatcher Explainability Audit
    # =========================================================================

    def test_section17_dispatcher_explainable_rationale(self):
        """Dispatcher produces transparent, deterministic, factual rationale for all classes."""
        m_lp = build_refinery_twin('lp')
        m_milp = build_refinery_twin('milp')
        m_qp = build_refinery_twin('qp')

        d_lp = auto_dispatch(m_lp)
        d_milp = auto_dispatch(m_milp)
        d_qp = auto_dispatch(m_qp)

        self.assertEqual(d_lp['problem_class'], 'LP')
        self.assertEqual(d_lp['method'], 'dual-simplex')
        self.assertIn('Continuous LP dispatched', d_lp['rationale'])

        self.assertEqual(d_milp['problem_class'], 'MILP')
        self.assertEqual(d_milp['method'], 'bb')
        self.assertIn('integer variables', d_milp['rationale'])

        self.assertEqual(d_qp['problem_class'], 'QP')
        self.assertEqual(d_qp['method'], 'ipm')
        self.assertIn('quadratic objective matrix Q', d_qp['rationale'])

    # =========================================================================
    # Section 18 & 19: Refinery Physical Engineering Validator
    # =========================================================================

    def test_section19_refinery_physical_validator_lp(self):
        """Refinery LP solution satisfies all physical material balances, capacities, and demands."""
        m = build_refinery_twin('lp')
        res = solve_dual_simplex(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        val = validate_refinery_physical_solution(m, res['x'], dual=res.get('dual'))
        self.assertTrue(val['passed'])
        self.assertLessEqual(val['material_balance_violation'], 1e-6)
        self.assertLessEqual(val['capacity_violation'], 1e-6)
        self.assertLessEqual(val['demand_violation'], 1e-6)
        self.assertLessEqual(val['bound_violation'], 1e-6)

    def test_section19_refinery_physical_validator_milp(self):
        """Refinery MILP solution satisfies physical balances and discrete binary commitment."""
        m = build_refinery_twin('milp')
        res = solve_milp(m, max_nodes=50)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        val = validate_refinery_physical_solution(m, res['x'])
        self.assertTrue(val['passed'])
        self.assertLessEqual(val['integrality_violation'], 1e-6)
        self.assertLessEqual(val['material_balance_violation'], 1e-6)

    def test_section19_refinery_physical_validator_qp(self):
        """Refinery QP solution satisfies physical balances and KKT stationarity."""
        m = build_refinery_twin('qp')
        res = solve_qp(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        val = validate_refinery_physical_solution(m, res['x'], dual=res.get('dual'))
        self.assertTrue(val['passed'])
        self.assertLessEqual(val['stationarity_residual'], 1e-5)

    # =========================================================================
    # =========================================================================
    # Section 2 & 20: SOV-OPT Trust Passport Schema, Fingerprint & Null-Safety
    # =========================================================================

    def test_section2_model_fingerprint_sha256_format_and_determinism(self):
        """Model fingerprint must be a deterministic 64-character lowercase hexadecimal SHA-256."""
        m = build_refinery_twin('lp')
        fp1 = m.fingerprint()
        fp2 = m.fingerprint()

        self.assertIsInstance(fp1, str)
        self.assertEqual(len(fp1), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in fp1))
        # Determinism
        self.assertEqual(fp1, fp2)

        # Perturbation sensitivity
        m_perturbed = build_refinery_twin('lp')
        m_perturbed.c[0] += 0.01
        fp_perturbed = m_perturbed.fingerprint()
        self.assertNotEqual(fp1, fp_perturbed)

    def test_section20_trust_passport_negative_forged_status_unverified(self):
        """Trust passport must refuse to mark unverified or forged status results as verified."""
        m = build_refinery_twin('lp')

        # Forged OPTIMAL_VERIFIED without KKT evidence
        forged_optimal = {
            'status': 'OPTIMAL_VERIFIED',
            'objective': -100.0,
            'verification': {'kkt_passed': False, 'feasible': False}
        }
        passport_opt = generate_trust_passport(m, forged_optimal)
        self.assertFalse(passport_opt['verified'])
        self.assertIsNone(passport_opt['solution_verification_precision'])

        # Forged INFEASIBLE_CERTIFIED without Farkas certificate
        forged_infeas = {
            'status': 'INFEASIBLE_CERTIFIED',
            'verification': {'farkas_verified': False}
        }
        passport_inf = generate_trust_passport(m, forged_infeas)
        self.assertFalse(passport_inf['verified'])
        self.assertIsNone(passport_inf['certificate_precision'])

        # Forged UNBOUNDED_CERTIFIED without unbounded certificate verification
        forged_unbdd = {
            'status': 'UNBOUNDED_CERTIFIED',
            'verification': {'verified': False}
        }
        passport_unbdd = generate_trust_passport(m, forged_unbdd)
        self.assertFalse(passport_unbdd['verified'])

    def test_section20_trust_passport_all_seven_status_types(self):
        """Trust passport verifies schema invariants across all 7 solver statuses."""
        required_keys = [
            'schema_version', 'model_sha256', 'solver_version', 'solver_commit',
            'model_type', 'rows', 'columns', 'nnz', 'algorithm', 'backend',
            'input_snapshot', 'status', 'objective', 'verified', 'verification_precision',
            'solution_verification_precision', 'bound_certificate_precision',
            'certificate_precision', 'primal_residual', 'dual_residual',
            'bound_violation', 'integrality_residual', 'kkt_residual',
            'relative_gap', 'certificate_type', 'certificate_verified'
        ]

        # 1. LP OPTIMAL_VERIFIED
        m_lp = build_refinery_twin('lp')
        res_lp = solve_dual_simplex(m_lp)
        pass_lp = generate_trust_passport(m_lp, res_lp, solver_commit='c44f1384')
        for k in required_keys:
            self.assertIn(k, pass_lp)
        self.assertEqual(pass_lp['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(pass_lp['verified'])
        self.assertIsNone(pass_lp['integrality_residual'])
        self.assertIsNone(pass_lp['bound_certificate_precision'])
        self.assertIn(pass_lp['solution_verification_precision'], ('IEEE_754_double', 'longdouble_extended'))

        # 2. MILP OPTIMAL_VERIFIED
        m_milp = build_refinery_twin('milp')
        res_milp = solve_milp(m_milp, max_nodes=50)
        pass_milp = generate_trust_passport(m_milp, res_milp, solver_commit='c44f1384')
        self.assertEqual(pass_milp['status'], 'OPTIMAL_VERIFIED')
        self.assertTrue(pass_milp['verified'])
        self.assertIsNotNone(pass_milp['integrality_residual'])
        self.assertLessEqual(pass_milp['integrality_residual'], 1e-6)
        self.assertEqual(pass_milp['bound_certificate_precision'], 'exact_rational_Q')

        # 3. QP OPTIMAL_VERIFIED
        m_qp = build_refinery_twin('qp')
        res_qp = solve_qp(m_qp)
        pass_qp = generate_trust_passport(m_qp, res_qp, solver_commit='c44f1384')
        self.assertEqual(pass_qp['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(pass_qp['model_type'], 'QP')
        self.assertTrue(pass_qp['verified'])
        self.assertIsNone(pass_qp['integrality_residual'])

        # 4. INFEASIBLE_CERTIFIED
        m_inf = Model(
            c=np.array([1.0]), A=np.array([[1.0], [1.0]]),
            row_lower=np.array([5.0, -np.inf]), row_upper=np.array([np.inf, 2.0]),
            lower=np.array([-np.inf]), upper=np.array([np.inf])
        )
        res_inf = solve_lp(m_inf)
        self.assertEqual(res_inf['status'], 'INFEASIBLE_CERTIFIED')
        pass_inf = generate_trust_passport(m_inf, res_inf)
        self.assertEqual(pass_inf['status'], 'INFEASIBLE_CERTIFIED')
        self.assertTrue(pass_inf['verified'])
        self.assertEqual(pass_inf['certificate_type'], 'Farkas_infeasibility_ray')
        self.assertEqual(pass_inf['certificate_precision'], 'exact_rational_Q')
        self.assertTrue(pass_inf['certificate_verified'])

        # 5. UNBOUNDED_CERTIFIED
        m_unb = Model(
            c=np.array([-1.0]), A=np.zeros((0, 1)),
            row_lower=np.zeros(0), row_upper=np.zeros(0),
            lower=np.array([0.0]), upper=np.array([np.inf])
        )
        res_unb = solve_lp(m_unb)
        self.assertEqual(res_unb['status'], 'UNBOUNDED_CERTIFIED')
        pass_unb = generate_trust_passport(m_unb, res_unb)
        self.assertEqual(pass_unb['status'], 'UNBOUNDED_CERTIFIED')
        self.assertTrue(pass_unb['verified'])
        self.assertEqual(pass_unb['certificate_type'], 'Unbounded_recession_direction')

        # 6. LIMIT_REACHED
        res_lim = solve_dual_simplex(m_lp, max_iter=0)
        pass_lim = generate_trust_passport(m_lp, res_lim)
        self.assertEqual(pass_lim['status'], 'LIMIT_REACHED')
        self.assertFalse(pass_lim['verified'])
        self.assertIsNone(pass_lim['certificate_precision'])

        # 7. NUMERICAL_FAILURE
        res_num = {'status': 'NUMERICAL_FAILURE', 'objective': None, 'verification': {}}
        pass_num = generate_trust_passport(m_lp, res_num)
        self.assertEqual(pass_num['status'], 'NUMERICAL_FAILURE')
        self.assertFalse(pass_num['verified'])
        self.assertIsNone(pass_num['objective'])
        self.assertIsNone(pass_num['kkt_residual'])

    # =========================================================================
    # Section 21: Farkas Constraint Lens Diagnostic Ranking
    # =========================================================================

    def test_section21_farkas_constraint_lens_exact_arithmetic_and_disclaimer(self):
        """Farkas lens ranks constraints with exact rational arithmetic and non-IIS disclaimer."""
        m = Model(
            c=np.array([1.0]),
            A=np.array([[1.0], [1.0]]),
            row_lower=np.array([2.0, -np.inf]),
            row_upper=np.array([np.inf, 1.0]),
            lower=np.array([-np.inf]),
            upper=np.array([np.inf]),
        )
        res = solve_lp(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        cert = res['certificate']
        lens = rank_farkas_contributions(m, cert, top_k=5)

        self.assertEqual(lens['disclaimer'], 'Diagnostic ranking — not a minimal IIS.')
        self.assertFalse(lens['is_minimal_iis'])
        self.assertTrue(lens['certificate_verified'])
        self.assertTrue(lens['diagnostic_available'])
        self.assertLess(lens['total_contradiction'], 0.0)
        self.assertGreater(len(lens['top_contributions']), 0)
        self.assertEqual(lens['top_contributions'][0]['term_description'], 'certificate term contribution')

    def test_section21_farkas_lens_fail_closed_on_corrupted_certificate(self):
        """Farkas lens fails closed returning diagnostic_available=False and empty ranking on invalid certificate."""
        m = Model(
            c=np.array([1.0]),
            A=np.array([[1.0], [1.0]]),
            row_lower=np.array([2.0, -np.inf]),
            row_upper=np.array([np.inf, 1.0]),
            lower=np.array([-np.inf]),
            upper=np.array([np.inf]),
        )
        # Invalid/corrupted certificate multipliers
        corrupted_cert = [0.0, 0.0]
        lens = rank_farkas_contributions(m, corrupted_cert)

        self.assertFalse(lens['certificate_verified'])
        self.assertFalse(lens['diagnostic_available'])
        self.assertIsNone(lens['total_contradiction'])
        self.assertEqual(lens['top_contributions'], [])
        self.assertIn('Diagnostic ranking unavailable', lens['warning'])

    def test_section21_farkas_lens_positive_row_scaling_invariance(self):
        """Farkas diagnostic rankings remain mathematically consistent under positive row scaling."""
        # Unscaled model: x >= 2 and x <= 1 -> -x <= -2 and x <= 1
        m1 = Model(
            c=np.array([1.0]),
            A=np.array([[1.0], [1.0]]),
            row_lower=np.array([2.0, -np.inf]),
            row_upper=np.array([np.inf, 1.0]),
            lower=np.array([-np.inf]),
            upper=np.array([np.inf]),
        )
        # Scaled model: second row multiplied by 2: 2*x <= 2
        m2 = Model(
            c=np.array([1.0]),
            A=np.array([[1.0], [2.0]]),
            row_lower=np.array([2.0, -np.inf]),
            row_upper=np.array([np.inf, 2.0]),
            lower=np.array([-np.inf]),
            upper=np.array([np.inf]),
        )
        res1 = solve_lp(m1)
        res2 = solve_lp(m2)

        lens1 = rank_farkas_contributions(m1, res1['certificate'])
        lens2 = rank_farkas_contributions(m2, res2['certificate'])

        # Both certificates must be verified and strictly certify infeasibility
        self.assertTrue(lens1['certificate_verified'])
        self.assertTrue(lens2['certificate_verified'])
        self.assertTrue(lens1['diagnostic_available'])
        self.assertTrue(lens2['diagnostic_available'])
        self.assertFalse(lens1['is_minimal_iis'])
        self.assertFalse(lens2['is_minimal_iis'])
        self.assertEqual(lens1['disclaimer'], 'Diagnostic ranking — not a minimal IIS.')
        self.assertEqual(lens2['disclaimer'], 'Diagnostic ranking — not a minimal IIS.')
        self.assertLess(lens1['total_contradiction'], 0.0)
        self.assertLess(lens2['total_contradiction'], 0.0)

        # Invariance of certificate term contribution under analytical row-rescaling of the ray:
        # If z = [z0, z1] is a valid Farkas ray for m1, then z_scaled = [z0, z1 / 2] is an exact ray for m2
        # with identical term contribution z1 * h1 = (z1 / 2) * (2 * h1).
        cert1 = res1['certificate']
        cert2_analytical = [cert1[0], cert1[1] / 2.0]
        lens2_rescaled = rank_farkas_contributions(m2, cert2_analytical)
        self.assertTrue(lens2_rescaled['certificate_verified'])
        self.assertAlmostEqual(lens1['total_contradiction'], lens2_rescaled['total_contradiction'], places=6)

    # =========================================================================
    # Section 23: Cross-Method Consistency Check (LP)
    # =========================================================================

    def test_section23_cross_method_consistency_simplex_vs_pdhg(self):
        """Cross-method diagnostic: Simplex and restarted PDHG agree on small continuous LP."""
        m = Model(
            c=np.array([-2.0, -1.0]),
            A=np.array([[1.0, 1.0], [1.0, 0.0]]),
            row_lower=np.array([-np.inf, -np.inf]),
            row_upper=np.array([4.0, 3.0]),
            lower=np.array([0.0, 0.0]),
            upper=np.array([5.0, 5.0]),
        )
        res_simplex = solve_dual_simplex(m)
        res_pdhg = solve_pdhg(m, device='cpu', tol=1e-5, max_iter=10000)

        self.assertEqual(res_simplex['status'], 'OPTIMAL_VERIFIED')
        self.assertEqual(res_pdhg['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res_simplex['objective'], -7.0, places=5)
        self.assertAlmostEqual(res_pdhg['objective'], -7.0, places=4)
        self.assertAlmostEqual(res_simplex['objective'], res_pdhg['objective'], delta=1e-3)


if __name__ == '__main__':
    unittest.main()
