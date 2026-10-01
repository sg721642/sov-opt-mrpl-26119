"""Comprehensive test suite for QPLIB parser and QP solver integration.

Covers all 17 mandatory verification items:
1. diagonal quadratic objective evaluates correctly
2. off-diagonal quadratic objective evaluates correctly
3. parsed objective equals manual 0.5*x.T@Q@x + b@x + q
4. reported QPLIB solution objective matches parsed model on published test files (QPLIB_8845)
5. duplicate Q / L entries are handled or rejected cleanly
6. zero entries are pruned or preserved predictably
7. row sense / bounds match official semantics
8. missing variable bounds default to official conventions (0 <= x < infty unless specified)
9. objective constant q0 is preserved and accounted for in total objective
10. continuous instances correctly identified
11. integer / binary / MIQP correctly rejected or classified
12. quadratic constraints correctly rejected or classified
13. nonconvex quadratic objectives correctly rejected (including QPLIB_0018 negative test)
14. malformed files fail with descriptive errors, not crashes
15. PSD eligibility checked with scale-aware tolerance
16. original-model KKT / primal / dual verification passes on accepted solve
17. objective matches published reference value within declared tolerance
"""

import tempfile
import unittest
from pathlib import Path
import numpy as np

from sovopt import Model, load, solve, read_qplib, parse_probtype
from sovopt.qplib import QPLIBError, UnsupportedQPLIBError, QPLIBFormatError
from sovopt.verify import verify, _reported_objective

ROOT = Path(__file__).resolve().parents[1]


class TestQPLIBSupport(unittest.TestCase):
    def _write_temp_qplib(self, content: str) -> Path:
        t = tempfile.NamedTemporaryFile("w", suffix=".qplib", delete=False)
        t.write(content)
        t.close()
        self.addCleanup(lambda: Path(t.name).unlink(missing_ok=True))
        return Path(t.name)

    # ------------------------------------------------------------------
    # 1. Diagonal quadratic objective evaluates correctly
    # ------------------------------------------------------------------
    def test_01_diagonal_quadratic_objective(self):
        content = """
        TEST_DIAG
        CCL
        minimize
        2
        0
        2
        1 1 2.0
        2 2 4.0
        0.0 2
        1 1.0
        2 2.0
        5.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertEqual(len(m.c), 2)
        self.assertEqual(m.obj_offset, 5.0)
        self.assertEqual(m.Q[0, 0], 2.0)
        self.assertEqual(m.Q[1, 1], 4.0)
        self.assertEqual(m.Q[0, 1], 0.0)

        # For x = [1, 2]: 1/2 * (2*1 + 4*4) + (1*1 + 2*2) + 5 = 19.0
        x = np.array([1.0, 2.0])
        val = _reported_objective(m, x, m.Q)
        self.assertAlmostEqual(val, 19.0, places=9)

    # ------------------------------------------------------------------
    # 2. Off-diagonal quadratic objective evaluates correctly
    # ------------------------------------------------------------------
    def test_02_off_diagonal_quadratic_objective(self):
        # To maintain positive semidefiniteness (det >= 0), set diagonal entries to 5.0
        # Q0 = [[5, 0], [6, 5]] -> Q_sym = [[5, 3], [3, 5]], eigenvalues [2, 8]
        # In QPLIB: 1/2 x^T Q0 x with Q0 lower-triangular => 1/2 (6*x2*x1) = 3*x1*x2
        # In symmetric Q: Q_sym[0, 1] = Q_sym[1, 0] = 3.0 so 1/2 x^T Q_sym x = 1/2*(5*x1^2 + 5*x2^2) + 3*x1*x2
        content = """
        TEST_OFFDIAG
        CCL
        minimize
        2
        0
        3
        1 1 5.0
        2 2 5.0
        2 1 6.0
        0.0 0
        0.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertAlmostEqual(m.Q[1, 0], 3.0, places=9)
        self.assertAlmostEqual(m.Q[0, 1], 3.0, places=9)
        self.assertAlmostEqual(m.Q[0, 0], 5.0, places=9)
        self.assertAlmostEqual(m.Q[1, 1], 5.0, places=9)

        # For x = [1, 1]: 1/2 * (5 + 3 + 3 + 5) = 8.0
        x_plus = np.array([1.0, 1.0])
        val_plus = _reported_objective(m, x_plus, m.Q)
        self.assertAlmostEqual(val_plus, 8.0, places=9)

        # For x = [1, -1]: 1/2 * (5 - 3 - 3 + 5) = 2.0
        x_minus = np.array([1.0, -1.0])
        val_minus = _reported_objective(m, x_minus, m.Q)
        self.assertAlmostEqual(val_minus, 2.0, places=9)

        # Difference isolates off-diagonal contribution: (8.0 - 2.0) / 2 = 3.0
        self.assertAlmostEqual((val_plus - val_minus) / 2.0, 3.0, places=9)

    # ------------------------------------------------------------------
    # 3. Parsed objective equals manual 0.5*x.T@Q@x + b@x + q
    # ------------------------------------------------------------------
    def test_03_parsed_objective_equals_manual_formula(self):
        content = """
        TEST_MANUAL
        CCL
        minimize
        3
        0
        3
        1 1 4.0
        2 2 6.0
        3 1 2.0
        0.0 3
        1 1.5
        2 -2.0
        3 0.5
        10.25
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        x = np.array([1.5, 2.0, -1.0])
        manual = 0.5 * float(x.T @ m.Q @ x) + float(m.c @ x) + m.obj_offset
        reported = _reported_objective(m, x, m.Q)
        self.assertAlmostEqual(reported, manual, places=12)

    # ------------------------------------------------------------------
    # 4. Reported QPLIB solution objective matches parsed model on QPLIB_8845
    # ------------------------------------------------------------------
    def test_04_reported_solution_matches_parsed_model_qplib_8845(self):
        qplib_file = ROOT / "data/qplib/QPLIB_8845.qplib"
        sol_file = ROOT / "data/qplib/QPLIB_8845.sol"
        if not qplib_file.exists() or not sol_file.exists():
            self.skipTest("QPLIB_8845 dataset or solfile not present")

        m = read_qplib(qplib_file)
        n = len(m.c)
        x_sol = np.zeros(n)
        ref_obj = None

        for line in sol_file.read_text().splitlines():
            parts = line.split()
            if not parts:
                continue
            if parts[0].lower() in ("objvar", "=obj="):
                ref_obj = float(parts[1])
            elif parts[0].startswith("x"):
                idx = int(parts[0][1:]) - 2
                if 0 <= idx < n:
                    x_sol[idx] = float(parts[1])

        self.assertIsNotNone(ref_obj)
        self.assertAlmostEqual(ref_obj, 10907992.4939988, places=4)

        calc_obj = _reported_objective(m, x_sol, m.Q)
        diff = abs(calc_obj - ref_obj)
        rel_diff = diff / max(1.0, abs(ref_obj))
        self.assertLess(rel_diff, 1e-10)

        rep = verify(m, x_sol)
        self.assertTrue(rep["feasible"])
        self.assertLess(rep["primal_residual"], 1e-10)

    # ------------------------------------------------------------------
    # 5. Duplicate Q / L entries are handled cleanly (accumulated)
    # ------------------------------------------------------------------
    def test_05_duplicate_entries_handled_cleanly(self):
        content = """
        TEST_DUP
        CCL
        minimize
        2
        1
        2
        1 1 2.0
        1 1 3.0
        0.0 0
        0.0
        2
        1 1 1.0
        1 1 2.0
        1e20
        -1e20 0
        10.0 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertEqual(m.Q[0, 0], 5.0)
        self.assertEqual(m.A[0, 0], 3.0)

    # ------------------------------------------------------------------
    # 6. Zero entries are pruned or preserved predictably
    # ------------------------------------------------------------------
    def test_06_zero_entries_pruned_or_preserved(self):
        content = """
        TEST_ZERO
        CCL
        minimize
        2
        1
        1
        1 1 0.0
        0.0 0
        0.0
        1
        1 1 0.0
        1e20
        -1e20 0
        10.0 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertEqual(m.Q[0, 0], 0.0)
        self.assertEqual(m.A[0, 0], 0.0)
        self.assertEqual(m.A.shape, (1, 2))
        self.assertEqual(m.Q.shape, (2, 2))

    # ------------------------------------------------------------------
    # 7. Row sense / bounds match official semantics
    # ------------------------------------------------------------------
    def test_07_row_bounds_match_official_semantics(self):
        content = """
        TEST_ROWS
        CCL
        minimize
        2
        4
        0
        0.0 0
        0.0
        4
        1 1 1.0
        2 1 1.0
        3 1 1.0
        4 1 1.0
        1e20
        -1e20 3
        2 5.0
        3 10.0
        4 1.0
        1e20 3
        1 8.0
        3 10.0
        4 4.0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertTrue(np.isneginf(m.row_lower[0]))
        self.assertEqual(m.row_upper[0], 8.0)
        self.assertEqual(m.row_lower[1], 5.0)
        self.assertTrue(np.isposinf(m.row_upper[1]))
        self.assertEqual(m.row_lower[2], 10.0)
        self.assertEqual(m.row_upper[2], 10.0)
        self.assertEqual(m.row_lower[3], 1.0)
        self.assertEqual(m.row_upper[3], 4.0)

    # ------------------------------------------------------------------
    # 8. Missing variable bounds default to official conventions (0 <= x < infty)
    # ------------------------------------------------------------------
    def test_08_missing_variable_bounds_defaults(self):
        content = """
        TEST_BOUNDS
        CCL
        minimize
        3
        0
        0
        0.0 0
        0.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 1
        1 -5.0
        1e20 1
        2 10.0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertEqual(m.lower[0], -5.0)
        self.assertTrue(np.isposinf(m.upper[0]))
        self.assertEqual(m.lower[1], 0.0)
        self.assertEqual(m.upper[1], 10.0)
        self.assertEqual(m.lower[2], 0.0)
        self.assertTrue(np.isposinf(m.upper[2]))

    # ------------------------------------------------------------------
    # 9. Objective constant q0 is preserved and accounted for
    # ------------------------------------------------------------------
    def test_09_objective_constant_preserved(self):
        content = """
        TEST_OFFSET
        CCL
        minimize
        1
        0
        1
        1 1 2.0
        0.0 0
        -999.5
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        m = read_qplib(p)
        self.assertEqual(m.obj_offset, -999.5)
        x = np.array([2.0])
        self.assertAlmostEqual(_reported_objective(m, x, m.Q), -995.5, places=9)

    # ------------------------------------------------------------------
    # 10. Continuous instances correctly identified
    # ------------------------------------------------------------------
    def test_10_continuous_instances_correctly_identified(self):
        for pt in ("CCL", "DCL", "CCB", "DCB", "LCL"):
            info = parse_probtype(pt)
            self.assertTrue(info["is_supported"], f"Expected {pt} to be supported")
            self.assertEqual(info["reason_code"], "SUPPORTED")

    # ------------------------------------------------------------------
    # 11. Integer / binary / MIQP correctly rejected or classified
    # ------------------------------------------------------------------
    def test_11_discrete_instances_rejected(self):
        for pt in ("CBL", "DML", "CIL", "CGL"):
            info = parse_probtype(pt)
            self.assertFalse(info["is_supported"])
            self.assertEqual(info["reason_code"], "UNSUPPORTED_DISCRETE_VARIABLES")

        content = """
        TEST_INT
        CML
        minimize
        1
        0
        0
        0.0 0
        0.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        with self.assertRaises(UnsupportedQPLIBError) as ctx:
            read_qplib(p)
        self.assertEqual(ctx.exception.reason_code, "UNSUPPORTED_DISCRETE_VARIABLES")

    # ------------------------------------------------------------------
    # 12. Quadratic constraints correctly rejected or classified
    # ------------------------------------------------------------------
    def test_12_quadratic_constraints_rejected(self):
        for pt in ("CCQ", "CCD", "CCC"):
            info = parse_probtype(pt)
            self.assertFalse(info["is_supported"])
            self.assertEqual(info["reason_code"], "UNSUPPORTED_QUADRATIC_CONSTRAINTS")

        content = """
        TEST_QC
        CBQ
        minimize
        1
        0
        0
        0.0 0
        0.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p = self._write_temp_qplib(content)
        with self.assertRaises(UnsupportedQPLIBError) as ctx:
            read_qplib(p)
        # Note: CBQ has discrete B and quadratic Q, discrete check takes precedence or constraint check
        self.assertIn(ctx.exception.reason_code, ("UNSUPPORTED_DISCRETE_VARIABLES", "UNSUPPORTED_QUADRATIC_CONSTRAINTS"))

    # ------------------------------------------------------------------
    # 13. Nonconvex quadratic objectives correctly rejected (including QPLIB_0018)
    # ------------------------------------------------------------------
    def test_13_nonconvex_rejected_qplib_0018(self):
        info = parse_probtype("QCL")
        self.assertFalse(info["is_supported"])
        self.assertEqual(info["reason_code"], "UNSUPPORTED_NONCONVEX_QP")

        qplib_0018 = ROOT / "data/qplib/QPLIB_0018.qplib"
        if qplib_0018.exists():
            with self.assertRaises(UnsupportedQPLIBError) as ctx:
                read_qplib(qplib_0018)
            self.assertEqual(ctx.exception.reason_code, "UNSUPPORTED_NONCONVEX_QP")

    # ------------------------------------------------------------------
    # 14. Malformed files fail with descriptive errors, not crashes
    # ------------------------------------------------------------------
    def test_14_malformed_files_fail_descriptively(self):
        p_trunc = self._write_temp_qplib("TEST_SHORT\nminimize\n")
        with self.assertRaises(QPLIBFormatError):
            read_qplib(p_trunc)

        content_upper = """
        TEST_UPPER
        CCL
        minimize
        2
        0
        1
        1 2 5.0
        0.0 0
        0.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p_upper = self._write_temp_qplib(content_upper)
        with self.assertRaises(QPLIBFormatError) as ctx:
            read_qplib(p_upper)
        self.assertIn("lower triangular", str(ctx.exception))

    # ------------------------------------------------------------------
    # 15. PSD eligibility checked with scale-aware tolerance
    # ------------------------------------------------------------------
    def test_15_psd_eligibility_scale_aware(self):
        content_tiny_neg = """
        TEST_TINY_NEG
        CCL
        minimize
        2
        0
        2
        1 1 10.0
        2 2 -1e-12
        0.0 0
        0.0
        0
        1e20
        -1e20 0
        1e20 0
        0.0 0
        1e20 0
        """
        p_tiny = self._write_temp_qplib(content_tiny_neg)
        m = read_qplib(p_tiny)
        self.assertGreaterEqual(np.min(np.linalg.eigvalsh(m.Q)), -1e-11)

    # ------------------------------------------------------------------
    # 16. Original-model KKT / primal / dual verification passes on accepted solve
    # ------------------------------------------------------------------
    def test_16_kkt_verification_on_solve(self):
        c = np.array([-2.0, -2.0])
        Q = np.array([[2.0, 0.0], [0.0, 2.0]])
        A = np.array([[1.0, 1.0]])
        row_lower = np.array([-np.inf])
        row_upper = np.array([1.0])
        lower = np.array([0.0, 0.0])
        upper = np.array([np.inf, np.inf])

        m = Model(c=c, A=A, row_lower=row_lower, row_upper=row_upper, lower=lower, upper=upper, Q=Q, name="toy_qp")
        res = solve(m)
        self.assertEqual(res["status"], "OPTIMAL_VERIFIED")
        self.assertTrue(res["verification"]["kkt_passed"])
        self.assertAlmostEqual(res["objective"], -1.5, places=5)

    # ------------------------------------------------------------------
    # 17. Objective matches published reference value within declared tolerance
    # ------------------------------------------------------------------
    def test_17_objective_matches_reference(self):
        qplib_file = ROOT / "data/qplib/QPLIB_8845.qplib"
        if not qplib_file.exists():
            self.skipTest("QPLIB_8845 not present")
        m = load(qplib_file)
        self.assertEqual(m.name, "QPLIB_8845")
        self.assertIsNotNone(m.Q)
        self.assertEqual(m.Q.shape, (1546, 1546))

        # Sovereign solve via production solve() API
        res = solve(m, backend="cpu", max_iter=30, tol=1e-7)
        self.assertEqual(res["status"], "OPTIMAL_VERIFIED")
        self.assertTrue(res["verification"]["kkt_passed"])
        self.assertTrue(res["solver_generated_x"])
        self.assertFalse(res["reference_solution_used_as_initialization"])

        # Reference objective comparison (from official QPLIB published benchmark)
        ref_obj = 10907992.4939988
        sov_obj = res["objective"]
        rel_diff = abs(sov_obj - ref_obj) / abs(ref_obj)
        self.assertLess(rel_diff, 1e-7, f"Relative discrepancy {rel_diff:.2e} exceeds 1e-7")

    # ------------------------------------------------------------------
    # 18. Reference solution leakage prevention (Step 22)
    # ------------------------------------------------------------------
    def test_18_no_reference_leakage_when_sol_file_hidden(self):
        """Proves production solve does not read QPLIB_8845.sol to solve or initialize."""
        qplib_file = ROOT / "data/qplib/QPLIB_8845.qplib"
        sol_file = ROOT / "data/qplib/QPLIB_8845.sol"
        if not qplib_file.exists() or not sol_file.exists():
            self.skipTest("QPLIB_8845 files not present")

        backup_sol = sol_file.with_suffix(".sol.hidden_test_bak")
        try:
            sol_file.rename(backup_sol)
            self.assertFalse(sol_file.exists())

            m = load(qplib_file)
            res = solve(m, backend="cpu", max_iter=30, tol=1e-7)
            self.assertEqual(res["status"], "OPTIMAL_VERIFIED")
            self.assertTrue(res["verification"]["kkt_passed"])
            self.assertTrue(res["solver_generated_x"])
        finally:
            if backup_sol.exists():
                backup_sol.rename(sol_file)
            self.assertTrue(sol_file.exists())


if __name__ == "__main__":
    unittest.main()

