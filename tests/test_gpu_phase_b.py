"""Gate 8 Phase B Regression Tests: CUDA Preflight Correctness and GPU Sparse Backend.

Tests:
- Correct CSR construction in preflight (sorted row order)
- CUDA unavailable semantics (CUDA_UNAVAILABLE status)
- CUDA sparse failure semantics (CUDA_SPMV_FAILED status)
- CUDA ready semantics (NVIDIA_CUDA_READY status)
- Custom GPU CSR A*x correctness against NumPy reference
- A^T sparse correctness (used in PDHG dual step)
- FP64 result correctness
- Deterministic result behavior
- gpu_executed truthfulness

CUDA hardware-specific tests skip cleanly on non-CUDA hosts.
Non-CUDA import behavior is preserved.
"""

import unittest
import numpy as np
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sovopt.cuda_backend import is_cuda_available, get_device_info
from scripts.gpu_preflight import run_preflight


CUDA_AVAILABLE = is_cuda_available()


class TestPreflightCSRConstruction(unittest.TestCase):
    """Verify that preflight builds CSR correctly by sorting COO entries by row."""

    def test_sorted_coo_csr_correctness(self):
        """CSR row pointer built from row-sorted COO must yield correct SpMV."""
        # Hand-checkable 3x4 CSR matrix in row-random COO order
        # Row 0: col 1 = 2.0, col 3 = 4.0
        # Row 1: col 0 = 5.0
        # Row 2: col 2 = 3.0, col 3 = 1.0
        r_coo = np.array([2, 0, 1, 0, 2], dtype=np.int32)  # intentionally out of order
        j_coo = np.array([2, 1, 0, 3, 3], dtype=np.int32)
        a_coo = np.array([3.0, 2.0, 5.0, 4.0, 1.0], dtype=np.float64)

        # Dense reference
        A_dense = np.zeros((3, 4), dtype=np.float64)
        for ri, ci, ai in zip(r_coo, j_coo, a_coo):
            A_dense[ri, ci] = ai
        x = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        y_ref = A_dense @ x  # [2*2+4*4, 5*1, 3*3+1*4] = [20, 5, 13]

        # Sort COO by row (the fix)
        order = np.argsort(r_coo, kind="stable")
        r_s = r_coo[order]
        j_s = j_coo[order]
        a_s = a_coo[order]

        # Build CSR row pointer from sorted row indices
        m = 3
        p = np.r_[0, np.cumsum(np.bincount(r_s, minlength=m))].astype(np.int32)

        # Manual CSR SpMV
        y_csr = np.zeros(m, dtype=np.float64)
        for row in range(m):
            for k in range(p[row], p[row + 1]):
                y_csr[row] += a_s[k] * x[j_s[k]]

        np.testing.assert_allclose(y_csr, y_ref, atol=1e-14,
                                   err_msg="Sorted-COO CSR SpMV must match dense reference")

    def test_unsorted_coo_wrong_csr_pointer(self):
        """Without sorting, CSR row pointer on random-order COO gives wrong results for non-trivial cases."""
        np.random.seed(777)
        m, n, nnz = 20, 20, 60
        r = np.random.randint(0, m, nnz).astype(np.int32)
        j = np.random.randint(0, n, nnz).astype(np.int32)
        a = np.random.randn(nnz).astype(np.float64)
        x = np.random.randn(n).astype(np.float64)

        # Reference via dense
        A_dense = np.zeros((m, n), dtype=np.float64)
        np.add.at(A_dense, (r, j), a)
        y_ref = A_dense @ x

        # WRONG: build CSR row pointer without sorting first
        p_wrong = np.r_[0, np.cumsum(np.bincount(r, minlength=m))].astype(np.int32)
        y_wrong = np.zeros(m, dtype=np.float64)
        for row in range(m):
            for k in range(p_wrong[row], p_wrong[row + 1]):
                y_wrong[row] += a[k] * x[j[k]]

        # CORRECT: sort first, then build CSR pointer
        order = np.argsort(r, kind="stable")
        r_s = r[order]
        j_s = j[order]
        a_s = a[order]
        p_correct = np.r_[0, np.cumsum(np.bincount(r_s, minlength=m))].astype(np.int32)
        y_correct = np.zeros(m, dtype=np.float64)
        for row in range(m):
            for k in range(p_correct[row], p_correct[row + 1]):
                y_correct[row] += a_s[k] * x[j_s[k]]

        np.testing.assert_allclose(y_correct, y_ref, atol=1e-13,
                                   err_msg="Sorted CSR must match dense reference")
        # Verify the wrong approach doesn't match (it typically won't)
        # This is just documentation; we don't assert it's always wrong
        max_err_wrong = float(np.max(np.abs(y_wrong - y_ref)))
        max_err_correct = float(np.max(np.abs(y_correct - y_ref)))
        self.assertLess(max_err_correct, 1e-13,
                        "Correctly sorted CSR SpMV error must be < 1e-13")


class TestPreflightStatusSemantics(unittest.TestCase):
    """Verify preflight produces correct three-state status semantics."""

    def test_preflight_has_required_keys(self):
        """Preflight report must contain all required keys regardless of CUDA availability."""
        rep = run_preflight()
        required_keys = ["timestamp_utc", "status", "cuda_available", "gpu_executed",
                         "device_info", "machine_metadata", "micro_spmv_test", "elapsed_seconds"]
        for key in required_keys:
            self.assertIn(key, rep, f"Preflight report missing required key: {key}")

    def test_status_values_are_valid_three_states(self):
        """Preflight status must be one of the three declared states."""
        rep = run_preflight()
        valid_states = {"CUDA_UNAVAILABLE", "CUDA_SPMV_FAILED", "NVIDIA_CUDA_READY"}
        self.assertIn(rep["status"], valid_states,
                      f"Status '{rep['status']}' is not one of {valid_states}")

    def test_no_cuda_unavailable_if_device_present_and_test_passes(self):
        """If CUDA is present and SpMV passes, status must be NVIDIA_CUDA_READY."""
        rep = run_preflight()
        if rep["cuda_available"] and rep.get("micro_spmv_test", {}).get("passed"):
            self.assertEqual(rep["status"], "NVIDIA_CUDA_READY",
                             "CUDA present + SpMV passed => must be NVIDIA_CUDA_READY, not CUDA_UNAVAILABLE")

    def test_cuda_unavailable_semantics_if_no_device(self):
        """On a host without CUDA, all three fields must reflect unavailability."""
        rep = run_preflight()
        if not CUDA_AVAILABLE:
            self.assertFalse(rep["cuda_available"])
            self.assertFalse(rep["gpu_executed"])
            self.assertEqual(rep["status"], "CUDA_UNAVAILABLE")
            self.assertIsNone(rep["micro_spmv_test"])

    def test_gpu_executed_truthfulness(self):
        """gpu_executed must be False if no CUDA is present."""
        rep = run_preflight()
        if not CUDA_AVAILABLE:
            self.assertFalse(rep["gpu_executed"],
                             "gpu_executed must be False when CUDA is unavailable")

    def test_cuda_spmv_failed_requires_cuda_present(self):
        """CUDA_SPMV_FAILED status may only appear when cuda_available=True."""
        rep = run_preflight()
        if rep["status"] == "CUDA_SPMV_FAILED":
            self.assertTrue(rep["cuda_available"],
                            "CUDA_SPMV_FAILED must only appear when cuda_available=True")


@unittest.skipUnless(CUDA_AVAILABLE, "CUDA hardware not present; skipping GPU SpMV tests")
class TestCUDACSRSpMVCorrectness(unittest.TestCase):
    """Verify custom RawKernel CSR SpMV correctness against NumPy reference (CUDA only)."""

    @classmethod
    def setUpClass(cls):
        from sovopt.cuda_backend import CUDABackend
        cls.backend = CUDABackend()

    def _run_spmv(self, A_dense):
        """Build CUDACSR from dense matrix, compute SpMV, return (y_gpu, y_ref)."""
        m, n = A_dense.shape
        r, j = np.nonzero(A_dense)
        a = A_dense[r, j].astype(np.float64)
        # Sort by row
        order = np.argsort(r, kind="stable")
        r = r[order].astype(np.int32)
        j = j[order].astype(np.int32)
        a = a[order]
        p = np.r_[0, np.cumsum(np.bincount(r, minlength=m))].astype(np.int32)

        x = np.random.randn(n).astype(np.float64)
        csr = self.backend.build_csr(p, j, a, (m, n))
        x_dev = self.backend.asarray(x)
        self.backend.synchronize()
        out = csr.dot(x_dev)
        self.backend.synchronize()
        y_gpu = self.backend.to_cpu(out)
        y_ref = A_dense @ x
        return y_gpu, y_ref

    def test_hand_checkable_small_csr(self):
        """Small hand-checkable 3x4 CSR matrix: y = A*x must match reference."""
        A = np.array([[0., 2., 0., 4.],
                      [5., 0., 0., 0.],
                      [0., 0., 3., 1.]], dtype=np.float64)
        y_gpu, y_ref = self._run_spmv(A)
        np.testing.assert_allclose(y_gpu, y_ref, atol=1e-13,
                                   err_msg="Hand-checkable GPU SpMV mismatch")

    def test_random_sparse_rectangular_matrix(self):
        """Random sparse 50x30 matrix: GPU SpMV must match NumPy reference within FP64 tolerance."""
        np.random.seed(101)
        A = np.random.randn(50, 30)
        A[np.abs(A) < 0.5] = 0.0
        y_gpu, y_ref = self._run_spmv(A)
        np.testing.assert_allclose(y_gpu, y_ref, atol=1e-12,
                                   err_msg="Random sparse rectangular GPU SpMV mismatch")

    def test_deterministic_sparse_matrix(self):
        """Deterministic sparse matrix (fixed seed): GPU SpMV result must be reproducible."""
        np.random.seed(42)
        A = np.random.randn(40, 25)
        A[np.abs(A) < 0.6] = 0.0

        x_fixed = np.random.randn(25).astype(np.float64)
        r, j = np.nonzero(A)
        a = A[r, j].astype(np.float64)
        order = np.argsort(r, kind="stable")
        r = r[order].astype(np.int32)
        j = j[order].astype(np.int32)
        a = a[order]
        m, n = A.shape
        p = np.r_[0, np.cumsum(np.bincount(r, minlength=m))].astype(np.int32)

        csr = self.backend.build_csr(p, j, a, (m, n))
        x_dev = self.backend.asarray(x_fixed)

        self.backend.synchronize()
        out1 = csr.dot(x_dev)
        self.backend.synchronize()
        out2 = csr.dot(x_dev)
        self.backend.synchronize()

        y1 = self.backend.to_cpu(out1)
        y2 = self.backend.to_cpu(out2)
        y_ref = A @ x_fixed

        np.testing.assert_allclose(y1, y_ref, atol=1e-12,
                                   err_msg="First GPU SpMV run mismatch vs NumPy reference")
        np.testing.assert_array_equal(y1, y2,
                                      err_msg="GPU SpMV must be deterministic across repeated calls")

    def test_non_square_matrix(self):
        """Non-square 20x80 sparse matrix: GPU SpMV must match NumPy reference."""
        np.random.seed(200)
        A = np.random.randn(20, 80)
        A[np.abs(A) < 0.8] = 0.0
        y_gpu, y_ref = self._run_spmv(A)
        np.testing.assert_allclose(y_gpu, y_ref, atol=1e-12,
                                   err_msg="Non-square GPU SpMV mismatch")

    def test_different_sparsity_patterns(self):
        """Dense diagonal vs dense anti-diagonal patterns."""
        n = 50
        # Dense diagonal
        A_diag = np.diag(np.arange(1.0, n + 1))
        y_gpu, y_ref = self._run_spmv(A_diag)
        np.testing.assert_allclose(y_gpu, y_ref, atol=1e-13,
                                   err_msg="Diagonal GPU SpMV mismatch")

        # Random striped pattern
        np.random.seed(300)
        A_stripe = np.zeros((30, 40))
        for i in range(30):
            for j in range(5):
                c = (i * 7 + j * 3) % 40
                A_stripe[i, c] = float(i + j + 1)
        y_gpu2, y_ref2 = self._run_spmv(A_stripe)
        np.testing.assert_allclose(y_gpu2, y_ref2, atol=1e-13,
                                   err_msg="Striped pattern GPU SpMV mismatch")

    def test_fp64_precision(self):
        """FP64 precision: GPU SpMV on numerically sensitive matrix must stay within double precision."""
        np.random.seed(999)
        A = np.random.randn(30, 30) * 1e6
        A[np.abs(A) < 1e5] = 0.0
        y_gpu, y_ref = self._run_spmv(A)
        # Check relative tolerance appropriate for large values
        max_rel_err = np.max(np.abs(y_gpu - y_ref) / (np.abs(y_ref) + 1e-100))
        self.assertLess(float(max_rel_err), 1e-10,
                        f"FP64 relative error {max_rel_err:.2e} exceeds 1e-10")

    def test_gpu_executed_true_after_spmv(self):
        """After a real CUDABackend SpMV, gpu_executed must be True in a PDHG solve on CUDA."""
        from sovopt.pdhg import solve_pdhg
        from sovopt.mps import read_mps
        afiro_path = ROOT / "data/verified/afiro.mps"
        if not afiro_path.exists():
            self.skipTest("afiro.mps not available")
        m = read_mps(afiro_path)
        res = solve_pdhg(m, backend="pdhg-cuda", max_iter=5000, tol=1e-7)
        self.assertTrue(res.get("gpu_executed"), "gpu_executed must be True for pdhg-cuda on CUDA hardware")


@unittest.skipUnless(CUDA_AVAILABLE, "CUDA hardware not present; skipping GPU transpose tests")
class TestCUDACSRTransposeCorrectness(unittest.TestCase):
    """Verify A^T sparse operation correctness (used in PDHG dual step AT.dot(y))."""

    @classmethod
    def setUpClass(cls):
        from sovopt.cuda_backend import CUDABackend
        cls.backend = CUDABackend()

    def _build_cuda_csr(self, A_dense):
        """Build CUDACSR object from dense matrix."""
        m, n = A_dense.shape
        r, j = np.nonzero(A_dense)
        a = A_dense[r, j].astype(np.float64)
        order = np.argsort(r, kind="stable")
        r = r[order].astype(np.int32)
        j = j[order].astype(np.int32)
        a = a[order]
        p = np.r_[0, np.cumsum(np.bincount(r, minlength=m))].astype(np.int32)
        return self.backend.build_csr(p, j, a, (m, n))

    def test_transpose_spmv_matches_reference(self):
        """A^T * y must match NumPy reference for several random matrices."""
        for seed in [42, 123, 456]:
            np.random.seed(seed)
            G = np.random.randn(30, 20)
            G[np.abs(G) < 0.5] = 0.0

            GT_dense = G.T  # 20x30
            AT_csr = self._build_cuda_csr(GT_dense)

            y = np.random.randn(30).astype(np.float64)
            y_dev = self.backend.asarray(y)
            self.backend.synchronize()
            out = AT_csr.dot(y_dev)
            self.backend.synchronize()
            y_gpu = self.backend.to_cpu(out)
            y_ref = GT_dense @ y  # equivalent to G.T @ y

            np.testing.assert_allclose(
                y_gpu, y_ref, atol=1e-12,
                err_msg=f"A^T SpMV mismatch at seed={seed}")

    def test_transpose_fp64_correctness(self):
        """A^T * y must maintain FP64 precision for moderately large values."""
        np.random.seed(777)
        G = np.random.randn(50, 40) * 100.0
        G[np.abs(G) < 10.0] = 0.0
        GT_dense = G.T
        AT_csr = self._build_cuda_csr(GT_dense)

        y = np.random.randn(50).astype(np.float64) * 1000.0
        y_dev = self.backend.asarray(y)
        self.backend.synchronize()
        out = AT_csr.dot(y_dev)
        self.backend.synchronize()
        y_gpu = self.backend.to_cpu(out)
        y_ref = G.T @ y

        np.testing.assert_allclose(y_gpu, y_ref, rtol=1e-10,
                                   err_msg="A^T FP64 precision mismatch")


@unittest.skipUnless(CUDA_AVAILABLE, "CUDA hardware not present; skipping CUDA preflight integration test")
class TestPreflightCUDAIntegration(unittest.TestCase):
    """Integration test: physical CUDA preflight must pass all criteria."""

    def test_preflight_nvidia_cuda_ready_on_cuda_host(self):
        """On a CUDA-capable host, preflight must report NVIDIA_CUDA_READY."""
        rep = run_preflight()
        self.assertTrue(rep["cuda_available"], "CUDA device must be detected")
        self.assertTrue(rep["gpu_executed"], "gpu_executed must be True after real CUDA operation")
        self.assertEqual(rep["status"], "NVIDIA_CUDA_READY",
                         f"Expected NVIDIA_CUDA_READY, got {rep['status']}; "
                         f"micro_spmv_test={rep.get('micro_spmv_test')}")
        mt = rep["micro_spmv_test"]
        self.assertIsNotNone(mt, "micro_spmv_test must not be None on CUDA host")
        self.assertTrue(mt["passed"],
                        f"Micro SpMV test must pass; max_discrepancy={mt.get('max_discrepancy')}")
        self.assertLess(mt["max_discrepancy"], 1e-12,
                        f"SpMV discrepancy {mt['max_discrepancy']:.2e} must be < 1e-12")

    def test_preflight_device_name_rtx5050(self):
        """Preflight device info must identify an NVIDIA GPU on CUDA host."""
        rep = run_preflight()
        if rep["cuda_available"]:
            dev_name = rep["device_info"].get("device_name", "")
            self.assertIn("NVIDIA", dev_name,
                          f"Expected NVIDIA GPU name, got '{dev_name}'")
            self.assertIsNotNone(rep["device_info"].get("compute_capability"))
            self.assertIsNotNone(rep["device_info"].get("total_memory_bytes"))


if __name__ == "__main__":
    unittest.main()
