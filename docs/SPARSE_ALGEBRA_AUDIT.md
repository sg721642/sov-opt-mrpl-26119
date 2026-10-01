# Sparse Linear Algebra Audit — SOV-OPT Solver Core

**Audit Date:** 2026-10-01  
**Scope:** `sovopt/linalg.py`, `sovopt/simplex.py`, `sovopt/qp.py`, `sovopt/pdhg.py`, `sovopt/model.py`, `sovopt/transforms.py`  
**Milestone:** Gate 3 Baseline Assessment  

---

## 1. Executive Summary & Core Question

> **Question:** *Does any current production LP basis solve use sparse LU?*  
> **Answer:** **NO.**  
> Prior to Gate 3 implementation, all production LP basis solves in `sovopt/simplex.py` use the dense `LU` class from `sovopt/linalg.py`. At every single simplex pivot, the full $m \times m$ basis matrix is sliced as a dense NumPy 2D array, factorized from scratch using dense Gaussian elimination with row pivoting, and solved with dense forward/backward substitution. The basis matrix transpose $B^T$ is separately instantiated and factorized from scratch to compute pricing duals.

---

## 2. Dense Matrix Allocations Across Core Modules

| Module & Line | Operation | Allocation Shape | Description |
|:---|:---|:---:|:---|
| `sovopt/linalg.py:8` | `np.array(A, float, copy=True)` | $m \times m$ | Dense working matrix copy in `LU.__init__` |
| `sovopt/linalg.py:8` | `self.original.copy()` | $m \times m$ | Preserved original matrix for residual computation in iterative refinement |
| `sovopt/linalg.py:17` | `np.outer(self.a[k+1:,k], self.a[k,k+1:])` | $(m-k-1) \times (m-k-1)$ | Dense outer product Schur complement update during factorization |
| `sovopt/simplex.py:334` | `B = M[:, basis]` | $m \times m$ | Dense basis matrix extraction via NumPy 2D column indexing in `_iterate` |
| `sovopt/simplex.py:337` | `B.T` | $m \times m$ | Dense transpose basis matrix creation for dual pricing |
| `sovopt/simplex.py:598` | `M[:, basis].T` | $m \times m$ | Dense transpose basis extraction during artificial variable elimination |
| `sovopt/qp.py:78` | `G.T @ ((z / s)[:, None] * G)` | $n \times n$ | Dense normal equations matrix formulation |
| `sovopt/qp.py:80` | `K + reg * np.eye(n)` | $n \times n$ | Dense regularized KKT matrix passed to `LU` |
| `sovopt/transforms.py:83-84` | `A_eq = np.zeros((m_eq, n_trans))` | $m_{eq} \times n_{trans}$ | Dense transformed equality constraint matrix |
| `sovopt/transforms.py:85` | `A_le = np.zeros((m_le, n_trans))` | $m_{le} \times n_{trans}$ | Dense transformed inequality constraint matrix |

---

## 3. Basis Solves and Factorization Lifecycle

### 3.1 Every Dense LU Call Site in LP Simplex (`sovopt/simplex.py`)

1. **Primal Basic Solution ($B x_B = b$):**
   - **Call:** `lu = LU(B)` followed by `xb = lu.solve(b)` (`sovopt/simplex.py:335-336`).
   - **Frequency:** Called on **every single iteration** of Phase I and Phase II simplex.
   - **Mechanism:** Factorizes $m \times m$ dense matrix $B = M[:, \text{basis}]$.
2. **Dual Multipliers / Pricing ($B^T y = c_B$):**
   - **Call:** `y = LU(B.T).solve(c[basis])` (`sovopt/simplex.py:337`).
   - **Frequency:** Called on **every single iteration** of Phase I and Phase II simplex.
   - **Mechanism:** Inefficiently constructs $B^T$ as a new dense matrix and performs a **second independent dense LU factorization** $O(m^3)$ from scratch because the dense `LU` class lacks a `solve_transpose` method.
3. **FTRAN / Pivot Column Transformation ($B d = a_q$):**
   - **Call:** `d = lu.solve(M[:, entering])` (`sovopt/simplex.py:344`).
   - **Frequency:** Called once per non-optimal iteration for entering column $q$.
   - **Mechanism:** Reuses the forward LU factors from `lu = LU(B)` via dense forward and back substitution.
4. **Artificial Variable Elimination / Basis Cleanup:**
   - **Call:** `row = LU(M[:, basis].T).solve(np.eye(m_total)[i]) @ M[:, :art_start]` (`sovopt/simplex.py:598`).
   - **Frequency:** Called if artificial variables remain basic with zero value at Phase I termination.
   - **Mechanism:** Dense transpose LU factorization from scratch.
5. **Exact Rational Fallback for Farkas Rays:**
   - **Call:** `y_F = _exact_solve_BT(M[:, basis], phase_cost[basis])` (`sovopt/simplex.py:100`).
   - **Frequency:** Only when numerical Farkas reconciliation fails on certified infeasible models.
   - **Mechanism:** Dense Gaussian elimination using exact rational `fractions.Fraction` arithmetic.

### 3.2 Dense Call Sites in Other Solvers

- **QP IPM Normal Equations:** `sovopt/qp.py:80` calls `lu = LU(K + reg * np.eye(n))` each IPM iteration, followed by predictor solve (`line 83`) and corrector solve (`line 93`).
- **PDHG First-Order Solver:** Does not factorize bases; uses SpMV via `sovopt/pdhg.py::CSR.dot`.

---

## 4. Algorithmic Properties of the Dense Implementation

### 4.1 Pivot Rule: Partial Row Pivoting (NOT Markowitz)
- The pivot rule in `sovopt/linalg.py:12`:
  ```python
  p = k + int(np.argmax(abs(self.a[k:, k])))
  ```
- **Classification:** Standard Gaussian elimination with partial row pivoting (choosing the largest absolute entry in column $k$ among active rows $k \dots n-1$).
- **Distinction:** This is **not** Markowitz pivoting. Markowitz pivoting evaluates the fill-in risk $(r_i - 1)(c_j - 1)$ across 2D candidates $(i, j)$ constrained by numerical threshold criteria. The dense code has zero notion of sparsity, row nonzero counts, column nonzero counts, or fill minimization.

### 4.2 Factorization Reuse & Basis Updates
- **Current Factorization Reuse:** Zero between pivots.
- **Eta / Product-Form Updates:** Not implemented in baseline. Every pivot immediately discards previous factors and re-factorizes from scratch.
- **Transpose Reuse:** None. To solve $B^T y = c_B$, the code constructs $B^T$ and factorizes it from scratch ($2 \times O(m^3)$ per simplex pivot).

### 4.3 Iterative Refinement
- Implemented in `sovopt/linalg.py:25-28`:
  ```python
  x = self.raw(b)
  for _ in range(2):
      r = np.asarray(np.asarray(b, np.longdouble) - np.asarray(self.original, np.longdouble) @ np.asarray(x, np.longdouble), float)
      if np.max(abs(r), initial=0) <= 1e-13 * (1 + np.max(abs(b), initial=0)): break
      x += self.raw(r)
  ```
- Uses up to 2 refinement steps.
- On macOS ARM64 (Apple Silicon), `np.finfo(np.longdouble)` has standard binary64 precision (15-17 decimal digits, 53 mantissa bits, same as `float64`), which must be recorded honestly.

### 4.4 Memory and Time Complexity
- **Memory:** $O(m^2)$ for each $B$, $B^T$, and factorized copy. Total memory allocated per iteration scales quadratically with constraint row count $m$, independent of matrix sparsity.
- **Time per iteration:** $2 \times \frac{2}{3} m^3 + O(m^2) \approx \frac{4}{3} m^3$ floating-point operations per pivot.
- **Practical constraint:** Strictly limits scalability to small LPs ($m \le 1000$).

---

## 5. Architectural Requirements for Gate 3 Sovereign Sparse Engine

To achieve true sovereign sparse numerical linear algebra:
1. **Sovereign CSR & CSC Classes (`sovopt/sparse.py`):** Pure NumPy index arrays (`indptr`, `indices`, `data`), with transpose matvec, slice, extraction, zero-dropping, and shape validation. Zero `scipy.sparse` dependency.
2. **Direct Sparse Basis Extraction:** Extract $B$ directly into sparse format without dense intermediate allocation.
3. **Threshold Markowitz Pivot Search:** Fill-risk scoring $(r_i - 1)(c_j - 1)$ combined with threshold stability $|a_{ij}| \ge u \cdot \max_k |a_{kj}|$.
4. **Sovereign Sparse LU (`sovopt/sparse_lu.py`):** Permutations $P B Q = L U$, sparse triangular forward/backward solves for both $B x = b$ (FTRAN) and $B^T y = b$ (BTRAN).
5. **Product-Form / Eta Basis Updates:** Maintain an eta vector stack $B_k = B_0 E_1 E_2 \dots E_k$ allowing $O(m \cdot \text{nnz})$ pivots between full refactorizations.
6. **Deterministic Refactorization Triggers:** Trigger full refactorization on eta depth limit, small pivot, residual degradation, or condition deterioration.
7. **Telemetry & Dual Backends:** Support `linear_algebra="auto"`, `"dense"`, `"sparse"`, recording full basis and solve diagnostics in result dictionaries.

---

## 6. Gate 3 Implementation Verification & Telemetry (Post-Implementation Status)

> **Post-Implementation Question:** *Does production LP basis solve now support and use sovereign sparse LU?*  
> **Answer:** **YES.**  
> Gate 3 is fully implemented in sovereign code (`sovopt/sparse.py`, `sovopt/sparse_lu.py`, and `sovopt/simplex.py`).

### 6.1 Deliverables Implemented

1. **`sovopt/sparse.py`**: Pure NumPy sovereign `CSRMatrix` and `CSCMatrix` supporting:
   - Row and column slicing, column extraction (`extract_columns`).
   - Sparse matrix-vector (`matvec`) and transpose vector (`rmatvec`) multiplication.
   - Triplet constructors (`csr_from_triplets`, `csc_from_triplets`), zero-dropping (`drop_zeros`), duplicate summing (`sum_duplicates`), and deterministic index sorting (`sort_indices`).
   - Zero `scipy.sparse` imports anywhere in the codebase.
2. **`sovopt/sparse_lu.py`**:
   - `MarkowitzPivotSelector`: Threshold stability criterion $|a_{ij}| \ge u \cdot \max_k |a_{kj}|$ with $u = 0.1$, fill-in risk score $(r_i - 1)(c_j - 1)$, and deterministic tie-breaking.
   - `SparseLU`: Exact sparse factors $P B Q = L U$ without full dense basis materialization; sparse forward/backward triangular solves for both FTRAN ($B x = b$) and BTRAN ($B^T y = c$); iterative refinement with dynamic platform longdouble precision detection.
   - `SparseBasisEngine`: Product-Form of Inverse (PFI) maintaining eta vectors $E_k$; forward eta sweep for FTRAN and backward eta sweep for BTRAN; deterministic refactorization triggers (`INITIAL`, `ETA_LIMIT`, `SMALL_PIVOT`, `RESIDUAL_DETERIORATION`, `FORCED`).
3. **`sovopt/simplex.py`**:
   - `_iterate_dense`: Preserved original dense LU implementation as oracle and small-problem fallback.
   - `_iterate_sparse`: Sparse primal revised simplex iteration with threshold Markowitz LU and PFI eta updates.
   - `solve_lp`: Parameter `linear_algebra='auto'|'dense'|'sparse'`. When `'auto'`, routes models with $m \ge 25$ to sparse LU, falling back to dense LU if numerical difficulties occur.
   - Uniform linear algebra telemetry attached to all LP result dictionaries (`linear_algebra_requested`, `linear_algebra_used`, `basis_factorization`, `sparse_basis_nnz`, `sparse_basis_density`, `refactorizations`, `eta_updates`, `ftran_count`, `btran_count`, `max_eta_depth`, `iterative_refinement_steps`).

### 6.2 Empirical Benchmark Telemetry on Genuine Netlib Instances

| Instance | Rows ($m$) | Cols ($n$) | Linear Algebra | Status | Objective | Refactorizations | Eta Updates | FTRAN Solves | BTRAN Solves | Max Eta Depth |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AFIRO** | 27 | 32 | `sparse` | `OPTIMAL_VERIFIED` | -464.7531428571 | 3 | 52 | 108 | 55 | 25 |
| **SC50A** | 50 | 48 | `sparse` | `OPTIMAL_VERIFIED` | -64.5750770586 | 4 | 54 | 114 | 58 | 25 |
| **SC50B** | 50 | 48 | `sparse` | `OPTIMAL_VERIFIED` | -70.0000000000 | 4 | 52 | 110 | 56 | 25 |
| **BLEND** | 74 | 83 | `sparse` | `OPTIMAL_VERIFIED` | -30.8121498458 | 13 | 310 | 644 | 323 | 25 |

*(In comparison, dense LU required 55 full $27 \times 27$ factorizations on AFIRO and 323 full $74 \times 74$ factorizations on BLEND).*

### 6.3 Test Coverage
- Dedicated test suite `tests/test_sparse.py` covers 28 distinct test cases: CSR/CSC operations, Markowitz pivot selection, threshold rejection, singularity detection, factorization accuracy, FTRAN/BTRAN residuals, dense-vs-sparse agreement, refinement, single/multiple eta updates, BTRAN eta sweeps, all refactorization triggers, near-singular recovery semantics, and end-to-end original-model verification across all 4 authentic Netlib benchmarks.

