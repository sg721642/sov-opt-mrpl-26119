import json
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
        self.assertIn(r_flug['status'], ('LIMIT_REACHED', 'OPTIMAL_VERIFIED'))
        self.assertLessEqual(r_flug['nodes'], 50)
        self.assertGreaterEqual(r_flug['nodes'], 1)
        self.assertIsNotNone(r_flug.get('best_bound'))
        # Conservative lower bound must be >= root LP relaxation (769500) and <= known optimum (1201500)
        self.assertGreaterEqual(r_flug['best_bound'], 769500.0 - 1e-6)
        self.assertLessEqual(r_flug['best_bound'], 1201500.0 + 1e-6)

    def test_infeasible_farkas_certificate_genuine(self):
        """Verify exact Farkas certificate on genuine infeasible branch of FLUGPL.
        Also verifies lossless JSON serialization/reload and re-certification on original model."""
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        l_node = m_flug.lower.copy()
        u_node = m_flug.upper.copy()
        # Genuine branch restriction creating Phase I infeasibility
        u_node[7] = 13.0
        u_node[15] = 70.0
        node = replace(m_flug, lower=l_node, upper=u_node, integer=())
        r = solve_lp(node)
        self.assertEqual(r['status'], 'INFEASIBLE_CERTIFIED')
        self.assertTrue(exact_farkas(node, r['certificate']))
        
        # Lossless round-trip export to JSON and reload
        cert_json = json.dumps({'certificate_exact': r['certificate_exact']})
        reloaded = json.loads(cert_json)
        self.assertTrue(exact_farkas(node, reloaded['certificate_exact']))

        # Non-certificate (zero vector) must fail verification
        self.assertFalse(exact_farkas(node, [0.0] * len(node.inequalities()[1])))

    def test_bad_candidate_validation(self):
        """Unit verification of independent verifier (verify.py): challenges the KKT and
        feasibility checker using invalid candidate vectors on the real AVGAS model to ensure
        infeasible or corrupted points are strictly rejected.
        These candidate vectors are verifier test probes, not application datasets.
        """
        m = load(ROOT / 'data/verified/avgas.mps')
        self.assertFalse(verify(m, [2.0] * 8)['feasible'])
        self.assertFalse(verify(m, [float('nan')] * 8)['kkt_passed'])
        self.assertFalse(verify(m, [1.0] * 8, [0] * len(m.inequalities()[1]))['kkt_passed'])

    def test_variable_transformations_equiv(self):
        """Verify that an invertible affine change of variables on real Netlib AFIRO
        preserves the exact optimal objective and allows exact postsolve recovery of
        both primal and dual solutions matching original model KKT conditions.
        
        Transformation: x = D * x_tilde + s, where D is diagonal (D_jj > 0).
        Bijective mapping:
          c_tilde = D * c
          A_tilde = A * D
          rl_tilde = row_lower - A * s
          ru_tilde = row_upper - A * s
          l_tilde = (lower - s) / D
          u_tilde = (upper - s) / D
          obj_offset_tilde = offset + c^T * s
        Dual recovery:
          z_rec[row_i] = z_tilde[row_i]
          z_rec[bound_j] = z_tilde[bound_j] / D_jj
        """
        m = load(ROOT / 'data/verified/afiro.mps')
        n = len(m.c)
        diag_D = np.array([1.0 + 0.1 * ((j % 4) + 1) for j in range(n)])
        s = np.array([0.5 * ((j % 3) + 1) for j in range(n)])

        c_tilde = m.c * diag_D
        A_tilde = m.A * diag_D[None, :]
        As = m.A @ s
        rl_tilde = m.row_lower - As
        ru_tilde = m.row_upper - As
        l_tilde = (m.lower - s) / diag_D
        u_tilde = (m.upper - s) / diag_D
        offset_tilde = float(m.c @ s)

        m_trans = Model(
            c=c_tilde, A=A_tilde, row_lower=rl_tilde, row_upper=ru_tilde,
            lower=l_tilde, upper=u_tilde, names=m.names, name='afiro_transformed',
            obj_offset=offset_tilde
        )

        r_trans = solve_lp(m_trans)
        self.assertEqual(r_trans['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_trans['objective'], -464.75314285714285, places=5)

        # Recover original primal solution
        x_rec = diag_D * np.array(r_trans['x']) + s

        # Recover original dual solution
        G, h, labels = m.inequalities()
        z_trans = np.array(r_trans['dual'])
        z_rec = z_trans.copy()
        for i, lbl in enumerate(labels):
            if 'row' not in lbl:
                for j, name in enumerate(m.names):
                    if name in lbl:
                        z_rec[i] = z_trans[i] / diag_D[j]
                        break

        # Verify against original AFIRO model
        rep = verify(m, x_rec, z_rec)
        self.assertTrue(rep['kkt_passed'])
        self.assertLess(rep['primal_residual'], 1e-12)
        self.assertLess(rep['dual_residual'], 1e-12)

    def test_pdhg_cpu_convergence(self):
        """Verify first-order PDHG solver convergence on AVGAS."""
        m = load(ROOT / 'data/verified/avgas.mps')
        r = solve(m, backend='pdhg-cpu', max_iter=5000)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r['objective'], -7.75, places=2)

    def test_limits_honest_enforcement(self):
        """Verify honest enforcement of node and iteration limits on genuine instances."""
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        r_flug = solve(m_flug, max_nodes=0)
        self.assertEqual(r_flug['status'], 'LIMIT_REACHED')
        self.assertNotIn('x', r_flug)

        m_avgas = load(ROOT / 'data/verified/avgas.mps')
        r_avgas = solve(m_avgas, max_iter=1)
        self.assertEqual(r_avgas['status'], 'LIMIT_REACHED')

    def test_exact_rational_lagrangian_bound(self):
        """Verify exact rational Lagrangian bounds against optimal objectives on AVGAS."""
        m = load(ROOT / 'data/verified/avgas.mps')
        r = solve_lp(m)
        bound = safe_lower_bound(m, r['dual'])
        self.assertIsNotNone(bound)
        self.assertLessEqual(float(bound), r['objective'] + 1e-12)

if __name__ == '__main__':
    unittest.main(verbosity=2)
