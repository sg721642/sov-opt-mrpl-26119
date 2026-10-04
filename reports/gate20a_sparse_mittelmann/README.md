# SOV-OPT Gate 20A — True Sparse Core & Hans Mittelmann Benchmark Suite

## 1. Overview and Engineering Objectives

Gate 20A breaks the previous dense memory ceiling ($N \le 5,000$ variables) and replaces it with a
**Sovereign True Sparse Core** (`CSRMatrix` / `CSCMatrix`). The representation-aware guard permits
models up to configured structural limits ($10^7$ variables/rows), strictly subject to a deterministic
**2.0 GB sparse-memory budget**.

To validate this architectural breakthrough under authentic academic benchmark standards, four
authentic Mittelmann LP benchmark instances were parsed, validated, and evaluated under bounded
execution from **Hans Mittelmann's Benchmark Collection** (`https://plato.asu.edu/ftp/lptestset/`):
1. **`qap15`**: LP benchmark instance (QAP relaxation; $6,330$ rows, $22,275$ cols, $94,950$ nnz)
2. **`brazil3`**: LP benchmark instance (MIPLIB 2017 LP relaxation; $14,646$ rows, $23,968$ cols, $133,184$ nnz)
3. **`chromaticindex1024-7`**: LP benchmark instance (MIPLIB 2017 LP relaxation; $67,583$ rows, $73,728$ cols, $270,324$ nnz)
4. **`supportcase10`**: LP benchmark instance (MIPLIB 2017 LP relaxation; $165,684$ rows, $14,770$ cols, $555,082$ nnz)

---

## 2. Key Technical Breakthroughs

1. **Native Sovereign `CSRMatrix` & `CSCMatrix`**:
   - Zero external library dependencies (pure Python & NumPy stdlib).
   - In-place $O(nnz)$ SpMV ($y = A x$) and Adjoint SpMV ($x = A^T y$).
   - Fast $O(nnz)$ transpose via CSC count-sort duality.
   - Exact $O(nnz)$ row/column absolute norms for Pock-Chambolle diagonal preconditioning.
2. **Elimination of Densification Across All Modules**:
   - `sovopt/model.py`: Accepts `CSRMatrix` directly; canonicalizes inequalities via `sparse_inequalities()` without dense intermediate arrays.
   - `sovopt/mps.py`: Streams MPS records directly into triplet lists and instantiates `CSRMatrix`. Zero dense list-of-lists.
   - `sovopt/pdhg.py`: Operates on sparse inequalities; eliminated dense transpose BLAS; exposes direct GPU pointer handoff.
   - `sovopt/verify.py`: Sparse residual verification; eliminated dense $n \times n$ quadratic matrix allocation on linear programs.
   - `sovopt/dual_simplex.py`: Sparse triplet extraction directly from `CSRMatrix`.
3. **Sparse Representation Stress Test**:
   - 1,000,000-variable × 500,000-row sparse representation and SpMV stress test completed with 2,500,000 nonzeros.
   - Evaluated across tiers: $10\text{K}$, $25\text{K}$, $50\text{K}$, $100\text{K}$, $250\text{K}$, $500\text{K}$, and $1\text{M}$ variables.
   - At $1,000,000$ variables $\times 500,000$ rows ($2,500,000$ nonzeros):
     - Sovereign sparse memory: **41.96 MB**
     - Theoretical dense memory: **3,725.29 GB (3.7 Terabytes)**
     - Compression factor: **90,909x**
     - SpMV execution time: **443 ms** on Apple Silicon MacBook Air.
     - *(Note: This is a representation and matrix-vector operation benchmark, NOT a full 1M-variable optimization solve.)*

---

## 3. Honest Algorithmic Comparison: PDHG vs HiGHS

SOV-OPT reports all results with complete scientific transparency:
- **First-Order Methods (PDHG)**: PDHG is an iterative first-order splitting method. While it scales with minimal memory and low cost-per-iteration to millions of variables, it converges sublinearly on highly degenerate, ill-conditioned continuous LPs like `qap15` and `supportcase10`. Under a 20-second in-loop solver time budget checked at convergence checkpoints (where wall-clock elapsed time may exceed the nominal budget by one checkpoint interval), SOV-OPT reached `LIMIT_REACHED` on all four Mittelmann instances.
- **External HiGHS Baseline**: HiGHS is an industrial-grade, compiled C++ dual simplex and interior-point solver with advanced presolve, crash bases, and bound-flipping. On `brazil3`, HiGHS reported `kOptimal` with objective 2.0 in approximately 9.065 s. On the remaining three degenerate instances (`qap15`, `chromaticindex1024-7`, and `supportcase10`), HiGHS did not report an optimal solution within the 30-second evaluation window.
- **Strict Boundary**: HiGHS is executed solely as an external differential baseline in an isolated worker process (`scripts/baseline_worker.py`). It is never imported into the sovereign solver core.
