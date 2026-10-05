"""Sovereign Compressed Sparse Row (CSR) and Compressed Sparse Column (CSC) matrices.

Dependencies: Python standard library and NumPy only.
Strictly prohibited: scipy.sparse, SuiteSparse, UMFPACK, or any external library.

Provides:
- CSRMatrix: 0-based compressed sparse row representation.
- CSCMatrix: 0-based compressed sparse column representation.
- csr_from_dense, csc_from_dense: controlled conversion from dense arrays.
- csr_from_triplets, csc_from_triplets: construction from row/col/val coordinate lists.
"""
from __future__ import annotations
import numpy as np


class SparseShapeError(ValueError):
    """Raised when sparse matrix dimensions or vector dimensions mismatch."""
    pass


class SparseIndexError(IndexError):
    """Raised when sparse matrix indices are out of valid bounds."""
    pass


class CSRMatrix:
    """Sovereign Compressed Sparse Row matrix.

    Fields:
      n_rows: int, number of rows (m).
      n_cols: int, number of columns (n).
      indptr: np.ndarray (int64), length m + 1, non-decreasing row pointers starting at 0.
      indices: np.ndarray (int64), length nnz, column indices for each stored nonzero.
      data: np.ndarray (float64), length nnz, non-zero values.
    """

    __slots__ = ('n_rows', 'n_cols', 'indptr', 'indices', 'data')

    def __init__(self, *args, n_rows: int | None = None, n_cols: int | None = None,
                 indptr: np.ndarray | None = None, indices: np.ndarray | None = None, data: np.ndarray | None = None,
                 row_ptr: np.ndarray | None = None, col_idx: np.ndarray | None = None, values: np.ndarray | None = None,
                 shape: tuple[int, int] | None = None, validate: bool = True):
        # Handle positional args: (n_rows, n_cols, indptr, indices, data)
        if len(args) >= 5:
            n_rows, n_cols, indptr, indices, data = args[:5]
        elif len(args) == 3:
            # (row_ptr, col_idx, values)
            row_ptr, col_idx, values = args[:3]

        if row_ptr is not None:
            indptr = row_ptr
        if col_idx is not None:
            indices = col_idx
        if values is not None:
            data = values

        if shape is not None:
            n_rows, n_cols = shape
        elif n_rows is None or n_cols is None:
            if indptr is not None:
                n_rows = len(indptr) - 1
            if indices is not None and len(indices) > 0:
                n_cols = int(np.max(indices)) + 1
            else:
                n_cols = 0

        self.n_rows = int(n_rows)
        self.n_cols = int(n_cols)
        self.indptr = np.asarray(indptr, dtype=np.int64)
        self.indices = np.asarray(indices, dtype=np.int64)
        self.data = np.asarray(data, dtype=np.float64)

        if validate:
            self.validate()

    def __len__(self) -> int:
        return self.n_rows

    def __getitem__(self, key: int | tuple[int, int]) -> float | np.ndarray:
        """Indexed access: A[i, j] returns scalar value; A[i] returns dense 1D row."""
        if isinstance(key, tuple):
            if len(key) != 2:
                raise IndexError("CSRMatrix 2D indexing requires (row, col)")
            i, j = key
            if not (0 <= i < self.n_rows):
                raise IndexError(f"Row index {i} out of bounds for matrix with {self.n_rows} rows")
            if not (0 <= j < self.n_cols):
                raise IndexError(f"Column index {j} out of bounds for matrix with {self.n_cols} cols")
            start = self.indptr[i]
            end = self.indptr[i + 1]
            if start == end:
                return 0.0
            cols = self.indices[start:end]
            idx = np.searchsorted(cols, j)
            if idx < len(cols) and cols[idx] == j:
                return float(self.data[start + idx])
            return 0.0
        elif isinstance(key, (int, np.integer)):
            i = int(key)
            if not (0 <= i < self.n_rows):
                raise IndexError(f"Row index {i} out of bounds for matrix with {self.n_rows} rows")
            row = np.zeros(self.n_cols, dtype=np.float64)
            cols, vals = self.get_row(i)
            row[cols] = vals
            return row
        else:
            raise TypeError(f"Invalid index type for CSRMatrix: {type(key)}")

    @property
    def shape(self) -> tuple[int, int]:
        return (self.n_rows, self.n_cols)

    @property
    def nnz(self) -> int:
        return len(self.data)

    @property
    def density(self) -> float:
        total = self.n_rows * self.n_cols
        return (self.nnz / total) if total > 0 else 0.0

    @property
    def row_ptr(self) -> np.ndarray:
        return self.indptr

    @property
    def col_idx(self) -> np.ndarray:
        return self.indices

    @property
    def values(self) -> np.ndarray:
        return self.data

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    @property
    def memory_bytes(self) -> int:
        """Estimated memory footprint of CSR data structures in bytes."""
        return int(self.indptr.nbytes + self.indices.nbytes + self.data.nbytes)

    def validate(self) -> None:
        """Validate structure, monotonically increasing pointers, and index bounds."""
        if self.n_rows < 0 or self.n_cols < 0:
            raise SparseShapeError(f"Matrix dimensions must be non-negative, got ({self.n_rows}, {self.n_cols})")
        if len(self.indptr) != self.n_rows + 1:
            raise SparseShapeError(f"indptr length must be n_rows + 1 ({self.n_rows + 1}), got {len(self.indptr)}")
        if self.indptr[0] != 0:
            raise SparseShapeError(f"indptr[0] must be 0, got {self.indptr[0]}")
        if len(self.indices) != len(self.data):
            raise SparseShapeError(f"indices length ({len(self.indices)}) must match data length ({len(self.data)})")
        if self.indptr[-1] != len(self.data):
            raise SparseShapeError(f"indptr[-1] ({self.indptr[-1]}) must equal data length ({len(self.data)})")

        # Check monotonicity
        diffs = np.diff(self.indptr)
        if np.any(diffs < 0):
            raise SparseShapeError("indptr must be non-decreasing")

        # Check index bounds
        if len(self.indices) > 0:
            if np.min(self.indices) < 0 or np.max(self.indices) >= self.n_cols:
                raise SparseIndexError(f"indices contains elements outside [0, {self.n_cols - 1}]")

        # Check monotonicity of column indices within each row
        for r in range(self.n_rows):
            start = self.indptr[r]
            end = self.indptr[r + 1]
            if end - start > 1:
                row_cols = self.indices[start:end]
                if np.any(np.diff(row_cols) <= 0):
                    raise ValueError(f"Column indices within row {r} must be strictly increasing")

        if not np.all(np.isfinite(self.data)):
            raise ValueError("CSR data contains non-finite entries (NaN or Inf)")

    def copy(self) -> CSRMatrix:
        return CSRMatrix(self.n_rows, self.n_cols,
                         self.indptr.copy(), self.indices.copy(), self.data.copy(),
                         validate=False)

    def dot(self, x: np.ndarray, out: np.ndarray | None = None) -> np.ndarray:
        """Compute y = A @ x (shape m), optionally writing into out."""
        x_arr = np.asarray(x, dtype=np.float64)
        if x_arr.shape != (self.n_cols,):
            raise SparseShapeError(f"dot dimension mismatch: matrix has {self.n_cols} cols, x has shape {x_arr.shape}")

        if out is None:
            out = np.zeros(self.n_rows, dtype=np.float64)
        else:
            out.fill(0.0)

        indptr = self.indptr
        indices = self.indices
        data = self.data

        for i in range(self.n_rows):
            start = indptr[i]
            end = indptr[i + 1]
            if start < end:
                out[i] = np.dot(data[start:end], x_arr[indices[start:end]])
        return out

    def matvec(self, x: np.ndarray) -> np.ndarray:
        """Compute y = A @ x (shape m). Alias for dot(x)."""
        return self.dot(x)

    def transpose_dot(self, y: np.ndarray, out: np.ndarray | None = None) -> np.ndarray:
        """Compute x = A.T @ y (shape n), optionally writing into out."""
        y_arr = np.asarray(y, dtype=np.float64)
        if y_arr.shape != (self.n_rows,):
            raise SparseShapeError(f"transpose_dot dimension mismatch: matrix has {self.n_rows} rows, y has shape {y_arr.shape}")

        if out is None:
            out = np.zeros(self.n_cols, dtype=np.float64)
        else:
            out.fill(0.0)

        indptr = self.indptr
        indices = self.indices
        data = self.data

        for i in range(self.n_rows):
            start = indptr[i]
            end = indptr[i + 1]
            if start < end:
                val = y_arr[i]
                if val != 0.0:
                    np.add.at(out, indices[start:end], data[start:end] * val)
        return out

    def rmatvec(self, y: np.ndarray) -> np.ndarray:
        """Compute x = A.T @ y (shape n). Alias for transpose_dot(y)."""
        return self.transpose_dot(y)

    def abs_dot(self, x: np.ndarray, out: np.ndarray | None = None) -> np.ndarray:
        """Compute y = |A| @ x (shape m), optionally writing into out."""
        x_arr = np.asarray(x, dtype=np.float64)
        if x_arr.shape != (self.n_cols,):
            raise SparseShapeError(f"abs_dot dimension mismatch: matrix has {self.n_cols} cols, x has shape {x_arr.shape}")

        if out is None:
            out = np.zeros(self.n_rows, dtype=np.float64)
        else:
            out.fill(0.0)

        indptr = self.indptr
        indices = self.indices
        abs_data = np.abs(self.data)

        for i in range(self.n_rows):
            start = indptr[i]
            end = indptr[i + 1]
            if start < end:
                out[i] = np.dot(abs_data[start:end], x_arr[indices[start:end]])
        return out

    def abs_transpose_dot(self, y: np.ndarray, out: np.ndarray | None = None) -> np.ndarray:
        """Compute x = |A|^T @ y (shape n), optionally writing into out."""
        y_arr = np.asarray(y, dtype=np.float64)
        if y_arr.shape != (self.n_rows,):
            raise SparseShapeError(f"abs_transpose_dot dimension mismatch: matrix has {self.n_rows} rows, y has shape {y_arr.shape}")

        if out is None:
            out = np.zeros(self.n_cols, dtype=np.float64)
        else:
            out.fill(0.0)

        indptr = self.indptr
        indices = self.indices
        abs_data = np.abs(self.data)

        for i in range(self.n_rows):
            start = indptr[i]
            end = indptr[i + 1]
            if start < end:
                val = y_arr[i]
                if val != 0.0:
                    np.add.at(out, indices[start:end], abs_data[start:end] * val)
        return out

    def transpose(self) -> CSRMatrix:
        """Return transpose A.T as a canonical CSRMatrix in O(nnz) without dense conversion."""
        csc = self.to_csc()
        return CSRMatrix(self.n_cols, self.n_rows, csc.indptr, csc.indices, csc.data, validate=False)

    def row_sums(self, abs_vals: bool = False) -> np.ndarray:
        """Compute row sums in O(nnz)."""
        d = np.abs(self.data) if abs_vals else self.data
        sums = np.zeros(self.n_rows, dtype=np.float64)
        indptr = self.indptr
        for i in range(self.n_rows):
            start = indptr[i]
            end = indptr[i + 1]
            if start < end:
                sums[i] = np.sum(d[start:end])
        return sums

    def col_sums(self, abs_vals: bool = False) -> np.ndarray:
        """Compute column sums in O(nnz)."""
        d = np.abs(self.data) if abs_vals else self.data
        if len(d) == 0:
            return np.zeros(self.n_cols, dtype=np.float64)
        return np.bincount(self.indices, weights=d, minlength=self.n_cols).astype(np.float64)

    def get_row(self, i: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (col_indices, values) for row i."""
        if not (0 <= i < self.n_rows):
            raise SparseIndexError(f"Row index {i} out of bounds for matrix with {self.n_rows} rows")
        start = self.indptr[i]
        end = self.indptr[i + 1]
        return self.indices[start:end].copy(), self.data[start:end].copy()

    def get_col(self, j: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (row_indices, values) for column j."""
        if not (0 <= j < self.n_cols):
            raise SparseIndexError(f"Column index {j} out of bounds for matrix with {self.n_cols} cols")
        # Search rows
        row_indices = []
        values = []
        for i in range(self.n_rows):
            start = self.indptr[i]
            end = self.indptr[i + 1]
            idx_in_row = np.where(self.indices[start:end] == j)[0]
            if len(idx_in_row) > 0:
                row_indices.append(i)
                values.append(self.data[start + idx_in_row[0]])
        return np.array(row_indices, dtype=np.int64), np.array(values, dtype=np.float64)

    def drop_zeros(self, tol: float = 1e-15) -> CSRMatrix:
        """Return a new CSRMatrix with entries |val| <= tol removed."""
        mask = np.abs(self.data) > tol
        if np.all(mask):
            return self.copy()

        new_data = self.data[mask]
        new_indices = self.indices[mask]
        new_indptr = np.zeros(self.n_rows + 1, dtype=np.int64)

        for i in range(self.n_rows):
            start = self.indptr[i]
            end = self.indptr[i + 1]
            new_indptr[i + 1] = new_indptr[i] + np.sum(mask[start:end])

        return CSRMatrix(self.n_rows, self.n_cols, new_indptr, new_indices, new_data, validate=False)

    def sort_indices(self) -> CSRMatrix:
        """Return a new CSRMatrix where column indices in each row are strictly sorted ascending."""
        new_indices = self.indices.copy()
        new_data = self.data.copy()

        for i in range(self.n_rows):
            start = self.indptr[i]
            end = self.indptr[i + 1]
            if end - start > 1:
                row_cols = new_indices[start:end]
                order = np.argsort(row_cols)
                new_indices[start:end] = row_cols[order]
                new_data[start:end] = new_data[start:end][order]

        return CSRMatrix(self.n_rows, self.n_cols, self.indptr.copy(), new_indices, new_data, validate=False)

    def sum_duplicates(self) -> CSRMatrix:
        """Combine duplicate (row, col) entries by summing their values and sorting column indices."""
        # Convert to triplets and reconstruct
        if self.nnz == 0:
            return self.copy()

        rows = np.repeat(np.arange(self.n_rows, dtype=np.int64), np.diff(self.indptr))
        return csr_from_triplets(self.n_rows, self.n_cols, rows, self.indices, self.data, sum_dups=True)

    def to_dense(self) -> np.ndarray:
        """Convert to dense 2D numpy array. For test verification and small-scale fallback only."""
        dense = np.zeros((self.n_rows, self.n_cols), dtype=np.float64)
        for i in range(self.n_rows):
            start = self.indptr[i]
            end = self.indptr[i + 1]
            dense[i, self.indices[start:end]] = self.data[start:end]
        return dense

    def to_csc(self) -> CSCMatrix:
        """Convert CSR to CSC in linear time without external libraries."""
        if self.nnz == 0:
            return CSCMatrix(self.n_rows, self.n_cols,
                             np.zeros(self.n_cols + 1, dtype=np.int64),
                             np.zeros(0, dtype=np.int64),
                             np.zeros(0, dtype=np.float64),
                             validate=False)

        rows = np.repeat(np.arange(self.n_rows, dtype=np.int64), np.diff(self.indptr))
        col_counts = np.bincount(self.indices, minlength=self.n_cols)
        csc_indptr = np.zeros(self.n_cols + 1, dtype=np.int64)
        csc_indptr[1:] = np.cumsum(col_counts)

        csc_indices = np.zeros(self.nnz, dtype=np.int64)
        csc_data = np.zeros(self.nnz, dtype=np.float64)
        next_pos = csc_indptr[:-1].copy()

        for k in range(self.nnz):
            col = self.indices[k]
            dest = next_pos[col]
            csc_indices[dest] = rows[k]
            csc_data[dest] = self.data[k]
            next_pos[col] += 1

        res = CSCMatrix(self.n_rows, self.n_cols, csc_indptr, csc_indices, csc_data, validate=False)
        return res.sort_indices()

    def extract_columns(self, col_indices: list[int] | np.ndarray) -> CSRMatrix:
        """Extract a subset of columns directly into a new CSRMatrix without dense conversion."""
        cols = np.asarray(col_indices, dtype=np.int64)
        k_cols = len(cols)

        # Mapping from original column index to new column position(s)
        # Note: In standard simplex, basis indices are unique columns
        col_map = {int(c): idx for idx, c in enumerate(cols)}

        new_indptr = [0]
        new_indices_list = []
        new_data_list = []

        for i in range(self.n_rows):
            start = self.indptr[i]
            end = self.indptr[i + 1]
            row_cols = self.indices[start:end]
            row_vals = self.data[start:end]

            for c, val in zip(row_cols, row_vals):
                if c in col_map:
                    new_indices_list.append(col_map[c])
                    new_data_list.append(val)
            new_indptr.append(len(new_indices_list))

        res = CSRMatrix(self.n_rows, k_cols,
                        np.array(new_indptr, dtype=np.int64),
                        np.array(new_indices_list, dtype=np.int64),
                        np.array(new_data_list, dtype=np.float64),
                        validate=False)
        return res.sort_indices()


class CSCMatrix:
    """Sovereign Compressed Sparse Column matrix.

    Fields:
      n_rows: int, number of rows (m).
      n_cols: int, number of columns (n).
      indptr: np.ndarray (int64), length n + 1, non-decreasing col pointers starting at 0.
      indices: np.ndarray (int64), length nnz, row indices for each stored nonzero.
      data: np.ndarray (float64), length nnz, non-zero values.
    """

    __slots__ = ('n_rows', 'n_cols', 'indptr', 'indices', 'data')

    def __init__(self, n_rows: int, n_cols: int, indptr: np.ndarray, indices: np.ndarray, data: np.ndarray,
                 validate: bool = True):
        self.n_rows = int(n_rows)
        self.n_cols = int(n_cols)
        self.indptr = np.asarray(indptr, dtype=np.int64)
        self.indices = np.asarray(indices, dtype=np.int64)
        self.data = np.asarray(data, dtype=np.float64)

        if validate:
            self.validate()

    def __len__(self) -> int:
        return self.n_rows

    def __getitem__(self, key: int | tuple[int, int]) -> float | np.ndarray:
        """Indexed access: A[i, j] returns scalar value; A[j] returns dense 1D column."""
        if isinstance(key, tuple):
            if len(key) != 2:
                raise IndexError("CSCMatrix 2D indexing requires (row, col)")
            i, j = key
            if not (0 <= i < self.n_rows):
                raise IndexError(f"Row index {i} out of bounds for matrix with {self.n_rows} rows")
            if not (0 <= j < self.n_cols):
                raise IndexError(f"Column index {j} out of bounds for matrix with {self.n_cols} cols")
            start = self.indptr[j]
            end = self.indptr[j + 1]
            if start == end:
                return 0.0
            rows = self.indices[start:end]
            idx = np.searchsorted(rows, i)
            if idx < len(rows) and rows[idx] == i:
                return float(self.data[start + idx])
            return 0.0
        elif isinstance(key, (int, np.integer)):
            j = int(key)
            if not (0 <= j < self.n_cols):
                raise IndexError(f"Column index {j} out of bounds for matrix with {self.n_cols} cols")
            col = np.zeros(self.n_rows, dtype=np.float64)
            rows, vals = self.get_col(j)
            col[rows] = vals
            return col
        else:
            raise TypeError(f"Invalid index type for CSCMatrix: {type(key)}")

    @property
    def shape(self) -> tuple[int, int]:
        return (self.n_rows, self.n_cols)

    @property
    def nnz(self) -> int:
        return len(self.data)

    @property
    def density(self) -> float:
        total = self.n_rows * self.n_cols
        return (self.nnz / total) if total > 0 else 0.0

    @property
    def col_ptr(self) -> np.ndarray:
        return self.indptr

    @property
    def row_idx(self) -> np.ndarray:
        return self.indices

    @property
    def values(self) -> np.ndarray:
        return self.data

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    @property
    def memory_bytes(self) -> int:
        """Estimated memory footprint of CSC data structures in bytes."""
        return int(self.indptr.nbytes + self.indices.nbytes + self.data.nbytes)

    def validate(self) -> None:
        """Validate structure, monotonically increasing pointers, and index bounds."""
        if self.n_rows < 0 or self.n_cols < 0:
            raise SparseShapeError(f"Matrix dimensions must be non-negative, got ({self.n_rows}, {self.n_cols})")
        if len(self.indptr) != self.n_cols + 1:
            raise SparseShapeError(f"indptr length must be n_cols + 1 ({self.n_cols + 1}), got {len(self.indptr)}")
        if self.indptr[0] != 0:
            raise SparseShapeError(f"indptr[0] must be 0, got {self.indptr[0]}")
        if len(self.indices) != len(self.data):
            raise SparseShapeError(f"indices length ({len(self.indices)}) must match data length ({len(self.data)})")
        if self.indptr[-1] != len(self.data):
            raise SparseShapeError(f"indptr[-1] ({self.indptr[-1]}) must equal data length ({len(self.data)})")

        diffs = np.diff(self.indptr)
        if np.any(diffs < 0):
            raise SparseShapeError("indptr must be non-decreasing")

        if len(self.indices) > 0:
            if np.min(self.indices) < 0 or np.max(self.indices) >= self.n_rows:
                raise SparseIndexError(f"indices contains elements outside [0, {self.n_rows - 1}]")

        if not np.all(np.isfinite(self.data)):
            raise ValueError("CSC data contains non-finite entries (NaN or Inf)")

    def copy(self) -> CSCMatrix:
        return CSCMatrix(self.n_rows, self.n_cols,
                         self.indptr.copy(), self.indices.copy(), self.data.copy(),
                         validate=False)

    def matvec(self, x: np.ndarray) -> np.ndarray:
        """Compute y = A @ x (shape m) via column accumulation."""
        x_arr = np.asarray(x, dtype=np.float64)
        if x_arr.shape != (self.n_cols,):
            raise SparseShapeError(f"matvec dimension mismatch: matrix has {self.n_cols} cols, x has shape {x_arr.shape}")

        y = np.zeros(self.n_rows, dtype=np.float64)
        indptr = self.indptr
        indices = self.indices
        data = self.data

        for j in range(self.n_cols):
            xj = x_arr[j]
            if xj != 0.0:
                start = indptr[j]
                end = indptr[j + 1]
                if start < end:
                    np.add.at(y, indices[start:end], data[start:end] * xj)
        return y

    def rmatvec(self, y: np.ndarray) -> np.ndarray:
        """Compute x = A.T @ y (shape n) via column dot products."""
        y_arr = np.asarray(y, dtype=np.float64)
        if y_arr.shape != (self.n_rows,):
            raise SparseShapeError(f"rmatvec dimension mismatch: matrix has {self.n_rows} rows, y has shape {y_arr.shape}")

        x = np.zeros(self.n_cols, dtype=np.float64)
        indptr = self.indptr
        indices = self.indices
        data = self.data

        for j in range(self.n_cols):
            start = indptr[j]
            end = indptr[j + 1]
            if start < end:
                x[j] = np.dot(data[start:end], y_arr[indices[start:end]])
        return x

    def get_col(self, j: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (row_indices, values) for column j in O(1) slice."""
        if not (0 <= j < self.n_cols):
            raise SparseIndexError(f"Column index {j} out of bounds for matrix with {self.n_cols} cols")
        start = self.indptr[j]
        end = self.indptr[j + 1]
        return self.indices[start:end].copy(), self.data[start:end].copy()

    def get_row(self, i: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (col_indices, values) for row i."""
        if not (0 <= i < self.n_rows):
            raise SparseIndexError(f"Row index {i} out of bounds for matrix with {self.n_rows} rows")
        cols = []
        vals = []
        for j in range(self.n_cols):
            start = self.indptr[j]
            end = self.indptr[j + 1]
            pos = np.where(self.indices[start:end] == i)[0]
            if len(pos) > 0:
                cols.append(j)
                vals.append(self.data[start + pos[0]])
        return np.array(cols, dtype=np.int64), np.array(vals, dtype=np.float64)

    def drop_zeros(self, tol: float = 1e-15) -> CSCMatrix:
        """Return a new CSCMatrix with entries |val| <= tol removed."""
        mask = np.abs(self.data) > tol
        if np.all(mask):
            return self.copy()

        new_data = self.data[mask]
        new_indices = self.indices[mask]
        new_indptr = np.zeros(self.n_cols + 1, dtype=np.int64)

        for j in range(self.n_cols):
            start = self.indptr[j]
            end = self.indptr[j + 1]
            new_indptr[j + 1] = new_indptr[j] + np.sum(mask[start:end])

        return CSCMatrix(self.n_rows, self.n_cols, new_indptr, new_indices, new_data, validate=False)

    def sort_indices(self) -> CSCMatrix:
        """Return a new CSCMatrix where row indices in each column are sorted ascending."""
        new_indices = self.indices.copy()
        new_data = self.data.copy()

        for j in range(self.n_cols):
            start = self.indptr[j]
            end = self.indptr[j + 1]
            if end - start > 1:
                col_rows = new_indices[start:end]
                order = np.argsort(col_rows)
                new_indices[start:end] = col_rows[order]
                new_data[start:end] = new_data[start:end][order]

        return CSCMatrix(self.n_rows, self.n_cols, self.indptr.copy(), new_indices, new_data, validate=False)

    def sum_duplicates(self) -> CSCMatrix:
        """Combine duplicate (row, col) entries by summing their values and sorting row indices."""
        if self.nnz == 0:
            return self.copy()

        cols = np.repeat(np.arange(self.n_cols, dtype=np.int64), np.diff(self.indptr))
        return csc_from_triplets(self.n_rows, self.n_cols, self.indices, cols, self.data, sum_dups=True)

    def to_dense(self) -> np.ndarray:
        """Convert to dense 2D numpy array. For test verification and small-scale fallback only."""
        dense = np.zeros((self.n_rows, self.n_cols), dtype=np.float64)
        for j in range(self.n_cols):
            start = self.indptr[j]
            end = self.indptr[j + 1]
            dense[self.indices[start:end], j] = self.data[start:end]
        return dense

    def to_csr(self) -> CSRMatrix:
        """Convert CSC to CSR in linear time without external libraries."""
        if self.nnz == 0:
            return CSRMatrix(self.n_rows, self.n_cols,
                             np.zeros(self.n_rows + 1, dtype=np.int64),
                             np.zeros(0, dtype=np.int64),
                             np.zeros(0, dtype=np.float64),
                             validate=False)

        cols = np.repeat(np.arange(self.n_cols, dtype=np.int64), np.diff(self.indptr))
        row_counts = np.bincount(self.indices, minlength=self.n_rows)
        csr_indptr = np.zeros(self.n_rows + 1, dtype=np.int64)
        csr_indptr[1:] = np.cumsum(row_counts)

        csr_indices = np.zeros(self.nnz, dtype=np.int64)
        csr_data = np.zeros(self.nnz, dtype=np.float64)
        next_pos = csr_indptr[:-1].copy()

        for k in range(self.nnz):
            row = self.indices[k]
            dest = next_pos[row]
            csr_indices[dest] = cols[k]
            csr_data[dest] = self.data[k]
            next_pos[row] += 1

        res = CSRMatrix(self.n_rows, self.n_cols, csr_indptr, csr_indices, csr_data, validate=False)
        return res.sort_indices()

    def extract_columns(self, col_indices: list[int] | np.ndarray) -> CSCMatrix:
        """Extract a subset of columns directly into a new CSCMatrix.

        In CSC format, column extraction is direct and requires zero search:
        slices [indptr[j]:indptr[j+1]] are concatenated directly!
        """
        cols = np.asarray(col_indices, dtype=np.int64)
        k_cols = len(cols)

        new_indptr = np.zeros(k_cols + 1, dtype=np.int64)
        slices_indices = []
        slices_data = []

        for idx, j in enumerate(cols):
            if not (0 <= j < self.n_cols):
                raise SparseIndexError(f"Column index {j} out of range [0, {self.n_cols - 1}]")
            start = self.indptr[j]
            end = self.indptr[j + 1]
            slices_indices.append(self.indices[start:end])
            slices_data.append(self.data[start:end])
            new_indptr[idx + 1] = new_indptr[idx] + (end - start)

        if len(slices_indices) > 0 and new_indptr[-1] > 0:
            new_indices = np.concatenate(slices_indices)
            new_data = np.concatenate(slices_data)
        else:
            new_indices = np.zeros(0, dtype=np.int64)
            new_data = np.zeros(0, dtype=np.float64)

        return CSCMatrix(self.n_rows, k_cols, new_indptr, new_indices, new_data, validate=False)


# ==============================================================================
# Sovereign Construction Helpers
# ==============================================================================

def csr_from_dense(A: np.ndarray, tol: float = 0.0) -> CSRMatrix:
    """Create a canonical CSRMatrix from a dense 2D numpy array."""
    arr = np.asarray(A, dtype=np.float64)
    if arr.ndim != 2:
        raise SparseShapeError(f"Dense array must be 2D, got shape {arr.shape}")
    m, n = arr.shape

    if tol > 0.0:
        rows, cols = np.nonzero(np.abs(arr) > tol)
    else:
        rows, cols = np.nonzero(arr != 0.0)

    data = arr[rows, cols]
    return csr_from_triplets(m, n, rows, cols, data, sum_dups=False, tol=tol)


def csc_from_dense(A: np.ndarray, tol: float = 0.0) -> CSCMatrix:
    """Create a canonical CSCMatrix from a dense 2D numpy array."""
    arr = np.asarray(A, dtype=np.float64)
    if arr.ndim != 2:
        raise SparseShapeError(f"Dense array must be 2D, got shape {arr.shape}")
    m, n = arr.shape

    if tol > 0.0:
        rows, cols = np.nonzero(np.abs(arr) > tol)
    else:
        rows, cols = np.nonzero(arr != 0.0)

    data = arr[rows, cols]
    return csc_from_triplets(m, n, rows, cols, data, sum_dups=False, tol=tol)


def csr_from_triplets(n_rows: int, n_cols: int,
                      rows: np.ndarray, cols: np.ndarray, data: np.ndarray,
                      sum_dups: bool = True, tol: float = 0.0) -> CSRMatrix:
    """Construct CSRMatrix from coordinate arrays (rows, cols, data).

    Deterministic: sorts column indices within each row ascending.
    If sum_dups is True, duplicate entries for the same (row, col) are summed.
    """
    m = int(n_rows)
    n = int(n_cols)
    r = np.asarray(rows, dtype=np.int64)
    c = np.asarray(cols, dtype=np.int64)
    d = np.asarray(data, dtype=np.float64)

    if len(r) != len(c) or len(r) != len(d):
        raise SparseShapeError(f"Triplets length mismatch: rows ({len(r)}), cols ({len(c)}), data ({len(d)})")

    if len(r) == 0:
        return CSRMatrix(m, n, np.zeros(m + 1, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64))

    # Filter out-of-bounds or zero entries if tol > 0
    if tol > 0.0:
        valid_mask = (r >= 0) & (r < m) & (c >= 0) & (c < n) & (np.abs(d) > tol)
    else:
        valid_mask = (r >= 0) & (r < m) & (c >= 0) & (c < n)

    if not np.all(valid_mask):
        r = r[valid_mask]
        c = c[valid_mask]
        d = d[valid_mask]

    if len(r) == 0:
        return CSRMatrix(m, n, np.zeros(m + 1, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64))

    # Lexicographical sort by (row, col)
    # Using 64-bit integer packing: key = row * n + col
    keys = r * n + c
    order = np.argsort(keys)
    r_sorted = r[order]
    c_sorted = c[order]
    d_sorted = d[order]

    if sum_dups:
        # Identify duplicates where key[k] == key[k-1]
        keys_sorted = keys[order]
        mask_unique = np.empty(len(keys_sorted), dtype=bool)
        mask_unique[0] = True
        mask_unique[1:] = (keys_sorted[1:] != keys_sorted[:-1])

        if not np.all(mask_unique):
            # Sum duplicates
            unique_indices = np.flatnonzero(mask_unique)
            n_unique = len(unique_indices)
            r_out = r_sorted[mask_unique]
            c_out = c_sorted[mask_unique]
            d_out = np.zeros(n_unique, dtype=np.float64)

            # Sum into d_out
            group_ids = np.cumsum(mask_unique) - 1
            np.add.at(d_out, group_ids, d_sorted)

            r_sorted = r_out
            c_sorted = c_out
            d_sorted = d_out

    # Build indptr via bincount
    row_counts = np.bincount(r_sorted, minlength=m)
    indptr = np.zeros(m + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(row_counts)

    return CSRMatrix(m, n, indptr, c_sorted, d_sorted, validate=False)


def csc_from_triplets(n_rows: int, n_cols: int,
                      rows: np.ndarray, cols: np.ndarray, data: np.ndarray,
                      sum_dups: bool = True, tol: float = 0.0) -> CSCMatrix:
    """Construct CSCMatrix from coordinate arrays (rows, cols, data).

    Deterministic: sorts row indices within each column ascending.
    If sum_dups is True, duplicate entries for the same (row, col) are summed.
    """
    m = int(n_rows)
    n = int(n_cols)
    r = np.asarray(rows, dtype=np.int64)
    c = np.asarray(cols, dtype=np.int64)
    d = np.asarray(data, dtype=np.float64)

    if len(r) != len(c) or len(r) != len(d):
        raise SparseShapeError(f"Triplets length mismatch: rows ({len(r)}), cols ({len(c)}), data ({len(d)})")

    if len(r) == 0:
        return CSCMatrix(m, n, np.zeros(n + 1, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64))

    if tol > 0.0:
        valid_mask = (r >= 0) & (r < m) & (c >= 0) & (c < n) & (np.abs(d) > tol)
    else:
        valid_mask = (r >= 0) & (r < m) & (c >= 0) & (c < n)

    if not np.all(valid_mask):
        r = r[valid_mask]
        c = c[valid_mask]
        d = d[valid_mask]

    if len(r) == 0:
        return CSCMatrix(m, n, np.zeros(n + 1, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64))

    # Lexicographical sort by (col, row)
    keys = c * m + r
    order = np.argsort(keys)
    r_sorted = r[order]
    c_sorted = c[order]
    d_sorted = d[order]

    if sum_dups:
        keys_sorted = keys[order]
        mask_unique = np.empty(len(keys_sorted), dtype=bool)
        mask_unique[0] = True
        mask_unique[1:] = (keys_sorted[1:] != keys_sorted[:-1])

        if not np.all(mask_unique):
            unique_indices = np.flatnonzero(mask_unique)
            n_unique = len(unique_indices)
            r_out = r_sorted[mask_unique]
            c_out = c_sorted[mask_unique]
            d_out = np.zeros(n_unique, dtype=np.float64)

            group_ids = np.cumsum(mask_unique) - 1
            np.add.at(d_out, group_ids, d_sorted)

            r_sorted = r_out
            c_sorted = c_out
            d_sorted = d_out

    col_counts = np.bincount(c_sorted, minlength=n)
    indptr = np.zeros(n + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(col_counts)

    return CSCMatrix(m, n, indptr, r_sorted, d_sorted, validate=False)
