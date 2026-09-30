# Implemented architecture and mathematics

## Canonical model

The minimization problem is `0.5*x^T*Q*x + c^T*x`, subject to `row_lower <= A*x <= row_upper`, finite `lower <= x <= upper`, and selected integer variables. LP/MILP omit Q. QP forbids integer variables and requires a symmetric matrix passing a conservative pivoted PSD check. This release does not accept infinite variable bounds, MIQP, general NLP, indicators, SOS or quadratic constraints.

The representation is dense NumPy arrays. CPU limits are 250 variables and 1,000 input rows; the web cap is 30 variables and 80 rows. These are rejection limits, not performance guarantees. A dense simplex basis may become expensive well below the caps. PDHG converts dense input to CSR internally; consequently the entire input path is not sparse-scalable yet.

## Original linear algebra

`linalg.py` computes dense LU with partial pivoting and a relative unsafe-pivot threshold. Solves use forward/back substitution and up to two iterative-refinement corrections. Residuals use NumPy long double where it provides additional precision. All basis factorizations are recomputed; there are no eta updates, sparse Markowitz pivots or Forrest–Tomlin updates. `numpy.linalg.solve` and existing factorization packages are not used by the core.

## LP route

1. Convert finite row sides and variable bounds into `G*x <= h`.
2. Shift `x = lower + t`, with `t >= 0`.
3. Optionally divide every inequality by its largest absolute coefficient.
4. Normalize RHS signs and introduce slack/surplus/artificial variables.
5. Minimize the sum of artificial variables in Phase I.
6. If infeasibility is suspected, reconstruct a Farkas multiplier and accept the status only if the exact rational check succeeds.
7. Remove artificial variables from the basis.
8. Optimize the original linear objective using primal revised simplex and Bland-style entering/tie choices.
9. Recover the original x and inequality multipliers. Recompute KKT conditions against the original model.

This is **primal revised simplex**, not dual simplex, not Devex, and not a Harris ratio implementation. The scale transformation is undone in the multipliers. No general presolve transformation is performed, so there is no unimplemented postsolve stack hidden behind the verification.

## Convex QP route

For `G*x + s = h`, `s >= 0`, `z >= 0`, the KKT equations are:

- stationarity: `Q*x + c + G^T*z = 0`;
- primal equation: `G*x + s - h = 0`;
- complementarity: `s_i*z_i = 0`.

The solver starts with positive slack and dual estimates and does not require a feasible x. It computes an affine predictor, a centering parameter from the predicted complementarity, and a corrector including the affine product term. Eliminating slack and dual directions gives a dense normal-equation matrix `Q + G^T*diag(z/s)*G`, regularized for the Newton solve. A 0.995 fraction-to-boundary rule preserves positivity. Only the **unregularized original KKT residuals** determine acceptance.

Normal equations can amplify conditioning problems. Sparse augmented KKT systems and better regularization are roadmap work. There is no homogeneous self-dual embedding, so arbitrary infeasible QPs may hit limits or numerical failure without an infeasibility proof.

## Branch and bound

`milp.py` uses a best-bound heap, most-fractional branching and fresh LP solves at each node. It rounds a near-integral candidate and checks it against the original model. There are no cuts, pseudocosts, warm-start bases or parallel tree search.

For every nonnegative inequality multiplier z and any feasible x:

`c^T*x >= -h^T*z + sum_j min_{lower_j <= x_j <= upper_j} (c + G^T*z)_j*x_j`.

The minimum uses the lower bound for a nonnegative coefficient and the upper bound otherwise. `Fraction` evaluates this lower bound exactly for the supplied binary64 coefficients and multipliers. Bounds printed as floats are rounded downward where needed. Thus a dual estimate need not have exactly zero stationarity residual to yield a valid lower bound over a finite box.

Incumbent feasibility remains tolerance-based. The package does not claim a formal exact MILP solution proof. Near-integral nodes close only when the conservative lower bound and checked candidate satisfy the requested numerical gap. Unresolved node LPs stop the proof attempt instead of being discarded.

## Farkas certificate

For inequalities `G*x <= h`, a nonnegative z with `G^T*z = 0` and `h^T*z < 0` proves infeasibility. These relations are checked exactly as rational operations on the input float values. A bounded-denominator rational reconstruction may propose integer-scaled multipliers; reconstruction itself is not proof. Only the exact checker can grant `INFEASIBLE_CERTIFIED`. Integer boxes containing no integer can also establish simple infeasibility directly.

## Experimental PDHG

Using only row inequalities and projecting x to its box, the iterations are:

`y_next = max(0, y + sigma*(G*x_bar - h))`

`x_next = clip(x - tau*(c + G^T*y_next), lower, upper)`

`x_bar = 2*x_next - x`.

Diagonal step sizes use inverse absolute row/column sums with a 0.99 safety factor. The unscaled alternative uses a bound on the spectral norm from maximum row and column sums. A periodic average restart is available. This is a modest PDHG implementation, not a full reproduction of PDLP adaptive heuristics or the research paper's convergence engineering.

CPU SpMV uses the original CSR structure with NumPy accumulation. CUDA SpMV uses the supplied `RawKernel` source. CuPy supplies device allocation, kernel compilation and vector operations. CPU verification is included in end-to-end timing. Final bound multipliers are reconstructed from box activity before KKT checks.

## Numerical trust semantics

- `OPTIMAL_VERIFIED`: numerical LP/QP KKT checks passed, or a checked MILP incumbent closed the finite tree within the reported gap.
- `INFEASIBLE_CERTIFIED`: exact Farkas proof, elementary integer-box proof, or a tree whose leaves were safely resolved as infeasible.
- `LIMIT_REACHED`: budget ended; a feasible candidate may or may not be present.
- `NUMERICAL_FAILURE`: a trustworthy conclusion could not be established.
- `INVALID_MODEL`: CLI rejected an input or unsupported feature.

LP iteration exhaustion currently returns `NUMERICAL_FAILURE` with an explicit iteration-limit message. QP, PDHG, MILP and external worker deadlines return `LIMIT_REACHED`.

The primal metric is `max_i max(G_i*x-h_i,0)/(1+abs(h_i)+abs(G_i)*abs(x))`. The checker also prints the largest absolute violation. Stationarity is normalized componentwise by `1+abs(gradient)+abs(G^T)*abs(z)`. Complementarity and the aggregate relative duality gap are checked separately. Integrality is an absolute distance to the nearest integer.

A residual tolerance of 1e-7 is a numerical criterion, not a percentage accuracy, guaranteed digit count, or theorem covering all ill-conditioned data. Scale units sensibly, inspect absolute violations, and use validation cases relevant to the application.
