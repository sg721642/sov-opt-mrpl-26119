"""Sovereign Sparse LU Factorization and Basis Engine with Eta Updates.

Dependencies: Python standard library and NumPy only.
Strictly prohibited: scipy.sparse, SuiteSparse, UMFPACK, SuperLU, or any external library.

Features:
- Threshold Markowitz pivot selection: minimizes (r_i - 1) * (c_j - 1) subject to |a_ij| >= u * max |a_kj|.
- Permuted sparse LU: P B Q = L U.
- Sovereign forward and backward sparse solves (FTRAN / BTRAN) with zero np.linalg.solve.
- Residual-based iterative refinement with platform longdouble precision detection.
- Product-Form of the Inverse (PFI / eta updates) between full refactorizations.
- Deterministic refactorization triggers on eta depth, small pivot, residual deterioration, or singularity.
- Full basis telemetry and instrumentation.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np

from .linalg import NumericalError
from .sparse import CSRMatrix, CSCMatrix, csc_from_dense, csc_from_triplets, csr_from_triplets


# Platform longdouble check
_LD_INFO = np.finfo(np.longdouble)
_F64_INFO = np.finfo(np.float64)
PLATFORM_LONGDOUBLE_EXTENDED = bool(_LD_INFO.bits > _F64_INFO.bits)


@dataclass
class MarkowitzDiagnostic:
    pivot_row: int
    pivot_col: int
    pivot_val: float
    markowitz_score: int
    active_row_nnz: int
    active_col_nnz: int
    fill_created: int


@dataclass
class EtaVector:
    pos: int                  # Pivot row position in basis (leaving variable index in basis array)
    eta: np.ndarray           # Column vector d = B^{-1} a_entering
    pivot_val: float          # eta[pos]
    entering_col: int         # Original column index entering basis
    leaving_col: int          # Original column index leaving basis


class MarkowitzPivotSelector:
    """Selects pivots using the Markowitz fill-in criterion with threshold numerical stability."""

    def __init__(self, u: float = 0.1, pivot_tol: float = 1e-13):
        if not (0.0 < u <= 1.0):
            raise ValueError(f"Threshold parameter u must be in (0, 1], got {u}")
        self.u = float(u)
        self.pivot_tol = float(pivot_tol)

    def find_pivot(self,
                   active_rows: dict[int, dict[int, float]],
                   active_cols: dict[int, set[int]],
                   search_limit: int = 16) -> Optional[tuple[int, int, float, int]]:
        """Find best pivot (row, col, val, score) in active submatrix.

        Returns None if matrix is singular (no numerically acceptable pivot).
        """
        if not active_rows or not active_cols:
            return None

        # Precompute column maximums for active rows
        col_max = {}
        for c, rows in active_cols.items():
            if rows:
                col_max[c] = max(abs(active_rows[r][c]) for r in rows)
            else:
                col_max[c] = 0.0

        best_score = float('inf')
        best_cand = None
        best_abs_val = -1.0

        # Sort columns and rows by active nonzero count to search sparse rows/columns first
        sorted_cols = sorted(active_cols.keys(), key=lambda c: len(active_cols[c]))
        cols_to_search = sorted_cols[:min(len(sorted_cols), max(search_limit, 4))]

        # Track rows inspected
        rows_inspected = set()

        for c in cols_to_search:
            c_nnz = len(active_cols[c])
            if c_nnz == 0:
                continue
            c_thresh = self.u * col_max[c]
            if c_thresh < self.pivot_tol:
                continue

            for r in active_cols[c]:
                rows_inspected.add(r)
                val = active_rows[r][c]
                abs_val = abs(val)

                if abs_val < c_thresh or abs_val < self.pivot_tol:
                    continue

                r_nnz = len(active_rows[r])
                score = (r_nnz - 1) * (c_nnz - 1)

                # Singleton shortcut: score == 0 creates zero fill-in
                if score == 0:
                    return (r, c, val, score)

                # Standard Markowitz comparison with deterministic tie-breaking
                if score < best_score:
                    best_score = score
                    best_cand = (r, c, val, score)
                    best_abs_val = abs_val
                elif score == best_score:
                    # Tie-breaking: prefer larger absolute value
                    if abs_val > best_abs_val + 1e-14:
                        best_cand = (r, c, val, score)
                        best_abs_val = abs_val
                    elif abs(abs_val - best_abs_val) <= 1e-14:
                        # Tie-breaking: lowest row index, then lowest col index
                        if best_cand is not None and (r, c) < (best_cand[0], best_cand[1]):
                            best_cand = (r, c, val, score)
                            best_abs_val = abs_val

        # If sparse search found a candidate, return it
        if best_cand is not None:
            return best_cand

        # Fallback: full active nonzero inspection if search_limit was too restrictive
        for r, row_dict in active_rows.items():
            if r in rows_inspected:
                continue
            r_nnz = len(row_dict)
            if r_nnz == 0:
                continue
            for c, val in row_dict.items():
                abs_val = abs(val)
                if abs_val < self.u * col_max.get(c, 0.0) or abs_val < self.pivot_tol:
                    continue
                c_nnz = len(active_cols[c])
                score = (r_nnz - 1) * (c_nnz - 1)

                if score == 0:
                    return (r, c, val, score)

                if score < best_score:
                    best_score = score
                    best_cand = (r, c, val, score)
                    best_abs_val = abs_val
                elif score == best_score:
                    if abs_val > best_abs_val + 1e-14:
                        best_cand = (r, c, val, score)
                        best_abs_val = abs_val
                    elif abs(abs_val - best_abs_val) <= 1e-14:
                        if best_cand is not None and (r, c) < (best_cand[0], best_cand[1]):
                            best_cand = (r, c, val, score)
                            best_abs_val = abs_val

        return best_cand


class SparseLU:
    """Sovereign Sparse LU Factorization (P B Q = L U).

    Guarantees:
    - Never converts B to a dense 2D array for factorization.
    - Never calls np.linalg.solve.
    - True Threshold Markowitz pivoting with dynamic fill tracking.
    - Both FTRAN (Bx=b) and BTRAN (B^T y=b) use the exact same sparse L and U factors.
    """

    def __init__(self, u: float = 0.1, drop_tol: float = 1e-15, pivot_tol: float = 1e-13):
        self.u = float(u)
        self.drop_tol = float(drop_tol)
        self.pivot_tol = float(pivot_tol)

        # Factorization state
        self.m = 0
        self.p_perm = np.zeros(0, dtype=np.int64)  # Row permutation: p_perm[k] = original row for step k
        self.q_perm = np.zeros(0, dtype=np.int64)  # Col permutation: q_perm[k] = original col for step k
        self.p_inv = np.zeros(0, dtype=np.int64)   # Inverse row permutation
        self.q_inv = np.zeros(0, dtype=np.int64)   # Inverse col permutation

        self.L_csr: Optional[CSRMatrix] = None
        self.L_csc: Optional[CSCMatrix] = None
        self.U_csr: Optional[CSRMatrix] = None
        self.U_csc: Optional[CSCMatrix] = None
        self.diag_U: np.ndarray = np.zeros(0, dtype=np.float64)

        self.original_matrix: Optional[CSCMatrix] = None
        self.growth_factor: float = 1.0
        self.diagnostics: list[MarkowitzDiagnostic] = []

    def factorize(self, B: CSCMatrix | CSRMatrix) -> None:
        """Compute P B Q = L U on sparse basis matrix B."""
        if B.n_rows != B.n_cols:
            raise NumericalError(f"Basis matrix must be square, got shape ({B.n_rows}, {B.n_cols})")
        m = B.n_rows
        self.m = m

        if m == 0:
            return

        # Preserve original matrix for iterative refinement
        if isinstance(B, CSCMatrix):
            self.original_matrix = B.copy()
            B_csc = B
        else:
            self.original_matrix = B.to_csc()
            B_csc = self.original_matrix

        max_orig_entry = float(np.max(np.abs(B_csc.data), initial=1.0))
        max_u_entry = max_orig_entry

        # Initialize active submatrix representation
        # active_rows[i] = {col: val, ...}
        # active_cols[j] = {row, ...}
        active_rows = {i: {} for i in range(m)}
        active_cols = {j: set() for j in range(m)}

        for j in range(m):
            start = B_csc.indptr[j]
            end = B_csc.indptr[j + 1]
            rows = B_csc.indices[start:end]
            vals = B_csc.data[start:end]
            for r, v in zip(rows, vals):
                if abs(v) > self.drop_tol:
                    active_rows[r][j] = float(v)
                    active_cols[j].add(int(r))

        selector = MarkowitzPivotSelector(u=self.u, pivot_tol=self.pivot_tol)

        p_list = []
        q_list = []
        L_triplets = []  # (step_i, step_k, multiplier)
        U_triplets = []  # (step_k, step_j, val)
        self.diagnostics.clear()

        # Gaussian Elimination steps k = 0 ... m - 1
        for k in range(m):
            cand = selector.find_pivot(active_rows, active_cols)
            if cand is None:
                raise NumericalError(f"Singular basis matrix detected at sparse LU elimination step {k}/{m}")

            p_k, q_k, pivot_val, score = cand
            p_list.append(p_k)
            q_list.append(q_k)

            # Record U pivot row (current step k)
            pivot_row_dict = active_rows[p_k]
            for c, val in pivot_row_dict.items():
                U_triplets.append((k, c, val))
                if abs(val) > max_u_entry:
                    max_u_entry = abs(val)

            # Eliminate in active columns
            cols_in_pivot_row = list(pivot_row_dict.keys())
            other_rows = [r for r in active_cols[q_k] if r != p_k]

            fill_count = 0
            for r in other_rows:
                mult = active_rows[r][q_k] / pivot_val
                L_triplets.append((r, k, mult))

                # Remove pivot column entry from row r
                del active_rows[r][q_k]

                # Update row r with Schur complement: a_rc -= mult * a_p_kc
                for c in cols_in_pivot_row:
                    if c == q_k:
                        continue
                    update_val = mult * pivot_row_dict[c]
                    if c in active_rows[r]:
                        new_val = active_rows[r][c] - update_val
                        if abs(new_val) <= self.drop_tol:
                            del active_rows[r][c]
                            active_cols[c].discard(r)
                        else:
                            active_rows[r][c] = new_val
                    else:
                        new_val = -update_val
                        if abs(new_val) > self.drop_tol:
                            active_rows[r][c] = new_val
                            active_cols[c].add(r)
                            fill_count += 1

            # Remove pivot row and pivot column from active submatrix
            del active_rows[p_k]
            del active_cols[q_k]
            for c in cols_in_pivot_row:
                if c != q_k:
                    active_cols[c].discard(p_k)

            self.diagnostics.append(MarkowitzDiagnostic(
                pivot_row=p_k, pivot_col=q_k, pivot_val=pivot_val,
                markowitz_score=score, active_row_nnz=len(pivot_row_dict),
                active_col_nnz=len(other_rows) + 1, fill_created=fill_count
            ))

        self.p_perm = np.array(p_list, dtype=np.int64)
        self.q_perm = np.array(q_list, dtype=np.int64)

        self.p_inv = np.empty(m, dtype=np.int64)
        self.p_inv[self.p_perm] = np.arange(m, dtype=np.int64)

        self.q_inv = np.empty(m, dtype=np.int64)
        self.q_inv[self.q_perm] = np.arange(m, dtype=np.int64)

        # Build permuted L and U sparse factor matrices
        # In permuted coordinates:
        # L row is p_inv[orig_r], L col is step k
        L_rows = [self.p_inv[orig_r] for orig_r, k, _ in L_triplets]
        L_cols = [k for _, k, _ in L_triplets]
        L_vals = [val for _, _, val in L_triplets]

        # Unit diagonal for L
        L_rows.extend(range(m))
        L_cols.extend(range(m))
        L_vals.extend([1.0] * m)

        self.L_csr = csr_from_triplets(m, m, np.array(L_rows), np.array(L_cols), np.array(L_vals)).sort_indices()
        self.L_csc = self.L_csr.to_csc()

        # U row is step k, U col is q_inv[orig_c]
        U_rows = [k for k, orig_c, _ in U_triplets]
        U_cols = [self.q_inv[orig_c] for _, orig_c, _ in U_triplets]
        U_vals = [val for _, _, val in U_triplets]

        self.U_csr = csr_from_triplets(m, m, np.array(U_rows), np.array(U_cols), np.array(U_vals)).sort_indices()
        self.U_csc = self.U_csr.to_csc()

        # Precompute diagonal of U for fast division in triangular solves
        self.diag_U = np.zeros(m, dtype=np.float64)
        for k in range(m):
            cols, vals = self.U_csr.get_row(k)
            diag_idx = np.where(cols == k)[0]
            if len(diag_idx) == 0 or abs(vals[diag_idx[0]]) < self.pivot_tol:
                raise NumericalError(f"Singular diagonal encountered in U factor at position {k}")
            self.diag_U[k] = vals[diag_idx[0]]

        self.growth_factor = float(max_u_entry / max(max_orig_entry, 1e-14))

    def solve(self, rhs: np.ndarray, refine: bool = True, max_refine: int = 2, tol: float = 1e-12) -> tuple[np.ndarray, float, float, int]:
        """Solve B x = rhs (FTRAN) using sparse factors P B Q = L U.

        Returns (x, initial_residual, final_residual, refinement_steps).
        """
        b = np.asarray(rhs, dtype=np.float64)
        m = self.m
        if b.shape != (m,):
            raise NumericalError(f"RHS dimension mismatch: expected ({m},), got {b.shape}")

        x0 = self._raw_solve(b)

        # Iterative refinement
        init_res = float(np.max(np.abs(b - self.original_matrix.matvec(x0)), initial=0.0))
        cur_res = init_res
        refine_steps = 0
        x = x0.copy()

        rhs_norm = float(np.max(np.abs(b), initial=1.0))
        target_res = tol * (1.0 + rhs_norm)

        if refine and cur_res > target_res:
            for step in range(max_refine):
                # Calculate residual
                if PLATFORM_LONGDOUBLE_EXTENDED:
                    r = np.asarray(np.asarray(b, np.longdouble) - self.original_matrix.matvec(x).astype(np.longdouble), dtype=np.float64)
                else:
                    r = b - self.original_matrix.matvec(x)

                res_norm = float(np.max(np.abs(r), initial=0.0))
                if res_norm <= target_res:
                    break

                corr = self._raw_solve(r)
                x += corr
                refine_steps += 1
                cur_res = float(np.max(np.abs(b - self.original_matrix.matvec(x)), initial=0.0))
                if cur_res <= target_res:
                    break

        if not np.all(np.isfinite(x)):
            raise NumericalError("Non-finite solution produced in sparse LU solve")

        return x, init_res, cur_res, refine_steps

    def _raw_solve(self, b: np.ndarray) -> np.ndarray:
        """Raw forward and backward triangular solve: P B Q x = L U (Q^T x) = P b."""
        m = self.m
        # 1. Permute RHS: b_tilde = P b
        b_tilde = b[self.p_perm]

        # 2. Forward solve L y = b_tilde (L is unit lower triangular CSR)
        y = np.zeros(m, dtype=np.float64)
        indptr_L = self.L_csr.indptr
        indices_L = self.L_csr.indices
        data_L = self.L_csr.data

        for i in range(m):
            start = indptr_L[i]
            end = indptr_L[i + 1]
            cols = indices_L[start:end]
            vals = data_L[start:end]
            # Strictly lower triangular part (cols < i)
            mask = cols < i
            if np.any(mask):
                dot_val = np.dot(vals[mask], y[cols[mask]])
                y[i] = b_tilde[i] - dot_val
            else:
                y[i] = b_tilde[i]

        # 3. Backward solve U z = y (U is upper triangular CSR)
        z = np.zeros(m, dtype=np.float64)
        indptr_U = self.U_csr.indptr
        indices_U = self.U_csr.indices
        data_U = self.U_csr.data
        diag_U = self.diag_U

        for i in range(m - 1, -1, -1):
            start = indptr_U[i]
            end = indptr_U[i + 1]
            cols = indices_U[start:end]
            vals = data_U[start:end]
            # Strictly upper triangular part (cols > i)
            mask = cols > i
            if np.any(mask):
                dot_val = np.dot(vals[mask], z[cols[mask]])
                z[i] = (y[i] - dot_val) / diag_U[i]
            else:
                z[i] = y[i] / diag_U[i]

        # 4. Inverse column permutation: x = Q z
        x = np.empty(m, dtype=np.float64)
        x[self.q_perm] = z
        return x

    def solve_transpose(self, rhs: np.ndarray, refine: bool = True, max_refine: int = 2, tol: float = 1e-12) -> tuple[np.ndarray, float, float, int]:
        """Solve B^T y = rhs (BTRAN) using sparse factors B^T = Q U^T L^T P.

        Returns (y, initial_residual, final_residual, refinement_steps).
        """
        c = np.asarray(rhs, dtype=np.float64)
        m = self.m
        if c.shape != (m,):
            raise NumericalError(f"RHS dimension mismatch: expected ({m},), got {c.shape}")

        y0 = self._raw_solve_transpose(c)

        # Iterative refinement
        init_res = float(np.max(np.abs(c - self.original_matrix.rmatvec(y0)), initial=0.0))
        cur_res = init_res
        refine_steps = 0
        y = y0.copy()

        rhs_norm = float(np.max(np.abs(c), initial=1.0))
        target_res = tol * (1.0 + rhs_norm)

        if refine and cur_res > target_res:
            for step in range(max_refine):
                if PLATFORM_LONGDOUBLE_EXTENDED:
                    r = np.asarray(np.asarray(c, np.longdouble) - self.original_matrix.rmatvec(y).astype(np.longdouble), dtype=np.float64)
                else:
                    r = c - self.original_matrix.rmatvec(y)

                res_norm = float(np.max(np.abs(r), initial=0.0))
                if res_norm <= target_res:
                    break

                corr = self._raw_solve_transpose(r)
                y += corr
                refine_steps += 1
                cur_res = float(np.max(np.abs(c - self.original_matrix.rmatvec(y)), initial=0.0))
                if cur_res <= target_res:
                    break

        if not np.all(np.isfinite(y)):
            raise NumericalError("Non-finite solution produced in sparse LU transpose solve")

        return y, init_res, cur_res, refine_steps

    def _raw_solve_transpose(self, c: np.ndarray) -> np.ndarray:
        """Raw solve for B^T y = c: Q U^T L^T P y = c <=> U^T L^T (P y) = Q^T c."""
        m = self.m
        # 1. Permute RHS by Q^T: c_tilde = Q^T c
        c_tilde = c[self.q_perm]

        # 2. Forward solve with U^T: U^T w = c_tilde
        # Since U is upper triangular in CSR, U^T is lower triangular in CSC!
        # Column j of U corresponds to row j of U^T
        w = np.zeros(m, dtype=np.float64)
        indptr_U = self.U_csc.indptr
        indices_U = self.U_csc.indices
        data_U = self.U_csc.data
        diag_U = self.diag_U

        for j in range(m):
            start = indptr_U[j]
            end = indptr_U[j + 1]
            rows = indices_U[start:end]
            vals = data_U[start:end]
            # Off-diagonal lower triangular elements (rows < j in U^T <=> row < j in U)
            mask = rows < j
            if np.any(mask):
                dot_val = np.dot(vals[mask], w[rows[mask]])
                w[j] = (c_tilde[j] - dot_val) / diag_U[j]
            else:
                w[j] = c_tilde[j] / diag_U[j]

        # 3. Backward solve with unit upper triangular L^T: L^T v = w
        # L is unit lower triangular in CSR, so L^T is unit upper triangular in CSC.
        # Column j of L corresponds to row j of L^T.
        v = np.zeros(m, dtype=np.float64)
        indptr_L = self.L_csc.indptr
        indices_L = self.L_csc.indices
        data_L = self.L_csc.data

        for j in range(m - 1, -1, -1):
            start = indptr_L[j]
            end = indptr_L[j + 1]
            rows = indices_L[start:end]
            vals = data_L[start:end]
            # Off-diagonal upper triangular elements (row > j in L <=> col > j in L^T)
            mask = rows > j
            if np.any(mask):
                dot_val = np.dot(vals[mask], v[rows[mask]])
                v[j] = w[j] - dot_val
            else:
                v[j] = w[j]

        # 4. Inverse row permutation: y = P^T v
        y = np.empty(m, dtype=np.float64)
        y[self.p_perm] = v
        return y


class SparseBasisEngine:
    """Manages basis factorization, Product-Form of Inverse (eta updates), and refactorizations.

    Maintains:
    B_k = B_0 E_1 E_2 ... E_k
    """

    def __init__(self,
                 max_eta_depth: int = 30,
                 pivot_threshold: float = 0.1,
                 min_pivot_mag: float = 1e-6,
                 residual_threshold: float = 1e-6):
        self.max_eta_depth = int(max_eta_depth)
        self.pivot_threshold = float(pivot_threshold)
        self.min_pivot_mag = float(min_pivot_mag)
        self.residual_threshold = float(residual_threshold)

        self.lu = SparseLU(u=self.pivot_threshold)
        self.etas: list[EtaVector] = []
        self.basis_indices: list[int] = []
        self.full_matrix: Optional[CSCMatrix] = None
        self.row_scales: Optional[np.ndarray] = None

        # Telemetry & diagnostics
        self.refactorizations = 0
        self.eta_updates = 0
        self.ftran_count = 0
        self.btran_count = 0
        self.observed_max_eta_depth = 0
        self.total_iterative_refinements = 0
        self.last_refactorization_reason = "INITIAL"
        self.refactorization_history: list[dict] = []

    def initialize(self, full_matrix: CSCMatrix, basis_indices: list[int], row_scales: Optional[np.ndarray] = None) -> None:
        """Factorize initial basis matrix B_0."""
        self.full_matrix = full_matrix
        self.basis_indices = list(basis_indices)
        self.row_scales = row_scales
        self.etas.clear()

        self._do_refactorization(reason="INITIAL")

    def _do_refactorization(self, reason: str) -> None:
        """Extract current basis columns and compute full sparse LU factorization."""
        B_csc = self.full_matrix.extract_columns(self.basis_indices)

        self.lu.factorize(B_csc)
        self.etas.clear()
        self.refactorizations += 1
        self.last_refactorization_reason = reason
        self.refactorization_history.append({
            'refactorization_id': self.refactorizations,
            'reason': reason,
            'basis_nnz': B_csc.nnz,
            'basis_density': B_csc.density,
            'growth_factor': self.lu.growth_factor
        })

    def ftran(self, rhs: np.ndarray, check_residual: bool = True) -> np.ndarray:
        """FTRAN: Solve B_k x = rhs via base solve + forward eta sweep."""
        self.ftran_count += 1
        # 1. Base solve: x_0 = B_0^{-1} rhs
        x, _, final_res, ref_steps = self.lu.solve(rhs)
        self.total_iterative_refinements += ref_steps

        # 2. Forward eta sweep: x_j = E_j^{-1} x_{j-1}
        for eta_vec in self.etas:
            p = eta_vec.pos
            alpha = eta_vec.pivot_val
            s = x[p] / alpha
            x[p] = s
            # x[i] -= s * eta[i] for i != p
            np.add.at(x, np.arange(len(x)), -s * eta_vec.eta)
            x[p] = s  # restore exact pivot position

        # Optional check for residual degradation on current basis
        if check_residual and len(self.etas) > 0:
            rhs_norm = float(np.max(np.abs(rhs), initial=1.0))
            if final_res > self.residual_threshold * rhs_norm:
                # Trigger refactorization on residual deterioration
                self._do_refactorization(reason="RESIDUAL_DETERIORATION")
                # Re-solve directly with new fresh basis factorization
                return self.ftran(rhs, check_residual=False)

        return x

    def btran(self, rhs: np.ndarray) -> np.ndarray:
        """BTRAN: Solve B_k^T y = rhs via backward eta sweep + base transpose solve."""
        self.btran_count += 1
        w = np.asarray(rhs, dtype=np.float64).copy()

        # 1. Backward eta sweep: w_{j-1} = E_j^{-T} w_j
        for eta_vec in reversed(self.etas):
            p = eta_vec.pos
            alpha = eta_vec.pivot_val
            # dot product of eta with w excluding position p
            dot_val = np.dot(eta_vec.eta, w) - eta_vec.eta[p] * w[p]
            w[p] = (w[p] - dot_val) / alpha

        # 2. Base transpose solve: y = B_0^{-T} w
        y, _, _, ref_steps = self.lu.solve_transpose(w)
        self.total_iterative_refinements += ref_steps
        return y

    def update(self, leaving_pos: int, entering_col: int, d_vector: np.ndarray) -> bool:
        """Update basis with new column: B_{k+1} = B_k E.

        leaving_pos: index in basis array (0 <= leaving_pos < m) that leaves.
        entering_col: column index in full_matrix entering basis.
        d_vector: FTRAN result of entering column (d = B_k^{-1} a_entering).

        Returns True if update succeeded with eta vector; False if refactorization triggered.
        """
        p = int(leaving_pos)
        pivot_val = float(d_vector[p])
        leaving_col = self.basis_indices[p]

        # Update basis array
        self.basis_indices[p] = int(entering_col)

        # Check triggers for full refactorization
        if abs(pivot_val) < self.min_pivot_mag:
            self._do_refactorization(reason="SMALL_PIVOT")
            return False

        if len(self.etas) >= self.max_eta_depth:
            self._do_refactorization(reason="ETA_LIMIT")
            return False

        # Add eta vector
        eta_vec = EtaVector(
            pos=p,
            eta=d_vector.copy(),
            pivot_val=pivot_val,
            entering_col=entering_col,
            leaving_col=leaving_col
        )
        self.etas.append(eta_vec)
        self.eta_updates += 1
        depth = len(self.etas)
        if depth > self.observed_max_eta_depth:
            self.observed_max_eta_depth = depth

        return True

    def force_refactorization(self) -> None:
        """Forced refactorization for testing or external trigger."""
        self._do_refactorization(reason="FORCED")

    def get_telemetry(self) -> dict:
        """Return diagnostic telemetry for LP results."""
        return {
            'basis_factorization': 'sovereign_sparse_lu_pfi',
            'sparse_basis_nnz': self.lu.original_matrix.nnz if self.lu.original_matrix else 0,
            'sparse_basis_density': self.lu.original_matrix.density if self.lu.original_matrix else 0.0,
            'refactorizations': self.refactorizations,
            'eta_updates': self.eta_updates,
            'ftran_count': self.ftran_count,
            'btran_count': self.btran_count,
            'max_eta_depth': self.observed_max_eta_depth,
            'iterative_refinement_steps': self.total_iterative_refinements,
            'last_refactorization_reason': self.last_refactorization_reason,
            'growth_factor': self.lu.growth_factor if self.lu else 1.0,
            'platform_longdouble_extended': PLATFORM_LONGDOUBLE_EXTENDED,
        }
