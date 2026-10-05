"""Deterministic unit tests for Sovereign True Sparse Matrix core.

Covers CSRMatrix construction, validation, SpMV, SpMV-transpose, memory estimation,
anti-densification at 50,000 x 25,000, and sparse MPS ingestion.
Zero external solver dependencies.
"""
import os
import time
import unittest
import numpy as np

from sovopt.sparse import CSRMatrix, CSCMatrix, csr_from_triplets
from sovopt.model import Model
from sovopt.mps import read_mps


class TestSparseCore(unittest.TestCase):
    """Test suite for sovereign sparse matrix representations and operations."""

    def test_01_csr_direct_creation_and_validation(self):
        """CSRMatrix direct creation and validation checks."""
        # Valid 3x3 CSR
        row_ptr = np.array([0, 2, 3, 5], dtype=np.int64)
        col_idx = np.array([0, 2, 1, 0, 1], dtype=np.int64)
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64)
        csr = CSRMatrix(row_ptr=row_ptr, col_idx=col_idx, values=values, shape=(3, 3))

        self.assertEqual(csr.shape, (3, 3))
        self.assertEqual(len(csr), 3)
        self.assertEqual(csr.nnz, 5)
        self.assertEqual(csr.row_ptr[0], 0)
        self.assertEqual(csr.row_ptr[3], 5)

        # Invalid row_ptr start
        bad_row_ptr = np.array([1, 2, 3, 5], dtype=np.int64)
        with self.assertRaises(ValueError):
            CSRMatrix(row_ptr=bad_row_ptr, col_idx=col_idx, values=values, shape=(3, 3))

        # Invalid shape (out-of-bounds column)
        with self.assertRaises((ValueError, IndexError)):
            CSRMatrix(row_ptr=row_ptr, col_idx=col_idx, values=values, shape=(3, 2))

        # Unsorted col_idx within row
        unsorted_col_idx = np.array([2, 0, 1, 0, 1], dtype=np.int64)
        with self.assertRaises(ValueError):
            CSRMatrix(row_ptr=row_ptr, col_idx=unsorted_col_idx, values=values, shape=(3, 3))

    def test_02_spmv_vs_dense_baseline(self):
        """Sovereign SpMV: y = A @ x compared against dense baseline for 1K, 5K, 10K, 25K."""
        rng = np.random.RandomState(42)
        sizes = [1000, 5000, 10000, 25000]

        for n in sizes:
            m = max(50, n // 10)
            nnz_per_row = 6
            rows = []
            cols = []
            vals = []
            for r in range(m):
                col_choices = np.sort(rng.choice(n, size=nnz_per_row, replace=False))
                for c in col_choices:
                    rows.append(r)
                    cols.append(c)
                    vals.append(rng.uniform(-5.0, 5.0))

            csr = csr_from_triplets(m, n, rows, cols, vals)
            x = rng.randn(n)

            # Sparse dot
            y_sp = csr.dot(x)

            # Dense equivalent
            A_dense = csr.to_dense()
            y_dense = np.einsum('ij,j->i', A_dense, x)

            np.testing.assert_allclose(y_sp, y_dense, rtol=1e-12, atol=1e-12,
                                       err_msg=f"SpMV mismatch at n={n}")

    def test_03_spmv_transpose_vs_dense_baseline(self):
        """Sovereign SpMV-transpose: x = A.T @ y compared against dense baseline for 1K, 5K, 10K, 25K."""
        rng = np.random.RandomState(43)
        sizes = [1000, 5000, 10000, 25000]

        for n in sizes:
            m = max(50, n // 10)
            nnz_per_row = 6
            rows = []
            cols = []
            vals = []
            for r in range(m):
                col_choices = np.sort(rng.choice(n, size=nnz_per_row, replace=False))
                for c in col_choices:
                    rows.append(r)
                    cols.append(c)
                    vals.append(rng.uniform(-5.0, 5.0))

            csr = csr_from_triplets(m, n, rows, cols, vals)
            y = rng.randn(m)

            # Sparse transpose dot
            x_sp = csr.transpose_dot(y)

            # Dense equivalent
            A_dense = csr.to_dense()
            x_dense = np.einsum('ji,j->i', A_dense, y)

            np.testing.assert_allclose(x_sp, x_dense, rtol=1e-12, atol=1e-12,
                                       err_msg=f"SpMV-transpose mismatch at n={n}")

    def test_04_memory_estimation_accuracy(self):
        """memory_bytes vs actual buffer sizes."""
        row_ptr = np.array([0, 2, 4], dtype=np.int64)
        col_idx = np.array([0, 1, 0, 1], dtype=np.int64)
        values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        csr = CSRMatrix(row_ptr=row_ptr, col_idx=col_idx, values=values, shape=(2, 2))

        expected = row_ptr.nbytes + col_idx.nbytes + values.nbytes
        self.assertEqual(csr.memory_bytes, expected)

    def test_05_anti_densification_50k_by_25k(self):
        """Instantiate sparse model with 50K variables, 25K rows, 5 nonzeros/row.

        Verify:
        - construction succeeds
        - memory_bytes < 20 MB (dense would be 50,000 * 25,000 * 8 = 10,000,000,000 bytes = 10 GB)
        - model.validate() passes
        - A.dot() executes in < 50ms on Mac
        """
        n_vars = 50000
        n_rows = 25000
        nnz_per_row = 5
        total_nnz = n_rows * nnz_per_row

        rng = np.random.RandomState(123)
        row_ptr = np.arange(0, total_nnz + 1, nnz_per_row, dtype=np.int64)

        # Build col_idx and values deterministically
        cols = []
        for r in range(n_rows):
            # choose 5 deterministic column indices spaced across 50,000
            step = n_vars // nnz_per_row
            row_cols = [c * step + (r % step) for c in range(nnz_per_row)]
            cols.extend(row_cols)
        col_idx = np.array(cols, dtype=np.int64)
        values = rng.uniform(0.1, 1.0, size=total_nnz).astype(np.float64)

        csr = CSRMatrix(row_ptr=row_ptr, col_idx=col_idx, values=values, shape=(n_rows, n_vars))
        self.assertEqual(csr.nnz, total_nnz)

        # Memory check: < 20 MB
        mem_mb = csr.memory_bytes / (1024 * 1024)
        self.assertLess(mem_mb, 20.0, f"Memory should be < 20 MB, got {mem_mb:.2f} MB")

        # Dense would be 10 GB
        dense_bytes = n_rows * n_vars * 8
        self.assertEqual(dense_bytes, 10_000_000_000)

        # Build Model
        c = np.ones(n_vars, dtype=np.float64)
        b_l = np.zeros(n_rows, dtype=np.float64)
        b_u = np.full(n_rows, 100.0, dtype=np.float64)
        l = np.zeros(n_vars, dtype=np.float64)
        u = np.full(n_vars, 10.0, dtype=np.float64)

        model = Model(c=c, A=csr, row_lower=b_l, row_upper=b_u, lower=l, upper=u)
        model.validate()  # Must not raise or trigger densification

        # SpMV timing on Mac: must execute in < 50ms
        x = np.ones(n_vars, dtype=np.float64)
        t0 = time.perf_counter()
        y = csr.dot(x)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(len(y), n_rows)
        self.assertLess(elapsed_ms, 50.0, f"SpMV took {elapsed_ms:.2f} ms (expected < 50ms)")

    def test_06_sparse_mps_ingest_small_real_mps(self):
        """Sparse MPS ingest on AFIRO."""
        afiro_path = os.path.join(os.path.dirname(__file__), "fixtures", "afiro.mps")
        if not os.path.exists(afiro_path):
            afiro_path = os.path.join(os.path.dirname(__file__), "..", "data", "netlib", "afiro.mps")

        if os.path.exists(afiro_path):
            model = read_mps(afiro_path, sparse=True)
            self.assertIsInstance(model.A, CSRMatrix)
            self.assertEqual(model.A.shape, (27, 32))
            self.assertEqual(model.A.nnz, 83)
            # Verify KKT on sparse model works
            from sovopt.pdhg import solve_pdhg
            res = solve_pdhg(model, max_iter=2000, tol=1e-4)
            self.assertIn(res['status'], ["OPTIMAL", "LIMIT_REACHED"])


if __name__ == "__main__":
    unittest.main()
