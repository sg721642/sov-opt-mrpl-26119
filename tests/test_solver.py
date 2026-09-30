import unittest
from pathlib import Path
from fractions import Fraction
import numpy as np
from sovopt import Model, load, solve
from sovopt.linalg import LU
from sovopt.verify import verify, safe_lower_bound, exact_farkas
from sovopt.simplex import solve_lp
from sovopt.transforms import transform_model
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]

class SolverTests(unittest.TestCase):
    def test_lu_pivot_refinement_real_basis(self):
        """Verify LU factorization residuals on actual bases from Netlib benchmarks."""
        for name, tol in [('afiro', 1e-12), ('sc50a', 1e-12), ('blend', 1e-10)]:
            m = load(ROOT / f'data/verified/{name}.mps')
            r = solve_lp(m)
            self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
            t = transform_model(m)
            m_eq, n_trans = t.A_eq.shape
            m_le = t.A_le.shape[0]
            m_total = m_eq + m_le
            A_all = np.vstack([t.A_eq, t.A_le]) if m_le > 0 else t.A_eq.copy()
            slack_blocks = [np.vstack([np.zeros((m_eq, m_le)), np.eye(m_le)])]
            M = np.hstack([A_all, slack_blocks[0], np.eye(m_total)])
            basis = r['basis']
            B = M[:, basis]
            # Deterministic test vector derived from model dimensions
            b = np.array([float(i + 1) / float(m_total) for i in range(m_total)])
            x = LU(B).solve(b)
            res = np.max(np.abs(B @ x - b))
            self.assertLess(res, tol, f'LU residual too high on {name}: {res}')

    def test_verified_real_instances(self):
        """Test real-source documented instances with published reference values."""
        # 1. AVGAS (Petroleum refinery aviation gasoline blending LP, Symonds 1955)
        r_avgas = solve(load(ROOT / 'data/verified/avgas.mps'))
        self.assertEqual(r_avgas['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_avgas['objective'], -7.75, places=5)
        self.assertTrue(r_avgas['verification']['kkt_passed'])

        # 2. AFIRO (Netlib LP, Michael Saunders, Systems Optimization Laboratory Stanford)
        r_afiro = solve(load(ROOT / 'data/verified/afiro.mps'))
        self.assertEqual(r_afiro['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_afiro['objective'], -464.75314285714285, places=5)
        self.assertTrue(r_afiro['verification']['kkt_passed'])

        # 3. SC50A (Netlib LP, staircase model)
        r_sc50a = solve(load(ROOT / 'data/verified/sc50a.mps'))
        self.assertEqual(r_sc50a['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_sc50a['objective'], -64.5750770585645, places=5)
        self.assertTrue(r_sc50a['verification']['kkt_passed'])

        # 4. SC50B (Netlib LP, staircase model)
        r_sc50b = solve(load(ROOT / 'data/verified/sc50b.mps'))
        self.assertEqual(r_sc50b['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_sc50b['objective'], -70.0, places=5)
        self.assertTrue(r_sc50b['verification']['kkt_passed'])

        # 5. BLEND (Netlib LP, refinery blending problem with 43 equality rows)
        r_blend = solve(load(ROOT / 'data/verified/blend.mps'))
        self.assertEqual(r_blend['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_blend['objective'], -30.812149845828237, places=5)
        self.assertTrue(r_blend['verification']['kkt_passed'])

    def test_milib_flugpl_solve_and_lower_bound(self):
        """Test MIPLIB airline fleet allocation MILP with conservative rational lower bound."""
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        r_flug = solve(m_flug, max_nodes=50)
        self.assertEqual(r_flug['status'], 'LIMIT_REACHED')
        self.assertAlmostEqual(r_flug['best_bound'], 769500.0, places=1)
        self.assertEqual(r_flug['nodes'], 50)

    def test_infeasible_farkas_certificate_genuine(self):
        """Verify exact Farkas certificate on genuine infeasible branch of FLUGPL."""
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        l_node = m_flug.lower.copy()
        u_node = m_flug.upper.copy()
        # Genuine branch restriction that creates Phase I infeasibility
        u_node[7] = 13.0
        u_node[15] = 70.0
        node = replace(m_flug, lower=l_node, upper=u_node, integer=())
        r = solve_lp(node)
        self.assertEqual(r['status'], 'INFEASIBLE_CERTIFIED')
        self.assertTrue(exact_farkas(node, r['certificate']))
        # Non-certificate (zero vector) must fail verification
        self.assertFalse(exact_farkas(node, [0.0] * len(node.inequalities()[1])))

    def test_bad_candidate_validation(self):
        """Verify independent verifier properly rejects non-feasible / invalid points."""
        m = load(ROOT / 'data/verified/avgas.mps')
        self.assertFalse(verify(m, [2.0] * 8)['feasible'])
        self.assertFalse(verify(m, [float('nan')] * 8)['kkt_passed'])
        self.assertFalse(verify(m, [1.0] * 8, [0] * len(m.inequalities()[1]))['kkt_passed'])

    def test_box_and_unconstrained(self):
        """Verify separable box optimization and unconstrained ray detection."""
        # Bounded box model: c = [-2, 3], x0 in [-3, 5], x1 in [2, 4]
        m_box = Model.from_dict({'c': [-2.0, 3.0], 'lower': [-3.0, 2.0], 'upper': [5.0, 4.0]})
        r_box = solve_lp(m_box)
        self.assertEqual(r_box['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_box['objective'], -4.0)
        self.assertEqual(r_box['x'], [5.0, 2.0])

        # Unbounded ray detection: negative cost with infinite upper bound
        m_ray = Model.from_dict({'c': [-2.0, 3.0], 'lower': [0.0, 0.0], 'upper': [None, 4.0]})
        r_ray = solve_lp(m_ray)
        self.assertEqual(r_ray['status'], 'UNBOUNDED_CERTIFIED')

    def test_variable_transformations_equiv(self):
        """Verify that variable transformations preserve exact optimal objectives."""
        m = load(ROOT / 'data/verified/afiro.mps')
        r_orig = solve_lp(m)
        x_opt = np.array(r_orig['x'])
        obj_opt = r_orig['objective']

        # Fix variable 0 to its optimal value
        l_fix = m.lower.copy(); u_fix = m.upper.copy()
        l_fix[0] = x_opt[0]; u_fix[0] = x_opt[0]
        m_fix = replace(m, lower=l_fix, upper=u_fix)
        r_fix = solve_lp(m_fix)
        self.assertEqual(r_fix['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_fix['objective'], obj_opt, places=6)

        # Upper-only variable bound
        l_free = m.lower.copy(); u_free = m.upper.copy()
        l_free[2] = -np.inf; u_free[2] = x_opt[2] + 10.0
        m_free = replace(m, lower=l_free, upper=u_free)
        r_free = solve_lp(m_free)
        self.assertEqual(r_free['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_free['objective'], obj_opt, places=6)

    def test_pdhg_cpu_convergence(self):
        """Verify first-order PDHG solver convergence on AVGAS."""
        m = load(ROOT / 'data/verified/avgas.mps')
        r = solve(m, backend='pdhg-cpu', max_iter=5000)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r['objective'], -7.75, places=2)

    def test_limits_honest_enforcement(self):
        """Verify honest enforcement of node and iteration limits."""
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        r_flug = solve(m_flug, max_nodes=0)
        self.assertEqual(r_flug['status'], 'LIMIT_REACHED')
        self.assertNotIn('x', r_flug)

        m_avgas = load(ROOT / 'data/verified/avgas.mps')
        r_avgas = solve(m_avgas, max_iter=1)
        self.assertEqual(r_avgas['status'], 'LIMIT_REACHED')

    def test_nonconvex_and_miqp_rejected(self):
        """Verify rejection of non-positive semidefinite matrices and MIQP."""
        with self.assertRaises(ValueError):
            Model.from_dict({'c': [0.0], 'Q': [[-1.0]]})
        with self.assertRaises(ValueError):
            Model.from_dict({'c': [0.0], 'Q': [[1.0]], 'integer': [0]})

    def test_exact_rational_lagrangian_bound(self):
        """Verify exact rational Lagrangian bounds against optimal objectives."""
        m = load(ROOT / 'data/verified/avgas.mps')
        r = solve_lp(m)
        bound = safe_lower_bound(m, r['dual'])
        self.assertIsNotNone(bound)
        self.assertLessEqual(float(bound), r['objective'] + 1e-12)

if __name__ == '__main__':
    unittest.main(verbosity=2)
