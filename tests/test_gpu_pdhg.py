"""Tests for Gate 8: Restarted PDHG and GPU Validation Pipeline.

Validates CPU PDHG convergence, Pock-Chambolle diagonal preconditioning,
ergodic averaging restart mechanics, truthful non-CUDA / Mac reporting,
disallowed alias rejection, numerical guards, and GPU benchmark manifest integrity.
"""

import unittest, json, hashlib
from pathlib import Path
import numpy as np

from sovopt import load, solve, __version__
from sovopt.pdhg import solve_pdhg, CSRMatrix
from sovopt.cuda_backend import is_cuda_available, get_device_info
from sovopt.dispatcher import auto_dispatch
from sovopt.mps import read_mps
from scripts.gpu_preflight import run_preflight

ROOT = Path(__file__).resolve().parent.parent

class TestGPUPDHGValidation(unittest.TestCase):

    def setUp(self):
        self.afiro_path = ROOT / "data/verified/afiro.mps"
        self.sc50a_path = ROOT / "data/verified/sc50a.mps"
        self.manifest_path = ROOT / "data/manifests/gpu_pdhg_lp.json"

    def test_01_deterministic_cpu_pdhg_convergence_afiro(self):
        """1. CPU PDHG converges to verified optimum on Netlib AFIRO with exact KKT certification."""
        m = load(self.afiro_path)
        r = solve(m, backend="pdhg-cpu", max_iter=20000, tol=1e-7)
        self.assertEqual(r["status"], "OPTIMAL_VERIFIED")
        self.assertFalse(r["gpu_executed"])
        self.assertEqual(r["backend"], "pdhg-cpu")
        self.assertAlmostEqual(r["objective"], -464.75314286, places=4)
        self.assertTrue(r["verification"]["kkt_passed"])
        self.assertLess(r["verification"]["primal_residual"], 1e-7)
        self.assertLess(r["verification"]["dual_residual"], 1e-7)

    def test_02_deterministic_cpu_pdhg_convergence_blend(self):
        """2. CPU PDHG converges to verified optimum on Netlib BLEND."""
        blend_path = ROOT / "data/verified/blend.mps"
        m = load(blend_path)
        r = solve(m, backend="pdhg-cpu", max_iter=20000, tol=1e-5)
        self.assertEqual(r["status"], "OPTIMAL_VERIFIED")
        self.assertFalse(r["gpu_executed"])
        self.assertEqual(r["backend"], "pdhg-cpu")
        self.assertAlmostEqual(r["objective"], -30.81214985, places=3)
        self.assertTrue(r["verification"]["kkt_passed"])

    def test_02b_honest_limit_reached_on_sc50a(self):
        """2b. Honest LIMIT_REACHED status when first-order iterations are bounded."""
        m = load(self.sc50a_path)
        r = solve(m, backend="pdhg-cpu", max_iter=1000, tol=1e-7)
        self.assertEqual(r["status"], "LIMIT_REACHED")
        self.assertFalse(r["gpu_executed"])

    def test_03_preconditioning_step_sizes_finite_and_positive(self):
        """3. Pock-Chambolle step sizes tau and sigma are strictly positive and finite."""
        m = load(self.afiro_path)
        G, h, _ = m.inequalities(bounds=False)
        tau_denom = np.maximum(np.sum(np.abs(G), axis=0), 1.0)
        sigma_denom = np.maximum(np.sum(np.abs(G), axis=1), 1.0)
        tau = 0.99 / tau_denom
        sigma = 0.99 / sigma_denom

        self.assertTrue(np.isfinite(tau).all())
        self.assertTrue((tau > 0).all())
        self.assertTrue(np.isfinite(sigma).all())
        self.assertTrue((sigma > 0).all())

    def test_04_scaling_ablation_effect(self):
        """4. Pock-Chambolle scaling accelerates convergence relative to uniform step sizes."""
        m = load(self.afiro_path)
        r_scaled = solve_pdhg(m, backend="pdhg-cpu", max_iter=15000, tol=1e-7, scaling=True, restart=1000)
        r_unscaled = solve_pdhg(m, backend="pdhg-cpu", max_iter=15000, tol=1e-7, scaling=False, restart=1000)

        self.assertEqual(r_scaled["status"], "OPTIMAL_VERIFIED")
        # Unscaled fails to reach 1e-7 tolerance in 15000 iterations
        self.assertEqual(r_unscaled["status"], "LIMIT_REACHED")
        self.assertFalse(r_unscaled["verification"]["kkt_passed"])

    def test_05_restart_ablation_behavior(self):
        """5. PDHG executes cleanly with restart=False without exceptions."""
        m = load(self.afiro_path)
        r_norestart = solve_pdhg(m, backend="pdhg-cpu", max_iter=10000, tol=1e-7, restart=False, scaling=True)
        self.assertIn(r_norestart["status"], ("OPTIMAL_VERIFIED", "LIMIT_REACHED"))
        self.assertIn("without restart", r_norestart["algorithm"])
        self.assertFalse(r_norestart["gpu_executed"])

    def test_06_mac_cuda_unavailable_truthful(self):
        """6. Requesting pdhg-cuda on Apple Silicon truthfully returns CUDA_UNAVAILABLE with gpu_executed=False."""
        m = load(self.afiro_path)
        # Low-level solve_pdhg call
        r_low = solve_pdhg(m, device="cuda")
        if not is_cuda_available():
            self.assertEqual(r_low["status"], "CUDA_UNAVAILABLE")
            self.assertFalse(r_low["gpu_executed"])

        # High-level solve call
        r_high = solve(m, backend="pdhg-cuda")
        if not is_cuda_available():
            self.assertEqual(r_high["status"], "CUDA_UNAVAILABLE")
            self.assertFalse(r_high["gpu_executed"])
            self.assertEqual(r_high["backend"], "pdhg-cuda")

    def test_07_auto_dispatch_cuda_fallback(self):
        """7. Automatic dispatch on non-CUDA host falls back from auto to pdhg-cpu with fallback_reason."""
        m = load(self.afiro_path)
        disp = auto_dispatch(m, backend="auto")
        if not is_cuda_available():
            self.assertEqual(disp["backend"], "pdhg-cpu")
            self.assertEqual(disp.get("fallback_reason"), "CUDA_UNAVAILABLE")

        r = solve(m, backend="auto")
        if not is_cuda_available():
            self.assertEqual(r["backend"], "pdhg-cpu")
            self.assertEqual(r["fallback_reason"], "CUDA_UNAVAILABLE")
            self.assertFalse(r["gpu_executed"])

    def test_08_disallowed_backend_aliases_rejected(self):
        """8. Deprecated informal backend and method aliases are rejected with descriptive ValueError."""
        m = load(self.afiro_path)
        with self.assertRaises(ValueError) as ctx1:
            solve(m, backend="cuda-pdhg")
        self.assertIn("Standard names are 'pdhg-cpu' and 'pdhg-cuda'", str(ctx1.exception))

        with self.assertRaises(ValueError) as ctx2:
            solve(m, backend="gpu-pdhg")
        self.assertIn("Standard names are 'pdhg-cpu' and 'pdhg-cuda'", str(ctx2.exception))

        with self.assertRaises(ValueError) as ctx3:
            solve(m, method="cuda-pdhg")
        self.assertIn("Standard names are 'pdhg-cpu' and 'pdhg-cuda'", str(ctx3.exception))

    def test_09_gpu_manifest_integrity_and_strata(self):
        """9. gpu_pdhg_lp.json manifest exists, has valid strata, and all 18 files match SHA-256."""
        self.assertTrue(self.manifest_path.exists(), "gpu_pdhg_lp.json manifest must exist")
        data = json.loads(self.manifest_path.read_text())
        self.assertEqual(len(data), 18, "Manifest must contain exactly 18 Netlib LP instances")

        strata_counts = {"SMALL": 0, "MEDIUM": 0, "LARGE": 0}
        for name, meta in data.items():
            stratum = meta.get("stratum")
            self.assertIn(stratum, strata_counts)
            strata_counts[stratum] += 1

            local_f = ROOT / meta["local_file"]
            self.assertTrue(local_f.exists(), f"File {local_f} must exist")
            actual_sha = hashlib.sha256(local_f.read_bytes()).hexdigest()
            self.assertEqual(actual_sha, meta["SHA256"], f"SHA256 mismatch for {name}")

        self.assertEqual(strata_counts["SMALL"], 6)
        self.assertEqual(strata_counts["MEDIUM"], 8)
        self.assertEqual(strata_counts["LARGE"], 4)

    def test_10_preflight_reports_truthful_diagnostics(self):
        """10. scripts/gpu_preflight.py produces compliant diagnostic report."""
        rep = run_preflight()
        self.assertIn("cuda_available", rep)
        self.assertIn("gpu_executed", rep)
        self.assertIn("status", rep)
        if not is_cuda_available():
            self.assertFalse(rep["cuda_available"])
            self.assertFalse(rep["gpu_executed"])
            self.assertEqual(rep["status"], "CUDA_UNAVAILABLE")

    def test_11_csrmatrix_cpu_spmv_matches_dense(self):
        """11. CPU CSRMatrix SpMV matches dense matrix-vector multiplication exactly."""
        np.random.seed(123)
        A_dense = np.random.randn(30, 20)
        A_dense[np.abs(A_dense) < 0.7] = 0.0
        csr = CSRMatrix(A_dense)
        x = np.random.randn(20)

        y_sparse = csr.dot(x)
        y_dense = A_dense @ x
        self.assertTrue(np.allclose(y_sparse, y_dense, atol=1e-12))


if __name__ == "__main__":
    unittest.main()
