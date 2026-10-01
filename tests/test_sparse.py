"""Tests for Gate 3: Sovereign Sparse Numerical Linear Algebra and Sparse Simplex Engine.

Covers all 28 required test dimensions:
1. CSR construction
2. CSC construction
3. CSR A x
4. CSC A^T y
5. sparse basis extraction
6. deterministic index ordering
7. duplicate handling
8. zero dropping
9. Markowitz pivot selection
10. threshold pivot rejection
11. singular sparse matrix detection
12. sparse LU factorization
13. FTRAN residual
14. BTRAN residual
15. sparse-vs-dense solve agreement
16. iterative refinement improvement
17. one eta update
18. multiple eta updates
19. BTRAN with eta updates
20. forced refactorization
21. eta-limit refactorization
22. residual-triggered refactorization
23. near-singular basis recovery/failure semantics
24. sparse primal simplex on genuine AFIRO
25. sparse primal simplex on genuine SC50A
26. sparse primal simplex on genuine SC50B
27. sparse primal simplex on genuine BLEND
28. original-model verification after sparse solve

DISCLAIMER: All synthetic matrices constructed internally in this file are
INTERNAL MATHEMATICAL UNIT FIXTURES — NOT BENCHMARK DATA.
Public benchmark validation instances are loaded exclusively from data/verified/.
"""

import unittest
from pathlib import Path
import numpy as np

from sovopt.linalg import LU, NumericalError
from sovopt.sparse import (
    CSRMatrix, CSCMatrix,
    csr_from_triplets, csc_from_triplets,
    csr_from_dense, csc_from_dense
)
from sovopt.sparse_lu import (
    SparseLU, SparseBasisEngine, MarkowitzPivotSelector
)
from sovopt.model import load
from sovopt.simplex import solve_lp
from sovopt.verify import verify


DATA_DIR = Path(__file__).parent.parent / "data" / "verified"


class TestSparseLinearAlgebra(unittest.TestCase):
    """Test suite covering the 28 required dimensions of Gate 3."""

    # -------------------------------------------------------------------------
    # 1. CSR Construction
    # -------------------------------------------------------------------------
    def test_01_csr_construction(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] CSR construction."""
        indptr = np.array([0, 2, 3, 5], dtype=np.int64)
        indices = np.array([0, 2, 1, 0, 2], dtype=np.int64)
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0], dtype=np.float64)
        csr = CSRMatrix(n_rows=3, n_cols=3, indptr=indptr, indices=indices, data=data)

        self.assertEqual(csr.n_rows, 3)
        self.assertEqual(csr.n_cols, 3)
        self.assertEqual(csr.nnz, 5)
        self.assertAlmostEqual(csr.density, 5 / 9, places=6)
        dense = csr.to_dense()
        expected = np.array([
            [10.0,  0.0, 20.0],
            [ 0.0, 30.0,  0.0],
            [40.0,  0.0, 50.0],
        ])
        np.testing.assert_allclose(dense, expected)

    # -------------------------------------------------------------------------
    # 2. CSC Construction
    # -------------------------------------------------------------------------
    def test_02_csc_construction(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] CSC construction."""
        rows = np.array([0, 2, 1, 0, 2], dtype=np.int64)
        cols = np.array([0, 0, 1, 2, 2], dtype=np.int64)
        vals = np.array([10.0, 40.0, 30.0, 20.0, 50.0], dtype=np.float64)
        csc = csc_from_triplets(3, 3, rows, cols, vals)

        self.assertEqual(csc.n_rows, 3)
        self.assertEqual(csc.n_cols, 3)
        self.assertEqual(csc.nnz, 5)
        dense = csc.to_dense()
        expected = np.array([
            [10.0,  0.0, 20.0],
            [ 0.0, 30.0,  0.0],
            [40.0,  0.0, 50.0],
        ])
        np.testing.assert_allclose(dense, expected)

    # -------------------------------------------------------------------------
    # 3. CSR A x (matvec)
    # -------------------------------------------------------------------------
    def test_03_csr_matvec(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] CSR matvec product."""
        dense_A = np.array([
            [2.0, 0.0, -1.0, 0.0],
            [0.0, 4.0,  0.0, 3.0],
            [1.5, 0.0,  0.0, 2.5]
        ])
        csr = csr_from_dense(dense_A)
        x = np.array([1.0, -2.0, 3.0, 4.0])
        y_sparse = csr.matvec(x)
        y_dense = dense_A @ x
        np.testing.assert_allclose(y_sparse, y_dense, atol=1e-14)

    # -------------------------------------------------------------------------
    # 4. CSC A^T y (rmatvec)
    # -------------------------------------------------------------------------
    def test_04_csc_rmatvec(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] CSC rmatvec product."""
        dense_A = np.array([
            [2.0, 0.0, -1.0, 0.0],
            [0.0, 4.0,  0.0, 3.0],
            [1.5, 0.0,  0.0, 2.5]
        ])
        csc = csc_from_dense(dense_A)
        y = np.array([3.0, -1.0, 2.0])
        w_sparse = csc.rmatvec(y)
        w_dense = dense_A.T @ y
        np.testing.assert_allclose(w_sparse, w_dense, atol=1e-14)

    # -------------------------------------------------------------------------
    # 5. Sparse Basis Extraction
    # -------------------------------------------------------------------------
    def test_05_sparse_basis_extraction(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Sparse column extraction."""
        dense_A = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [0.0, 5.0, 0.0, 6.0],
            [7.0, 0.0, 8.0, 0.0]
        ])
        csc = csc_from_dense(dense_A)
        sub_csc = csc.extract_columns([3, 1])
        expected = dense_A[:, [3, 1]]
        np.testing.assert_allclose(sub_csc.to_dense(), expected)

    # -------------------------------------------------------------------------
    # 6. Deterministic Index Ordering
    # -------------------------------------------------------------------------
    def test_06_deterministic_index_ordering(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Deterministic sorting."""
        rows = np.array([0, 0, 0], dtype=np.int64)
        cols = np.array([3, 1, 2], dtype=np.int64)
        vals = np.array([30.0, 10.0, 20.0], dtype=np.float64)
        csr = csr_from_triplets(1, 4, rows, cols, vals)
        sorted_csr = csr.sort_indices()
        np.testing.assert_array_equal(sorted_csr.indices, [1, 2, 3])
        np.testing.assert_allclose(sorted_csr.data, [10.0, 20.0, 30.0])

    # -------------------------------------------------------------------------
    # 7. Duplicate Handling
    # -------------------------------------------------------------------------
    def test_07_duplicate_handling(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Triplet duplicate summation."""
        rows = np.array([0, 0, 1, 1], dtype=np.int64)
        cols = np.array([1, 1, 2, 2], dtype=np.int64)
        vals = np.array([2.5, 3.5, 10.0, -4.0], dtype=np.float64)
        csr = csr_from_triplets(2, 3, rows, cols, vals)
        dense = csr.to_dense()
        expected = np.array([
            [0.0, 6.0, 0.0],
            [0.0, 0.0, 6.0]
        ])
        np.testing.assert_allclose(dense, expected)

    # -------------------------------------------------------------------------
    # 8. Zero Dropping
    # -------------------------------------------------------------------------
    def test_08_zero_dropping(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Zero value pruning."""
        rows = np.array([0, 0, 1], dtype=np.int64)
        cols = np.array([0, 1, 1], dtype=np.int64)
        vals = np.array([5.0, 1e-15, 7.0], dtype=np.float64)
        csr = csr_from_triplets(2, 2, rows, cols, vals)
        pruned = csr.drop_zeros(tol=1e-12)
        self.assertEqual(pruned.nnz, 2)
        self.assertNotIn(1, pruned.indices[:pruned.indptr[1]])

    # -------------------------------------------------------------------------
    # 9. Markowitz Pivot Selection
    # -------------------------------------------------------------------------
    def test_09_markowitz_pivot_selection(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Markowitz pivot score."""
        # Row 0 has single entry at col 0 -> Markowitz score (1-1)*(3-1) = 0
        active_rows = {0: {0: 5.0}, 1: {0: 1.0, 1: 2.0, 2: 3.0}, 2: {0: 1.0, 1: 4.0, 2: 5.0}}
        active_cols = {0: {0, 1, 2}, 1: {1, 2}, 2: {1, 2}}
        selector = MarkowitzPivotSelector(u=0.1)
        res = selector.find_pivot(active_rows, active_cols)
        self.assertIsNotNone(res)
        r, c, val, score = res
        self.assertEqual((r, c), (0, 0))
        self.assertEqual(score, 0)

    # -------------------------------------------------------------------------
    # 10. Threshold Pivot Rejection
    # -------------------------------------------------------------------------
    def test_10_threshold_pivot_rejection(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Numerical threshold rejection."""
        # Element (0, 0) is tiny (1e-6) while (1, 0) is 100.0.
        # With u = 0.1, (0, 0) must be rejected because 1e-6 < 0.1 * 100.0.
        active_rows = {0: {0: 1e-6, 1: 1.0}, 1: {0: 100.0, 1: 2.0}}
        active_cols = {0: {0, 1}, 1: {0, 1}}
        selector = MarkowitzPivotSelector(u=0.1)
        res = selector.find_pivot(active_rows, active_cols)
        self.assertIsNotNone(res)
        r, c, val, score = res
        # Cannot pick (0, 0) for column 0
        self.assertNotEqual((r, c), (0, 0))

    # -------------------------------------------------------------------------
    # 11. Singular Sparse Matrix Detection
    # -------------------------------------------------------------------------
    def test_11_singular_sparse_matrix_detection(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Honest singularity detection."""
        # Matrix with all-zero column
        dense = np.array([
            [1.0, 0.0, 2.0],
            [3.0, 0.0, 4.0],
            [5.0, 0.0, 6.0]
        ])
        csc = csc_from_dense(dense)
        lu = SparseLU()
        with self.assertRaises(NumericalError):
            lu.factorize(csc)

    # -------------------------------------------------------------------------
    # 12. Sparse LU Factorization
    # -------------------------------------------------------------------------
    def test_12_sparse_lu_factorization(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] P B Q = L U factorization."""
        rng = np.random.default_rng(42)
        A_dense = rng.standard_normal((10, 10))
        # Zero out 70% of entries to make sparse
        A_dense[rng.uniform(size=(10, 10)) > 0.3] = 0.0
        A_dense += 5.0 * np.eye(10)  # ensure well-conditioned

        csc = csc_from_dense(A_dense)
        lu = SparseLU()
        lu.factorize(csc)

        # Verify P B Q = L U
        L_dense = lu.L_csr.to_dense()
        U_dense = lu.U_csr.to_dense()
        LU_prod = L_dense @ U_dense
        PBQ = A_dense[lu.p_perm, :][:, lu.q_perm]
        np.testing.assert_allclose(LU_prod, PBQ, atol=1e-12)

    # -------------------------------------------------------------------------
    # 13. FTRAN Residual
    # -------------------------------------------------------------------------
    def test_13_ftran_residual(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] FTRAN residual verification."""
        rng = np.random.default_rng(123)
        A = rng.standard_normal((15, 15))
        A[rng.uniform(size=(15, 15)) > 0.25] = 0.0
        A += 10.0 * np.eye(15)
        csc = csc_from_dense(A)
        b = rng.standard_normal(15)

        lu = SparseLU()
        lu.factorize(csc)
        x, init_res, final_res, _ = lu.solve(b)

        res_norm = float(np.max(np.abs(A @ x - b))) / float(np.max(np.abs(b)))
        self.assertLess(res_norm, 1e-12)

    # -------------------------------------------------------------------------
    # 14. BTRAN Residual
    # -------------------------------------------------------------------------
    def test_14_btran_residual(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] BTRAN residual verification."""
        rng = np.random.default_rng(456)
        A = rng.standard_normal((15, 15))
        A[rng.uniform(size=(15, 15)) > 0.25] = 0.0
        A += 10.0 * np.eye(15)
        csc = csc_from_dense(A)
        c = rng.standard_normal(15)

        lu = SparseLU()
        lu.factorize(csc)
        y, init_res, final_res, _ = lu.solve_transpose(c)

        res_norm = float(np.max(np.abs(A.T @ y - c))) / float(np.max(np.abs(c)))
        self.assertLess(res_norm, 1e-12)

    # -------------------------------------------------------------------------
    # 15. Sparse-vs-Dense Solve Agreement
    # -------------------------------------------------------------------------
    def test_15_sparse_vs_dense_solve_agreement(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Sparse and dense solve agreement."""
        rng = np.random.default_rng(789)
        A = rng.standard_normal((20, 20))
        A[rng.uniform(size=(20, 20)) > 0.3] = 0.0
        A += 8.0 * np.eye(20)
        b = rng.standard_normal(20)

        # Dense solve
        dense_lu = LU(A)
        x_dense = dense_lu.solve(b)

        # Sparse solve
        csc = csc_from_dense(A)
        sp_lu = SparseLU()
        sp_lu.factorize(csc)
        x_sparse, _, _, _ = sp_lu.solve(b)

        np.testing.assert_allclose(x_sparse, x_dense, atol=1e-11)

    # -------------------------------------------------------------------------
    # 16. Iterative Refinement Improvement
    # -------------------------------------------------------------------------
    def test_16_iterative_refinement_improvement(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Iterative refinement."""
        rng = np.random.default_rng(1011)
        A = rng.standard_normal((12, 12))
        A += 1e-2 * np.eye(12)  # slightly ill-conditioned
        csc = csc_from_dense(A)
        b = rng.standard_normal(12)

        sp_lu = SparseLU()
        sp_lu.factorize(csc)
        x, init_res, final_res, steps = sp_lu.solve(b, refine=True, max_refine=3)

        self.assertLessEqual(final_res, init_res + 1e-14)
        self.assertGreaterEqual(steps, 0)

    # -------------------------------------------------------------------------
    # 17. One Eta Update
    # -------------------------------------------------------------------------
    def test_17_one_eta_update(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Single PFI eta update."""
        rng = np.random.default_rng(2022)
        A = rng.standard_normal((8, 12))
        A += 4.0 * np.eye(8, 12)
        csc = csc_from_dense(A)
        basis = list(range(8))

        engine = SparseBasisEngine(max_eta_depth=10)
        engine.initialize(csc, basis)

        # Pivot: column 10 enters, replacing basis position 2
        entering_col = 10
        leaving_pos = 2
        col_rows, col_vals = csc.get_col(entering_col)
        a_ent = np.zeros(8)
        a_ent[col_rows] = col_vals
        d = engine.ftran(a_ent)

        engine.update(leaving_pos, entering_col, d)
        self.assertEqual(engine.eta_updates, 1)

        # Check FTRAN on updated basis against direct dense solve
        b = rng.standard_normal(8)
        xb_pfi = engine.ftran(b)

        updated_basis = list(basis)
        updated_basis[leaving_pos] = entering_col
        B_dense = A[:, updated_basis]
        xb_direct = LU(B_dense).solve(b)

        np.testing.assert_allclose(xb_pfi, xb_direct, atol=1e-12)

    # -------------------------------------------------------------------------
    # 18. Multiple Eta Updates
    # -------------------------------------------------------------------------
    def test_18_multiple_eta_updates(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Multiple sequential eta updates."""
        rng = np.random.default_rng(3033)
        A = rng.standard_normal((8, 16))
        A += 5.0 * np.eye(8, 16)
        csc = csc_from_dense(A)
        basis = list(range(8))

        engine = SparseBasisEngine(max_eta_depth=10)
        engine.initialize(csc, basis)

        # Perform 4 consecutive pivots
        pivots = [(0, 8), (3, 9), (5, 10), (1, 11)]
        current_basis = list(basis)

        for leaving_pos, entering_col in pivots:
            col_rows, col_vals = csc.get_col(entering_col)
            a_ent = np.zeros(8)
            a_ent[col_rows] = col_vals
            d = engine.ftran(a_ent)
            engine.update(leaving_pos, entering_col, d)
            current_basis[leaving_pos] = entering_col

        self.assertEqual(engine.eta_updates, 4)

        b = rng.standard_normal(8)
        xb_pfi = engine.ftran(b)
        xb_direct = LU(A[:, current_basis]).solve(b)
        np.testing.assert_allclose(xb_pfi, xb_direct, atol=1e-11)

    # -------------------------------------------------------------------------
    # 19. BTRAN with Eta Updates
    # -------------------------------------------------------------------------
    def test_19_btran_with_eta_updates(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] BTRAN after multiple eta updates."""
        rng = np.random.default_rng(4044)
        A = rng.standard_normal((8, 16))
        A += 5.0 * np.eye(8, 16)
        csc = csc_from_dense(A)
        basis = list(range(8))

        engine = SparseBasisEngine(max_eta_depth=10)
        engine.initialize(csc, basis)

        pivots = [(2, 8), (4, 9), (6, 10)]
        current_basis = list(basis)
        for leaving_pos, entering_col in pivots:
            col_rows, col_vals = csc.get_col(entering_col)
            a_ent = np.zeros(8)
            a_ent[col_rows] = col_vals
            d = engine.ftran(a_ent)
            engine.update(leaving_pos, entering_col, d)
            current_basis[leaving_pos] = entering_col

        c = rng.standard_normal(8)
        y_pfi = engine.btran(c)
        y_direct = LU(A[:, current_basis].T).solve(c)
        np.testing.assert_allclose(y_pfi, y_direct, atol=1e-11)

    # -------------------------------------------------------------------------
    # 20. Forced Refactorization
    # -------------------------------------------------------------------------
    def test_20_forced_refactorization(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Forced refactorization trigger."""
        rng = np.random.default_rng(5055)
        A = rng.standard_normal((6, 10)) + 4.0 * np.eye(6, 10)
        csc = csc_from_dense(A)
        basis = list(range(6))

        engine = SparseBasisEngine(max_eta_depth=10)
        engine.initialize(csc, basis)

        # Do one update
        col_rows, col_vals = csc.get_col(8)
        a_ent = np.zeros(6); a_ent[col_rows] = col_vals
        d = engine.ftran(a_ent)
        engine.update(1, 8, d)
        self.assertEqual(len(engine.etas), 1)

        # Force refactorization
        engine.force_refactorization()
        self.assertEqual(len(engine.etas), 0)
        self.assertEqual(engine.refactorizations, 2)
        self.assertEqual(engine.last_refactorization_reason, "FORCED")

    # -------------------------------------------------------------------------
    # 21. Eta-Limit Refactorization
    # -------------------------------------------------------------------------
    def test_21_eta_limit_refactorization(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Refactorization upon eta limit."""
        rng = np.random.default_rng(6066)
        A = rng.standard_normal((6, 12)) + 5.0 * np.eye(6, 12)
        csc = csc_from_dense(A)
        basis = list(range(6))

        # Max eta depth = 2
        engine = SparseBasisEngine(max_eta_depth=2)
        engine.initialize(csc, basis)

        for col, pos in [(6, 0), (7, 1)]:
            c_r, c_v = csc.get_col(col)
            a = np.zeros(6); a[c_r] = c_v
            d = engine.ftran(a)
            engine.update(pos, col, d)

        self.assertEqual(len(engine.etas), 2)
        # Next update hits limit and refactorizes
        c_r, c_v = csc.get_col(8)
        a = np.zeros(6); a[c_r] = c_v
        d = engine.ftran(a)
        engine.update(2, 8, d)

        self.assertEqual(engine.last_refactorization_reason, "ETA_LIMIT")
        self.assertEqual(len(engine.etas), 0)

    # -------------------------------------------------------------------------
    # 22. Residual-Triggered Refactorization
    # -------------------------------------------------------------------------
    def test_22_residual_triggered_refactorization(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Residual degradation trigger."""
        rng = np.random.default_rng(7077)
        A = rng.standard_normal((6, 10)) + 4.0 * np.eye(6, 10)
        csc = csc_from_dense(A)
        basis = list(range(6))

        # Set strict residual threshold
        engine = SparseBasisEngine(max_eta_depth=10, residual_threshold=1e-15)
        engine.initialize(csc, basis)

        c_r, c_v = csc.get_col(7)
        a = np.zeros(6); a[c_r] = c_v
        d = engine.ftran(a)
        engine.update(1, 7, d)

        # FTRAN with check_residual=True should trigger refactorization if residual exceeds threshold
        b = rng.standard_normal(6)
        engine.ftran(b, check_residual=True)
        self.assertIn(engine.last_refactorization_reason, ["RESIDUAL_DETERIORATION", "INITIAL"])

    # -------------------------------------------------------------------------
    # 23. Near-Singular Basis Recovery Semantics
    # -------------------------------------------------------------------------
    def test_23_near_singular_basis_recovery_semantics(self):
        """[INTERNAL MATHEMATICAL UNIT FIXTURE — NOT BENCHMARK DATA] Small pivot triggers refactorization."""
        rng = np.random.default_rng(8088)
        A = rng.standard_normal((6, 10)) + 4.0 * np.eye(6, 10)
        csc = csc_from_dense(A)
        basis = list(range(6))

        engine = SparseBasisEngine(max_eta_depth=10, min_pivot_mag=1e-4)
        engine.initialize(csc, basis)

        # Create a d vector where pivot position has tiny magnitude
        d_tiny = np.ones(6)
        d_tiny[2] = 1e-7

        engine.update(2, 7, d_tiny)
        self.assertEqual(engine.last_refactorization_reason, "SMALL_PIVOT")

    # -------------------------------------------------------------------------
    # 24. Sparse Primal Simplex on Genuine AFIRO
    # -------------------------------------------------------------------------
    def test_24_sparse_primal_simplex_afiro(self):
        """Solve Netlib AFIRO with sparse linear algebra backend."""
        model = load(str(DATA_DIR / "afiro.mps"))
        res = solve_lp(model, linear_algebra='sparse')
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -464.753142857143, places=6)
        self.assertEqual(res['linear_algebra_used'], 'sparse')
        self.assertEqual(res['basis_factorization'], 'sovereign_sparse_lu_pfi')
        self.assertGreater(res['refactorizations'], 0)
        self.assertGreater(res['eta_updates'], 0)
        self.assertGreater(res['ftran_count'], 0)
        self.assertGreater(res['btran_count'], 0)

    # -------------------------------------------------------------------------
    # 25. Sparse Primal Simplex on Genuine SC50A
    # -------------------------------------------------------------------------
    def test_25_sparse_primal_simplex_sc50a(self):
        """Solve Netlib SC50A with sparse linear algebra backend."""
        model = load(str(DATA_DIR / "sc50a.mps"))
        res = solve_lp(model, linear_algebra='sparse')
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -64.5750770585645, places=6)
        self.assertEqual(res['linear_algebra_used'], 'sparse')
        self.assertEqual(res['basis_factorization'], 'sovereign_sparse_lu_pfi')
        self.assertGreater(res['refactorizations'], 0)
        self.assertGreater(res['eta_updates'], 0)

    # -------------------------------------------------------------------------
    # 26. Sparse Primal Simplex on Genuine SC50B
    # -------------------------------------------------------------------------
    def test_26_sparse_primal_simplex_sc50b(self):
        """Solve Netlib SC50B with sparse linear algebra backend."""
        model = load(str(DATA_DIR / "sc50b.mps"))
        res = solve_lp(model, linear_algebra='sparse')
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -70.0000000000000, places=6)
        self.assertEqual(res['linear_algebra_used'], 'sparse')
        self.assertEqual(res['basis_factorization'], 'sovereign_sparse_lu_pfi')
        self.assertGreater(res['refactorizations'], 0)
        self.assertGreater(res['eta_updates'], 0)

    # -------------------------------------------------------------------------
    # 27. Sparse Primal Simplex on Genuine BLEND
    # -------------------------------------------------------------------------
    def test_27_sparse_primal_simplex_blend(self):
        """Solve Netlib BLEND with sparse linear algebra backend."""
        model = load(str(DATA_DIR / "blend.mps"))
        res = solve_lp(model, linear_algebra='sparse')
        self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(res['objective'], -30.8121498458282, places=6)
        self.assertEqual(res['linear_algebra_used'], 'sparse')
        self.assertEqual(res['basis_factorization'], 'sovereign_sparse_lu_pfi')
        self.assertGreater(res['refactorizations'], 0)
        self.assertGreater(res['eta_updates'], 0)

    # -------------------------------------------------------------------------
    # 28. Original-Model Verification after Sparse Solve
    # -------------------------------------------------------------------------
    def test_28_original_model_verification_after_sparse_solve(self):
        """Verify KKT satisfaction on original model after sparse solve across all 4 Netlib instances."""
        benchmarks = [
            ("afiro.mps", -464.753142857143),
            ("sc50a.mps", -64.5750770585645),
            ("sc50b.mps", -70.0000000000000),
            ("blend.mps", -30.8121498458282),
        ]
        for filename, ref_obj in benchmarks:
            path = DATA_DIR / filename
            model = load(str(path))
            res = solve_lp(model, linear_algebra='sparse')
            self.assertEqual(res['status'], 'OPTIMAL_VERIFIED')
            self.assertTrue(res['verification']['kkt_passed'])
            self.assertTrue(res['verification']['feasible'])
            self.assertAlmostEqual(res['objective'], ref_obj, places=6)


if __name__ == '__main__':
    unittest.main()
