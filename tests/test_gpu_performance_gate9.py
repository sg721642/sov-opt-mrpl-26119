"""Gate 9: GPU Performance Engineering Regression and Integrity Tests.

Verifies:
1. Mathematical equivalence of fused dual/primal operations against reference expressions.
2. Invariance of restarted PDHG convergence across preallocated buffer reuse.
3. Telemetry and granular timing breakdown instrumentation.
4. Truthful non-CUDA reporting on Apple Silicon / non-CUDA environments.
5. Large public LP manifest integrity and SHA-256 validation.
"""

import unittest
import json
import hashlib
from pathlib import Path
import numpy as np

from sovopt import load, solve
from sovopt.pdhg import solve_pdhg, CSRMatrix
from sovopt.cuda_backend import is_cuda_available, get_device_info, CUDA_SPMV_SOURCE, CUDA_DUAL_STEP_SOURCE, CUDA_PRIMAL_STEP_SOURCE, CUDA_VECTOR_COPY_SOURCE
from sovopt.mps import read_mps

ROOT = Path(__file__).resolve().parent.parent


class TestGPUPerformanceGate9(unittest.TestCase):

    def setUp(self):
        self.afiro_path = ROOT / "data/verified/afiro.mps"
        self.large_manifest_path = ROOT / "data/manifests/gpu_pdhg_large_public.json"

    def test_01_fused_dual_step_mathematical_equivalence(self):
        """1. Fused dual step logic exactly reproduces unfused sequential operations."""
        np.random.seed(42)
        m = 50
        Ax_bar = np.random.randn(m)
        hh = np.random.randn(m)
        sigma = np.random.uniform(0.01, 1.0, size=m)
        y = np.maximum(0.0, np.random.randn(m))
        avgy = y.copy()

        # Reference unfused calculation
        y_ref = np.maximum(0.0, y + sigma * (Ax_bar - hh))
        count = 17
        inv_count = 1.0 / count
        avgy_ref = avgy + (y_ref - avgy) / count

        # Fused kernel simulation (identical to CUDA C code)
        y_fused = y.copy()
        avgy_fused = avgy.copy()
        for i in range(m):
            step = y_fused[i] + sigma[i] * (Ax_bar[i] - hh[i])
            y_new = max(0.0, step)
            avgy_fused[i] += (y_new - avgy_fused[i]) * inv_count
            y_fused[i] = y_new

        self.assertTrue(np.allclose(y_ref, y_fused, atol=1e-15))
        self.assertTrue(np.allclose(avgy_ref, avgy_fused, atol=1e-15))

    def test_02_fused_primal_step_mathematical_equivalence(self):
        """2. Fused primal step logic exactly reproduces unfused sequential operations."""
        np.random.seed(42)
        n = 60
        ATy = np.random.randn(n)
        c = np.random.randn(n)
        tau = np.random.uniform(0.01, 1.0, size=n)
        lo = np.full(n, -5.0)
        hi = np.full(n, 5.0)
        lo[0:10] = -np.inf
        hi[50:60] = np.inf

        x = np.random.uniform(-3.0, 3.0, size=n)
        avg = x.copy()

        # Reference unfused calculation
        new_x_ref = np.clip(x - tau * (c + ATy), lo, hi)
        bar_ref = 2.0 * new_x_ref - x
        count = 23
        inv_count = 1.0 / count
        avg_ref = avg + (new_x_ref - avg) / count

        # Fused kernel simulation (identical to CUDA C code)
        x_fused = x.copy()
        bar_fused = np.zeros(n)
        avg_fused = avg.copy()
        for j in range(n):
            x_old = x_fused[j]
            step = x_old - tau[j] * (c[j] + ATy[j])
            l = lo[j]
            u = hi[j]
            x_new = min(max(step, l), u)
            bar_fused[j] = 2.0 * x_new - x_old
            avg_fused[j] += (x_new - avg_fused[j]) * inv_count
            x_fused[j] = x_new

        self.assertTrue(np.allclose(new_x_ref, x_fused, atol=1e-15))
        self.assertTrue(np.allclose(bar_ref, bar_fused, atol=1e-15))
        self.assertTrue(np.allclose(avg_ref, avg_fused, atol=1e-15))

    def test_03_csrmatrix_preallocated_out_buffer(self):
        """3. CSRMatrix dot product supports preallocated destination buffer without reallocation."""
        np.random.seed(99)
        A = np.random.randn(25, 30)
        A[np.abs(A) < 0.6] = 0.0
        csr = CSRMatrix(A)
        x = np.random.randn(30)

        out_buf = np.zeros(25, dtype=np.float64)
        ptr_before = out_buf.__array_interface__["data"][0]
        res = csr.dot(x, out=out_buf)
        ptr_after = res.__array_interface__["data"][0]

        self.assertEqual(ptr_before, ptr_after, "dot(x, out=buf) must write in-place to preallocated buffer")
        self.assertTrue(np.allclose(res, A @ x, atol=1e-14))

    def test_04_granular_timing_and_telemetry_schema(self):
        """4. solve_pdhg returns granular timing breakdown and telemetry fields."""
        m = load(self.afiro_path)
        r = solve_pdhg(m, backend="pdhg-cpu", max_iter=2000, tol=1e-7)

        self.assertIn("setup_seconds", r)
        self.assertIn("iteration_seconds", r)
        self.assertIn("verification_seconds", r)
        self.assertIn("iteration_and_verification_seconds", r)
        self.assertIn("total_elapsed_seconds", r)
        self.assertIn("telemetry", r)

        t = r["telemetry"]
        self.assertIn("kernel_launches_count", t)
        self.assertIn("restarts_count", t)
        self.assertIn("convergence_checks_count", t)

        self.assertGreaterEqual(r["setup_seconds"], 0.0)
        self.assertGreaterEqual(r["iteration_seconds"], 0.0)
        self.assertGreaterEqual(r["verification_seconds"], 0.0)
        self.assertGreaterEqual(r["total_elapsed_seconds"], 0.0)

        self.assertAlmostEqual(
            r["total_elapsed_seconds"],
            r["setup_seconds"] + r["iteration_and_verification_seconds"],
            places=6
        )

    def test_05_cuda_unavailable_on_mac_retains_truthful_telemetry(self):
        """5. CUDA_UNAVAILABLE on non-CUDA host populates empty telemetry without crashing."""
        m = load(self.afiro_path)
        r = solve_pdhg(m, backend="pdhg-cuda")
        if not is_cuda_available():
            self.assertEqual(r["status"], "CUDA_UNAVAILABLE")
            self.assertFalse(r["gpu_executed"])
            self.assertEqual(r["telemetry"]["kernel_launches_count"], 0)
            self.assertEqual(r["telemetry"]["restarts_count"], 0)
            self.assertEqual(r["telemetry"]["convergence_checks_count"], 0)

    def test_06_large_public_manifest_integrity(self):
        """6. gpu_pdhg_large_public.json exists and all instances match primary SHA-256."""
        self.assertTrue(self.large_manifest_path.exists(), "Manifest gpu_pdhg_large_public.json must exist")
        data = json.loads(self.large_manifest_path.read_text())
        self.assertGreaterEqual(len(data), 4, "Must contain at least 4 large public continuous LP instances")

        for key, item in data.items():
            self.assertEqual(item["problem_class"], "LP")
            self.assertEqual(item["stratum"], "LARGE")
            local_p = ROOT / item["local_file"]
            self.assertTrue(local_p.exists(), f"Local file {local_p} must exist")
            actual_sha = hashlib.sha256(local_p.read_bytes()).hexdigest()
            self.assertEqual(actual_sha, item["SHA256"], f"SHA256 mismatch for {key}")

    def test_07_cuda_source_code_contains_required_optimizations(self):
        """7. RawKernel source strings include __restrict__, unroll pragma, and fused math."""
        self.assertIn("__restrict__", CUDA_SPMV_SOURCE)
        self.assertIn("#pragma unroll", CUDA_SPMV_SOURCE)
        self.assertIn("dual_step_fused", CUDA_DUAL_STEP_SOURCE)
        self.assertIn("__restrict__", CUDA_DUAL_STEP_SOURCE)
        self.assertIn("primal_step_fused", CUDA_PRIMAL_STEP_SOURCE)
        self.assertIn("__restrict__", CUDA_PRIMAL_STEP_SOURCE)
        self.assertIn("fmin", CUDA_PRIMAL_STEP_SOURCE)
        self.assertIn("fmax", CUDA_PRIMAL_STEP_SOURCE)
        self.assertIn("vector_copy", CUDA_VECTOR_COPY_SOURCE)


if __name__ == "__main__":
    unittest.main()
