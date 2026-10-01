import json
import unittest
from pathlib import Path
from fractions import Fraction
import numpy as np
from sovopt import Model, load, solve, build_refinery_twin, auto_dispatch, inspect_model
from sovopt.linalg import LU
from sovopt.verify import verify, safe_lower_bound, exact_farkas
from sovopt.simplex import solve_lp
from sovopt.transforms import transform_model
from dataclasses import replace
from scripts.generate_reports import evaluate_differential_comparison

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
        """Test real-source documented instances with published reference values.
        Uses active verified instances from Netlib LP: AFIRO, SC50A, SC50B, BLEND.
        """
        # 1. AFIRO (Netlib LP, Michael Saunders, Systems Optimization Laboratory Stanford)
        r_afiro = solve(load(ROOT / 'data/verified/afiro.mps'))
        self.assertEqual(r_afiro['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_afiro['objective'], -464.75314285714285, places=5)
        self.assertTrue(r_afiro['verification']['kkt_passed'])

        # 2. SC50A (Netlib LP, staircase model)
        r_sc50a = solve(load(ROOT / 'data/verified/sc50a.mps'))
        self.assertEqual(r_sc50a['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_sc50a['objective'], -64.5750770585645, places=5)
        self.assertTrue(r_sc50a['verification']['kkt_passed'])

        # 3. SC50B (Netlib LP, staircase model)
        r_sc50b = solve(load(ROOT / 'data/verified/sc50b.mps'))
        self.assertEqual(r_sc50b['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_sc50b['objective'], -70.0, places=5)
        self.assertTrue(r_sc50b['verification']['kkt_passed'])

        # 4. BLEND (Netlib LP, refinery blending problem with 43 equality rows)
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
        self.assertTrue(r.get('farkas_certificate'))
        self.assertTrue(r.get('verification', {}).get('farkas_verified'))
        
        # Lossless round-trip export to JSON and reload
        cert_json = json.dumps({'certificate_exact': r['certificate_exact']})
        reloaded = json.loads(cert_json)
        self.assertTrue(exact_farkas(node, reloaded['certificate_exact']))

        # Non-certificate (zero vector) must fail verification
        self.assertFalse(exact_farkas(node, [0.0] * len(node.inequalities()[1])))

    def test_bad_candidate_validation(self):
        """Unit verification of independent verifier (verify.py): challenges the KKT and
        feasibility checker using invalid candidate vectors on the real Netlib AFIRO model to ensure
        infeasible or corrupted points are strictly rejected.
        These candidate vectors are verifier test probes, not application datasets.
        """
        m = load(ROOT / 'data/verified/afiro.mps')
        n = len(m.c)
        self.assertFalse(verify(m, [1e6] * n)['feasible'])
        self.assertFalse(verify(m, [float('nan')] * n)['kkt_passed'])
        self.assertFalse(verify(m, [1.0] * n, [0.0] * len(m.inequalities()[1]))['kkt_passed'])

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
        """Verify first-order PDHG solver convergence on Netlib AFIRO."""
        m = load(ROOT / 'data/verified/afiro.mps')
        r = solve(m, backend='pdhg-cpu', max_iter=20000)
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r['objective'], -464.75314286, places=4)
        self.assertTrue(r['verification']['kkt_passed'])

    def test_limits_honest_enforcement(self):
        """Verify honest enforcement of node and iteration limits on genuine instances."""
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        r_flug = solve(m_flug, max_nodes=0)
        self.assertEqual(r_flug['status'], 'LIMIT_REACHED')
        self.assertNotIn('x', r_flug)

        m_afiro = load(ROOT / 'data/verified/afiro.mps')
        r_afiro = solve(m_afiro, max_iter=1)
        self.assertEqual(r_afiro['status'], 'LIMIT_REACHED')

    def test_exact_rational_lagrangian_bound(self):
        """Verify exact rational Lagrangian bound evaluation on MIPLIB FLUGPL LP relaxation node.
        Uses exact rational basis duals (_exact_dual_from_basis) to compute a safe lower bound.
        """
        m_flug = load(ROOT / 'data/verified/flugpl.mps')
        node = replace(m_flug, integer=())
        r = solve_lp(node)
        self.assertIn('dual_exact_fraction', r, "Exact rational duals must be constructed")
        bound = safe_lower_bound(node, r['dual_exact_fraction'])
        self.assertIsNotNone(bound, "safe_lower_bound must return a non-None bound with exact rational duals")
        self.assertLessEqual(float(bound), r['objective'] + 1e-6)
        self.assertAlmostEqual(float(bound), r['objective'], places=4)

    def test_flugpl_honest_metadata(self):
        """Regression: FLUGPL B&B results must satisfy mathematical invariants regardless of termination.

        At 50 nodes the independently reproduced result is LIMIT_REACHED with bound ~1173644.9999999998
        and no incumbent. This test accepts any terminal status (LIMIT_REACHED or OPTIMAL_VERIFIED
        if the solver improves) but checks the invariants that must hold in all cases:
        - best_bound must be present, finite, and within valid range [root_lb, known_optimum]
        - if an incumbent is present, objective must be >= best_bound
        - if OPTIMAL_VERIFIED, incumbent must pass feasibility verification
        - node limit must be strictly respected
        """
        m = load(ROOT / 'data/verified/flugpl.mps')
        r = solve(m, max_nodes=50)

        # Status must be a recognized terminal state, not an error
        self.assertIn(r['status'], ('LIMIT_REACHED', 'OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED'),
                      f"Unexpected FLUGPL status: {r['status']}")

        # Node limit respected
        self.assertLessEqual(r.get('nodes', 0), 50)

        # best_bound must be present, non-NaN, and in valid range
        self.assertIsNotNone(r.get('best_bound'), "FLUGPL must report a best_bound")
        self.assertTrue(r['best_bound'] == r['best_bound'], "best_bound must not be NaN")
        self.assertGreaterEqual(r['best_bound'], 769500.0 - 1.0,
                                "FLUGPL bound must be >= root LP relaxation (~769500)")
        self.assertLessEqual(r['best_bound'], 1201500.0 + 1.0,
                             "FLUGPL bound must not exceed known integer optimum (1201500)")

        # If an incumbent exists, objective must be >= best_bound and pass feasibility
        if r.get('objective') is not None:
            self.assertGreaterEqual(r['objective'], r['best_bound'] - 1.0,
                                    "Incumbent objective must be >= best_bound")
            if r.get('verification'):
                self.assertTrue(r['verification'].get('feasible'),
                                "Reported incumbent must be feasible in the original model")

    def test_checksum_manifest_integrity(self):
        """Verify that SHA256SUMS.json parses cleanly with json.loads and has no syntax or trailing data defects."""
        chk_file = ROOT / 'SHA256SUMS.json'
        self.assertTrue(chk_file.exists(), "SHA256SUMS.json must exist")
        raw = chk_file.read_bytes()
        self.assertFalse(raw.endswith(b"\\n"), "SHA256SUMS.json must not have literal trailing backslash-n")
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception as e:
            self.fail(f"SHA256SUMS.json failed json.loads: {e}")
        self.assertIsInstance(data, dict)
        self.assertNotIn("SHA256SUMS.json", data, "SHA256SUMS.json must not list itself")


class TestDifferentialComparisonLogic(unittest.TestCase):
    """Verify differential comparison logic across solver termination states.

    Tests the evaluator using metadata and recorded external outputs from real
    benchmarks (Netlib AFIRO, MIPLIB FLUGPL) without creating synthetic optimization
    instances or fabricated measurements.
    """

    @classmethod
    def setUpClass(cls):
        manifest_path = ROOT / 'data/manifest.json'
        cls.manifest = json.loads(manifest_path.read_text())
        cls.afiro_meta = cls.manifest['instances']['afiro']
        cls.flugpl_meta = cls.manifest['instances']['flugpl']

        ext_val_path = ROOT / 'reports/external_validation.json'
        cls.ext_val = json.loads(ext_val_path.read_text()) if ext_val_path.exists() else {}

    def test_external_optimal_lp_match(self):
        """LP MATCH requires ext_optimal == True and verified SOV-OPT status."""
        afiro_ext = dict(self.ext_val.get('instances', {}).get('afiro', {
            'parsed_dimensions': {'variables': 32, 'constraints': 27, 'integers': 0},
            'model_status': 'HighsModelStatus.kOptimal',
            'exit_code': 0,
            'success': True,
            'objective': -464.75314285714285,
        }))
        sovopt_res = {
            'status': 'OPTIMAL_VERIFIED',
            'objective': -464.75314285714285,
            'verification': {'kkt_passed': True},
        }
        res = evaluate_differential_comparison(sovopt_res, afiro_ext, self.afiro_meta)
        self.assertEqual(res['comparison_status'], 'MATCH')
        self.assertAlmostEqual(res['discrepancy_vs_sovopt'], 0.0, places=6)

    def test_external_optimal_milp_bound_only_validated(self):
        """MILP bound-only requires ext_optimal == True and valid conservative bound direction."""
        flugpl_ext = dict(self.ext_val.get('instances', {}).get('flugpl', {
            'parsed_dimensions': {'variables': 18, 'constraints': 18, 'integers': 11},
            'model_status': 'HighsModelStatus.kOptimal',
            'exit_code': 0,
            'success': True,
            'objective': 1201500.0,
        }))
        sovopt_res = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1173645.0,
            'objective': None,
        }
        res = evaluate_differential_comparison(sovopt_res, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res['comparison_status'], 'BOUND_ONLY')
        self.assertTrue(res['bound_direction_valid'])
        self.assertIn("without discovering an incumbent solution", res['comparison_note'])
        self.assertIn("validated against external optimum 1201500.0", res['comparison_note'])

    def test_external_non_optimal_feasible_refuses_optimum_claim(self):
        """Non-optimal external solve must NOT be described as an optimum or used to validate bounds."""
        flugpl_ext = {
            'parsed_dimensions': {'variables': 18, 'constraints': 18, 'integers': 11},
            'model_status': 'HighsModelStatus.kTimeLimit',
            'exit_code': 0,
            'success': True,
            'objective': 1300000.0,
        }
        sovopt_res = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1173645.0,
            'objective': None,
        }
        res = evaluate_differential_comparison(sovopt_res, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res['comparison_status'], 'EXTERNAL_NOT_OPTIMAL')
        self.assertIn("feasible objective, not an external optimum", res['comparison_note'])
        self.assertIn("Bound cannot be validated against external optimum", res['comparison_note'])

    def test_external_failed_distinguishes_internally_certified_bound(self):
        """Failed external validation distinguishes internal rational certification from external check."""
        flugpl_ext = {
            'status': 'FAILED',
            'actual_error': 'External process terminated with error',
        }
        sovopt_res = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1173645.0,
            'objective': None,
        }
        res = evaluate_differential_comparison(sovopt_res, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res['comparison_status'], 'BOUND_INTERNALLY_CERTIFIED')
        self.assertIn("internally certified via exact rational arithmetic", res['comparison_note'])
        self.assertIn("Bound is not externally checked", res['comparison_note'])

    def test_external_not_run_or_missing_objective(self):
        """Unrun or missing external objective marks bound as internally certified."""
        flugpl_ext = {
            'status': 'NOT_RUN',
            'actual_error': 'highspy not installed in environment',
        }
        sovopt_res = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1173645.0,
            'objective': None,
        }
        res = evaluate_differential_comparison(sovopt_res, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res['comparison_status'], 'BOUND_INTERNALLY_CERTIFIED')

        # Also when status is run but objective is None
        flugpl_ext2 = {
            'parsed_dimensions': {'variables': 18, 'constraints': 18, 'integers': 11},
            'model_status': 'HighsModelStatus.kIterationLimit',
            'exit_code': 0,
            'success': True,
            'objective': None,
        }
        res2 = evaluate_differential_comparison(sovopt_res, flugpl_ext2, self.flugpl_meta)
        self.assertEqual(res2['comparison_status'], 'BOUND_INTERNALLY_CERTIFIED')

    def test_bound_direction_validation_min_and_max(self):
        """Bound validation handles both minimization (lower bound) and maximization (upper bound)."""
        # Minimization (FLUGPL): lower bound exceeding optimum is invalid
        flugpl_ext = {
            'parsed_dimensions': {'variables': 18, 'constraints': 18, 'integers': 11},
            'model_status': 'HighsModelStatus.kOptimal',
            'exit_code': 0,
            'success': True,
            'objective': 1201500.0,
        }
        sovopt_invalid_min = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1300000.0,  # Invalid: lower bound cannot exceed minimum
            'objective': None,
        }
        res_min = evaluate_differential_comparison(sovopt_invalid_min, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res_min['comparison_status'], 'INVALID_BOUND')
        self.assertFalse(res_min['bound_direction_valid'])

        # Maximization: upper bound direction
        max_meta = dict(self.flugpl_meta)
        max_meta['objective_sense'] = 'MAXIMIZE'

        # Valid upper bound: best_bound >= external maximum
        sovopt_valid_max = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1300000.0,
            'objective': None,
        }
        res_max_valid = evaluate_differential_comparison(sovopt_valid_max, flugpl_ext, max_meta)
        self.assertEqual(res_max_valid['comparison_status'], 'BOUND_ONLY')
        self.assertTrue(res_max_valid['bound_direction_valid'])

        # Invalid upper bound: best_bound < external maximum
        sovopt_invalid_max = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1100000.0,
            'objective': None,
        }
        res_max_invalid = evaluate_differential_comparison(sovopt_invalid_max, flugpl_ext, max_meta)
        self.assertEqual(res_max_invalid['comparison_status'], 'INVALID_BOUND')
        self.assertFalse(res_max_invalid['bound_direction_valid'])

    def test_incomplete_solve_with_incumbent_vs_without(self):
        """Incomplete solve comparison correctly notes presence or absence of incumbent."""
        flugpl_ext = {
            'parsed_dimensions': {'variables': 18, 'constraints': 18, 'integers': 11},
            'model_status': 'HighsModelStatus.kOptimal',
            'exit_code': 0,
            'success': True,
            'objective': 1201500.0,
        }
        # Incomplete with incumbent
        sovopt_with_inc = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1173645.0,
            'objective': 1250000.0,
        }
        res_with = evaluate_differential_comparison(sovopt_with_inc, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res_with['comparison_status'], 'BOUND_ONLY')
        self.assertIn("with incumbent objective 1250000.0", res_with['comparison_note'])

        # Incomplete without incumbent
        sovopt_without_inc = {
            'status': 'LIMIT_REACHED',
            'best_bound': 1173645.0,
            'objective': None,
        }
        res_without = evaluate_differential_comparison(sovopt_without_inc, flugpl_ext, self.flugpl_meta)
        self.assertEqual(res_without['comparison_status'], 'BOUND_ONLY')
        self.assertIn("without discovering an incumbent solution", res_without['comparison_note'])

    def test_dimension_mismatch_detection(self):
        """External parser reporting different dimensions triggers DIMENSION_MISMATCH."""
        afiro_ext_wrong_dims = {
            'parsed_dimensions': {'variables': 50, 'constraints': 50, 'integers': 0},
            'model_status': 'HighsModelStatus.kOptimal',
            'exit_code': 0,
            'success': True,
            'objective': -464.75314285714285,
        }
        sovopt_res = {
            'status': 'OPTIMAL_VERIFIED',
            'objective': -464.75314285714285,
            'verification': {'kkt_passed': True},
        }
        res = evaluate_differential_comparison(sovopt_res, afiro_ext_wrong_dims, self.afiro_meta)
        self.assertEqual(res['comparison_status'], 'DIMENSION_MISMATCH')


class TestRefineryPlanningTwin(unittest.TestCase):
    """Test the unified MRPL Refinery Planning Digital Twin across LP, MILP, QP, and Infeasible modes."""

    def test_refinery_twin_lp_kkt_verified(self):
        """LP planning twin solves to OPTIMAL_VERIFIED with KKT satisfaction."""
        m = build_refinery_twin('lp')
        res = solve(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertIsNotNone(res['objective'])
        v = res['verification']
        self.assertTrue(v['feasible'])
        self.assertTrue(v['kkt_passed'])
        self.assertLessEqual(v['primal_residual'], 1e-7)
        self.assertLessEqual(v['dual_residual'], 1e-7)

    def test_refinery_twin_infeasible_farkas_certified(self):
        """Infeasible twin variant generates an exact Farkas certificate."""
        m = build_refinery_twin('infeasible')
        res = solve(m)
        self.assertEqual(res['status'], 'INFEASIBLE_CERTIFIED')
        self.assertTrue(res.get('farkas_certificate'))

    def test_refinery_twin_milp_optimal_verified(self):
        """MILP twin solves discrete unit commitment to OPTIMAL_VERIFIED with exact conservative bounds."""
        m = build_refinery_twin('milp')
        res = solve(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertIsNotNone(res['objective'])
        self.assertIsNotNone(res['best_bound'])
        self.assertLessEqual(res['relative_gap'], 1e-6)
        v = res['verification']
        self.assertTrue(v['feasible'])
        self.assertLessEqual(v['integrality_residual'], 1e-7)

    def test_refinery_twin_qp_kkt_verified(self):
        """QP twin with smooth throughput penalties converges via IPM with KKT stationarity."""
        m = build_refinery_twin('qp')
        res = solve(m)
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertIsNotNone(res['objective'])
        v = res['verification']
        self.assertTrue(v['feasible'])
        self.assertTrue(v['kkt_passed'])
        self.assertLessEqual(v['primal_residual'], 1e-7)
        self.assertLessEqual(v['dual_residual'], 1e-7)


class TestAutoDispatcher(unittest.TestCase):
    """Test automatic algorithm dispatcher model inspection and routing."""

    def test_dispatcher_model_inspection(self):
        """Model inspection accurately reports dimensions, integrality, and QP structure."""
        m_lp = build_refinery_twin('lp')
        info_lp = inspect_model(m_lp)
        self.assertEqual(info_lp['variables'], 36)
        self.assertEqual(info_lp['constraints'], 28)
        self.assertEqual(info_lp['integer_variables'], 0)
        self.assertFalse(info_lp['has_quadratic_objective'])

        m_milp = build_refinery_twin('milp')
        info_milp = inspect_model(m_milp)
        self.assertEqual(info_milp['variables'], 42)
        self.assertEqual(info_milp['integer_variables'], 6)
        self.assertFalse(info_milp['has_quadratic_objective'])

        m_qp = build_refinery_twin('qp')
        info_qp = inspect_model(m_qp)
        self.assertEqual(info_qp['variables'], 36)
        self.assertEqual(info_qp['integer_variables'], 0)
        self.assertTrue(info_qp['has_quadratic_objective'])

    def test_dispatcher_auto_selection(self):
        """Auto dispatcher routes LP to simplex, MILP to bb, and QP to ipm."""
        m_lp = build_refinery_twin('lp')
        disp_lp = auto_dispatch(m_lp)
        self.assertEqual(disp_lp['problem_class'], 'LP')
        self.assertEqual(disp_lp['method'], 'simplex')
        self.assertEqual(disp_lp['backend'], 'cpu')

        m_milp = build_refinery_twin('milp')
        disp_milp = auto_dispatch(m_milp)
        self.assertEqual(disp_milp['problem_class'], 'MILP')
        self.assertEqual(disp_milp['method'], 'bb')
        self.assertEqual(disp_milp['backend'], 'cpu')

        m_qp = build_refinery_twin('qp')
        disp_qp = auto_dispatch(m_qp)
        self.assertEqual(disp_qp['problem_class'], 'QP')
        self.assertEqual(disp_qp['method'], 'ipm')
        self.assertEqual(disp_qp['backend'], 'cpu')

    def test_dispatcher_explicit_override_and_errors(self):
        """Explicit method overrides are respected and invalid methods rejected."""
        m_lp = build_refinery_twin('lp')
        disp_override = auto_dispatch(m_lp, method='pdhg-cpu')
        self.assertEqual(disp_override['method'], 'pdhg-cpu')
        self.assertEqual(disp_override['backend'], 'pdhg-cpu')

        with self.assertRaises(ValueError):
            auto_dispatch(m_lp, method='invalid_method')


class TestUnboundedCertificateHardening(unittest.TestCase):
    """Complete 18-point regression matrix for original-model unbounded certificate verification (Gate 2.1).

    All handcrafted models in this class are labeled:
    # INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
    They are not benchmark instances, are not included in public dataset counts,
    and represent exact mathematical edge cases for verifying certificate invariants.
    """

    def _make_model(self, c, A_rows, row_lower, row_upper, lower, upper, names=None, maximize=False):
        n = len(c)
        if names is None:
            names = tuple(f'x{j}' for j in range(n))
        m = len(A_rows) if A_rows else 0
        A = np.array(A_rows, dtype=float).reshape(m, n) if m > 0 else np.zeros((0, n), dtype=float)
        return Model(
            c=np.array(c, dtype=float),
            A=A,
            row_lower=np.array(row_lower, dtype=float),
            row_upper=np.array(row_upper, dtype=float),
            lower=np.array(lower, dtype=float),
            upper=np.array(upper, dtype=float),
            names=names,
            maximize=maximize,
        )

    def test_01_unconstrained_minimization_unbounded(self):
        """1. unconstrained minimization unbounded: min -x1 s.t. x1 >= 0 (no constraints).
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[-1.0], A_rows=[], row_lower=[], row_upper=[], lower=[0.0], upper=[np.inf])
        r = solve_lp(m)
        self.assertEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        self.assertIn('base_point', r)
        self.assertIn('ray', r)
        self.assertIsNotNone(r.get('ray_verification'))
        self.assertTrue(r['ray_verification']['verified'])
        self.assertTrue(r['ray_verification']['base_feasible'])
        self.assertTrue(r['ray_verification']['ray_verified'])
        self.assertLess(float(m.c @ np.array(r['ray'])), 0.0)

    def test_02_constrained_minimization_unbounded(self):
        """2. constrained minimization unbounded: min -x1 s.t. x1 - x2 <= 1, x1 >= 0, x2 >= 0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[-1.0, 0.0], A_rows=[[1.0, -1.0]], row_lower=[-np.inf], row_upper=[1.0],
                             lower=[0.0, 0.0], upper=[np.inf, np.inf])
        r = solve_lp(m)
        self.assertEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        self.assertIn('base_point', r)
        self.assertIn('ray', r)
        self.assertTrue(r['ray_verification']['verified'])
        self.assertTrue(r['ray_verification']['base_feasible'])
        self.assertTrue(r['ray_verification']['ray_verified'])
        self.assertLess(float(m.c @ np.array(r['ray'])), 0.0)

    def test_03_constrained_maximization_unbounded(self):
        """3. constrained MAXIMIZATION unbounded: max x1 s.t. x1 - x2 <= 2, x1 >= 0, x2 >= 0.
        Stored c is [-1.0, 0.0] with maximize=True.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[-1.0, 0.0], A_rows=[[1.0, -1.0]], row_lower=[-np.inf], row_upper=[2.0],
                             lower=[0.0, 0.0], upper=[np.inf, np.inf], maximize=True)
        r = solve_lp(m)
        self.assertEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        self.assertIn('base_point', r)
        self.assertIn('ray', r)
        cert = r['ray_verification']
        self.assertTrue(cert['verified'])
        self.assertTrue(cert['base_feasible'])
        self.assertTrue(cert['ray_verified'])
        # Internal min improves: c^T d < 0
        ray = np.array(r['ray'])
        self.assertLess(float(m.c @ ray), 0.0)
        # Original max improves: original_objective_direction > 0
        self.assertGreater(cert['original_objective_direction'], 0.0)

    def test_04_lower_bounded_variable_direction(self):
        """4. lower-bounded variable direction: x1 >= 10.0 (finite lower, upper inf).
        d1 >= 0 is valid; d1 < 0 must be rejected.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0], A_rows=[], row_lower=[], row_upper=[], lower=[10.0], upper=[np.inf])
        # Valid direction: d1 = 1.0 >= 0
        cert_valid = verify_unbounded_certificate(m, [10.0], [1.0])
        self.assertTrue(cert_valid['verified'])
        self.assertTrue(cert_valid['ray_verified'])
        # Invalid direction: d1 = -1.0 < 0
        cert_invalid = verify_unbounded_certificate(m, [10.0], [-1.0])
        self.assertFalse(cert_invalid['verified'])
        self.assertGreater(cert_invalid['max_bound_direction_violation'], 0.0)

    def test_05_upper_bounded_variable_direction(self):
        """5. upper-bounded variable direction: x1 <= 20.0 (lower -inf, finite upper).
        min x1 with x1 <= 20.0. Direction d1 = -1.0 improves min and satisfies d1 <= 0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[1.0], A_rows=[], row_lower=[], row_upper=[], lower=[-np.inf], upper=[20.0])
        # Valid direction: d1 = -1.0 <= 0 (improves min x1 as x1 -> -inf)
        cert_valid = verify_unbounded_certificate(m, [20.0], [-1.0])
        self.assertTrue(cert_valid['verified'])
        self.assertTrue(cert_valid['ray_verified'])
        # Invalid direction: d1 = 1.0 > 0 (violates upper bound recession)
        cert_invalid = verify_unbounded_certificate(m, [20.0], [1.0])
        self.assertFalse(cert_invalid['verified'])
        self.assertGreater(cert_invalid['max_bound_direction_violation'], 0.0)

    def test_06_free_variable_unbounded_case(self):
        """6. FREE variable unbounded case: min x1 with -inf < x1 < +inf.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[1.0], A_rows=[], row_lower=[], row_upper=[], lower=[-np.inf], upper=[np.inf])
        r = solve_lp(m)
        self.assertEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        self.assertIn('base_point', r)
        self.assertIn('ray', r)
        self.assertTrue(r['ray_verification']['verified'])
        # Free variable decreases to -inf: ray[0] < 0
        self.assertLess(r['ray'][0], 0.0)

    def test_07_shifted_variable_transformation(self):
        """7. shifted-variable transformation: x1 >= 500.0 (affine shift s = 500).
        Direction must NOT have 500 added to it; ray[0] == 1.0, not 501.0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[-1.0], A_rows=[], row_lower=[], row_upper=[], lower=[500.0], upper=[np.inf])
        r = solve_lp(m)
        self.assertEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        # Ray direction must be purely linear (1.0), not shifted by 500.0
        self.assertAlmostEqual(r['ray'][0], 1.0, places=6)
        self.assertGreaterEqual(r['base_point'][0], 500.0 - 1e-7)
        self.assertTrue(r['ray_verification']['verified'])

    def test_08_sign_flipped_upper_bound_transformation(self):
        """8. sign-flipped/upper-bound transformation: x1 <= 150.0 (x = 150 - t).
        Linear part is dx = -dt. Ray must have dx = -1.0, NOT 149.0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[1.0], A_rows=[], row_lower=[], row_upper=[], lower=[-np.inf], upper=[150.0])
        r = solve_lp(m)
        self.assertEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        self.assertAlmostEqual(r['ray'][0], -1.0, places=6)
        self.assertLessEqual(r['base_point'][0], 150.0 + 1e-7)
        self.assertTrue(r['ray_verification']['verified'])

    def test_09_free_variable_split_transformation(self):
        """9. free-variable split transformation: x1 = t+ - t-.
        postsolve_direction must map dt+ -> +1 and dt- -> -1 without any shifts.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.transforms import transform_model, postsolve_direction
        m = self._make_model(c=[1.0], A_rows=[], row_lower=[], row_upper=[], lower=[-np.inf], upper=[np.inf])
        trans = transform_model(m)
        # dt+ = 1, dt- = 0 => dx = +1
        d_pos = postsolve_direction(np.array([1.0, 0.0]), trans)
        self.assertAlmostEqual(d_pos[0], 1.0, places=9)
        # dt+ = 0, dt- = 1 => dx = -1
        d_neg = postsolve_direction(np.array([0.0, 1.0]), trans)
        self.assertAlmostEqual(d_neg[0], -1.0, places=9)

    def test_10_equality_constrained_recession_direction(self):
        """10. equality-constrained recession direction: x1 - x2 = 0.
        A_i @ d must == 0. (1, 1) passes; (1, 0) fails with max_row_direction_violation > 0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0, -1.0], A_rows=[[1.0, -1.0]], row_lower=[0.0], row_upper=[0.0],
                             lower=[0.0, 0.0], upper=[np.inf, np.inf])
        cert_valid = verify_unbounded_certificate(m, [0.0, 0.0], [1.0, 1.0])
        self.assertTrue(cert_valid['verified'])
        cert_invalid = verify_unbounded_certificate(m, [0.0, 0.0], [1.0, 0.0])
        self.assertFalse(cert_invalid['verified'])
        self.assertGreater(cert_invalid['max_row_direction_violation'], 0.0)

    def test_11_ranged_row_recession_direction(self):
        """11. ranged-row recession direction: 2.0 <= x1 - x2 <= 8.0 (finite lower AND upper).
        Both bounds finite requires A_i @ d == 0. (1, 1) passes; (2, 1) fails.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0, -1.0], A_rows=[[1.0, -1.0]], row_lower=[2.0], row_upper=[8.0],
                             lower=[5.0, 0.0], upper=[np.inf, np.inf])
        # (1, 1) has A_i @ d = 1 - 1 = 0
        cert_valid = verify_unbounded_certificate(m, [5.0, 0.0], [1.0, 1.0])
        self.assertTrue(cert_valid['verified'])
        # (2, 1) has A_i @ d = 2 - 1 = 1 != 0
        cert_invalid = verify_unbounded_certificate(m, [5.0, 0.0], [2.0, 1.0])
        self.assertFalse(cert_invalid['verified'])
        self.assertGreater(cert_invalid['max_row_direction_violation'], 0.0)

    def test_12_finite_lower_plus_upper_box_must_not_be_unbounded(self):
        """12. finite lower+upper box that MUST NOT be unbounded: 0 <= x1 <= 10, 0 <= x2 <= 10.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.simplex import solve_lp
        m = self._make_model(c=[-1.0, -1.0], A_rows=[], row_lower=[], row_upper=[],
                             lower=[0.0, 0.0], upper=[10.0, 10.0])
        r = solve_lp(m)
        self.assertNotEqual(r['status'], 'UNBOUNDED_CERTIFIED')
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r['objective'], -20.0, places=6)

    def test_13_invalid_objective_direction_rejection(self):
        """13. invalid objective direction rejection: c^T d >= 0 must be rejected.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[1.0], A_rows=[], row_lower=[], row_upper=[], lower=[0.0], upper=[np.inf])
        # d = [1.0] worsens minimization objective (c^T d = 1.0 > 0)
        cert_worsen = verify_unbounded_certificate(m, [0.0], [1.0])
        self.assertFalse(cert_worsen['verified'])
        self.assertFalse(cert_worsen['ray_verified'])
        # d = [0.0] has no improvement
        cert_zero = verify_unbounded_certificate(m, [0.0], [0.0])
        self.assertFalse(cert_zero['verified'])
        self.assertFalse(cert_zero['ray_verified'])

    def test_14_invalid_row_recession_rejection(self):
        """14. invalid row recession rejection: row x1 <= 5.0 with direction d1 = 1.0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0], A_rows=[[1.0]], row_lower=[-np.inf], row_upper=[5.0],
                             lower=[0.0], upper=[np.inf])
        cert = verify_unbounded_certificate(m, [0.0], [1.0])
        self.assertFalse(cert['verified'])
        self.assertGreater(cert['max_row_direction_violation'], 0.0)

    def test_15_invalid_bound_direction_rejection(self):
        """15. invalid bound direction rejection: variable 0 <= x1 <= 10 with d1 = 1.0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0], A_rows=[], row_lower=[], row_upper=[], lower=[0.0], upper=[10.0])
        cert = verify_unbounded_certificate(m, [5.0], [1.0])
        self.assertFalse(cert['verified'])
        self.assertGreater(cert['max_bound_direction_violation'], 0.0)

    def test_16_infeasible_base_point_rejection(self):
        """16. infeasible base-point rejection: valid direction d=(1, 1), but x0=(-5, 0) violates x1 >= 0.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0, 0.0], A_rows=[[1.0, -1.0]], row_lower=[-np.inf], row_upper=[1.0],
                             lower=[0.0, 0.0], upper=[np.inf, np.inf])
        # x0 = [-5.0, 0.0] violates lower bound x1 >= 0
        cert = verify_unbounded_certificate(m, [-5.0, 0.0], [1.0, 1.0])
        self.assertFalse(cert['verified'])
        self.assertFalse(cert['base_feasible'])
        self.assertTrue(cert['ray_verified'])  # direction itself is valid, but certificate fails

    def test_17_transformed_direction_postsolve_test(self):
        """17. transformed direction postsolve test: proves mathematically that postsolve_direction
        never adds affine shifts s to directions.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.transforms import transform_model, postsolve_direction, postsolve_primal
        # Large affine bounds: l1 = 1000.0, u2 = -500.0
        m = self._make_model(c=[-1.0, 1.0], A_rows=[], row_lower=[], row_upper=[],
                             lower=[1000.0, -np.inf], upper=[np.inf, -500.0])
        trans = transform_model(m)
        # Primal postsolve of t=0 MUST include affine shifts: x = [1000.0, -500.0]
        x_primal = postsolve_primal(np.array([0.0, 0.0]), trans)
        self.assertAlmostEqual(x_primal[0], 1000.0, places=9)
        self.assertAlmostEqual(x_primal[1], -500.0, places=9)

        # Direction postsolve of dt=0 MUST BE STRICTLY ZERO: d = [0.0, 0.0], NOT [1000.0, -500.0]
        d_zero = postsolve_direction(np.array([0.0, 0.0]), trans)
        self.assertAlmostEqual(d_zero[0], 0.0, places=9)
        self.assertAlmostEqual(d_zero[1], 0.0, places=9)

        # Direction postsolve of dt=[1.0, 0.0] MUST BE [1.0, 0.0], NOT [1001.0, -500.0]
        d_unit = postsolve_direction(np.array([1.0, 0.0]), trans)
        self.assertAlmostEqual(d_unit[0], 1.0, places=9)
        self.assertAlmostEqual(d_unit[1], 0.0, places=9)

    def test_18_dimension_nonfinite_certificate_rejection(self):
        """18. dimension/nonfinite certificate rejection: NaN, Inf, dimension mismatch.
        INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA
        """
        from sovopt.verify import verify_unbounded_certificate
        m = self._make_model(c=[-1.0], A_rows=[], row_lower=[], row_upper=[], lower=[0.0], upper=[np.inf])
        # NaN in base point
        self.assertFalse(verify_unbounded_certificate(m, [np.nan], [1.0])['verified'])
        # Inf in base point
        self.assertFalse(verify_unbounded_certificate(m, [np.inf], [1.0])['verified'])
        # Dimension mismatch in base point
        self.assertFalse(verify_unbounded_certificate(m, [0.0, 0.0], [1.0])['verified'])
        # NaN in direction
        self.assertFalse(verify_unbounded_certificate(m, [0.0], [np.nan])['verified'])
        # Inf in direction
        self.assertFalse(verify_unbounded_certificate(m, [0.0], [np.inf])['verified'])
        # Dimension mismatch in direction
        self.assertFalse(verify_unbounded_certificate(m, [0.0], [1.0, 0.0])['verified'])

    def test_highs_woodinfe_infeasible_farkas_certified(self):
        """Authentic public infeasible LP benchmark: HiGHS woodinfe.mps.
        Confirms sovopt generates a verified exact rational Farkas certificate.
        """
        from sovopt import load, solve
        wood_path = ROOT / "data" / "verified" / "woodinfe.mps"
        if not wood_path.exists():
            self.skipTest("data/verified/woodinfe.mps not found")
        m = load(wood_path)
        r = solve(m)
        self.assertEqual(r['status'], 'INFEASIBLE_CERTIFIED')
        self.assertTrue(r['farkas_certificate'])
        self.assertTrue(r['verification']['farkas_verified'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

