# SOV-OPT Gate 20A — Sovereign True Sparse Core Architecture Audit

## 1. Executive Summary

Prior to Gate 20A, the SOV-OPT solver core enforced an arbitrary ceiling of $N \le 5,000$ variables
and materialized dense 2D NumPy arrays ($m \times n$) during several critical solver phases:
- Model validation (`(A != 0).sum()` densified sparse inputs)
- MPS ingestion (`read_mps` built dense Python lists `[[...]]`)
- Inequality canonicalization (`model.inequalities()` built dense 2D matrices)
- Verification (`verify.py` allocated $n \times n$ dense arrays even for continuous linear programs)
- Solvers (`pdhg.py` densified the constraint matrix $G$ before converting to sparse)

Gate 20A re-architects the entire sovereign solver pipeline around a native, zero-dependency
**True Sparse Matrix Contract** (`CSRMatrix` / `CSCMatrix`). All dense size bottlenecks and
arbitrary variable ceilings have been dismantled. The representation-aware guard permits models
up to configured structural limits ($10^7$ variables/rows), strictly subject to a deterministic
**2.0 GB sparse-memory budget**, with empirical representation and SpMV stress tested up to
1,000,000 variables $\times$ 500,000 rows.

---

## 2. Component-by-Component Dense vs Sparse Inventory

| Module | Prior Implementation (Gate 19B) | Gate 20A Sovereign True Sparse Implementation | Memory Complexity Change |
| :--- | :--- | :--- | :--- |
| **`sovopt/sparse.py`** | Basic CSC wrapper, limited transpose/dot, no in-place SpMV, missing `abs_dot` | Full sovereign `CSRMatrix` and `CSCMatrix` with in-place `dot()`, `transpose_dot()`, $O(nnz)$ `transpose()`, `abs_dot()`, `abs_transpose_dot()`, `row_sums()`, `col_sums()`, memory footprint estimation. | $O(m \cdot n) \to O(m + nnz)$ |
| **`sovopt/model.py`** | Required dense 2D `A`, arbitrary $N \le 5000$ cap, dense `inequalities()` | Native `CSRMatrix` support, $O(nnz)$ `sparse_inequalities()`, removed 5K limit, $10^7$ ceiling with $\le 2.0$ GB memory guard. | $O(m \cdot n) \to O(m + nnz)$ |
| **`sovopt/mps.py`** | Materialized dense Python list of lists for matrix $A$ | Streams lines, accumulates nonzeros in triplet lists, instantiates `CSRMatrix` directly. Streams `.bz2`, `.gz`, and text MPS. | $O(m \cdot n) \to O(nnz)$ |
| **`sovopt/pdhg.py`** | Called `model.inequalities()` (dense), then converted to CSR; dense transpose BLAS | Operates directly on `sparse_inequalities()` CSRMatrix, $O(nnz)$ preconditioning, pure SpMV/SpMV-T, zero dense buffers. | $O(m \cdot n) \to O(m + nnz)$ |
| **`sovopt/verify.py`** | Materialized dense $G$, allocated $n \times n$ zero matrix for $Q$ when $Q$ was `None` | Computes KKT residuals via sparse SpMV and SpMV-T, linear objective evaluated in $O(n)$ without $Q$ allocation. | $O(n^2) \to O(nnz)$ |
| **`sovopt/dual_simplex.py`** | Called `np.nonzero(A)` which materialized coordinates from dense $A$ | Directly extracts nonzeros from `CSRMatrix.indptr, indices, data` without densification. | $O(m \cdot n) \to O(nnz)$ |
| **`sovopt/dispatcher.py`** | Evaluated `(A != 0).sum()` triggering densification | Evaluates `A.nnz` if sparse, preserving sparse representation. | $O(m \cdot n) \to O(1)$ |

---

## 3. Sovereign True Sparse Matrix Contract Specification

### Class: `sovopt.sparse.CSRMatrix`
1. **Core Representation**:
   - `n_rows` ($m$), `n_cols` ($n$): Non-negative 64-bit integers.
   - `indptr` (`row_ptr`): 1D NumPy array (`int64`), length $m + 1$, monotonically non-decreasing, `indptr[0] == 0`, `indptr[m] == nnz`.
   - `indices` (`col_idx`): 1D NumPy array (`int64`), length $nnz$, strictly increasing within each row, entries in $[0, n - 1]$.
   - `data` (`values`): 1D NumPy array (`float64`), length $nnz$, finite binary64 floats.
2. **Memory Footprint**:
   $$\text{Memory Bytes} = 8 \cdot (m + 1) + 8 \cdot nnz + 8 \cdot nnz = 8 \cdot (m + 2 \cdot nnz + 1)$$
   - At 1,000,000 variables, 500,000 rows, and 2,500,000 nonzeros:
     $$\text{Sparse Memory} = 8 \cdot (500001 + 5000000) \approx 41.96\text{ MB}$$
     $$\text{Dense Memory} = 500,000 \times 1,000,000 \times 8 = 4,000,000,000,000\text{ bytes} \approx 3,725.29\text{ GB (3.7 TB)}$$
     $$\text{Compression Factor} = 90,909\times$$
3. **Sovereign Operations**:
   - `dot(x, out=None)`: Forward SpMV $y = A x$ in $O(nnz)$.
   - `transpose_dot(y, out=None)`: Adjoint SpMV $x = A^T y$ in $O(nnz)$ without explicit transposition.
   - `transpose()`: Exact $O(nnz)$ CSR-to-CSC/CSR transposition via count-sort.
   - `abs_dot(x)`: Evaluates $|A| x$ for exact componentwise KKT scaling.
   - `abs_transpose_dot(y)`: Evaluates $|A^T| y$ for dual stationarity scaling.
   - `row_sums(abs_vals=True)` / `col_sums(abs_vals=True)`: Preconditioning diagonal norms in $O(nnz)$.

---

## 4. CUDA / GPU Handoff Contract

The sovereign true sparse core is specifically structured for direct zero-copy / linear copy
handoff to GPU backends (`pdhg-cuda`):
- `indptr` (`int32` / `int64` pointer array directly compatible with `cusparseSpMV` and CuPy CSR)
- `indices` (`int32` / `int64` column indices array)
- `data` (`float64` values array)
- Zero memory re-layout required between CPU sparse representation and GPU sparse memory.

---

## 5. Capacity Ceiling Evolution

| Metric | Gate 18 Production Main | Gate 20A Sovereign True Sparse Core |
| :--- | :--- | :--- |
| **Configured Ceiling (LP Variables)** | 5,000 | **10,000,000 (10M)** *(structural limit)* |
| **Configured Ceiling (LP Rows)** | 5,000 | **10,000,000 (10M)** *(structural limit)* |
| **Demonstrated Representation Stress** | $\le 5,000$ variables | **1,000,000 variables $\times$ 500,000 rows** |
| **Theoretical Dense Limit at 1M** | $\sim 0.2$ GB ($5000 \times 5000$) | $> 3.7$ TB (Blocked by OS RAM) |
| **Actual Sovereign RAM Usage at 1M Scale** | Memory Error / Rejected | **41.96 MB** |
| **Memory Guard** | None (crashed on big inputs) | **Strict 2.0 GB Memory Guard** |
| **MPS Ingestion Mechanism** | Dense Python 2D lists | **Streaming Triplet-to-CSR** |
| **Verification Overhead** | Allocated $n \times n$ matrix | **$O(nnz)$ Sparse SpMV** |
