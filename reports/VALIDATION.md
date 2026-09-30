# Delivery validation record

The package was exercised in the delivery environment on Linux x86-64, Python 3.12.14, NumPy 2.3.5. See tests.txt for the captured test output and benchmark.json for raw repeated results.

- 17 automated test methods passed.
- Included parameter loops: 50 LP problems with constructed optimal KKT solutions, 25 small all-integer problems checked against exhaustive enumeration, and 20 positive-diagonal convex QPs with constructed KKT solutions.
- Other checks: pivoted LU residuals, fixed/negative variable bounds, degenerate duplicated constraints with row scaling from 1e-8 to 1e8, exact rational bound validity, certificate rejection/acceptance, corrupted candidates, unsupported nonconvex/MIQP input, solver limits, MPS parsing, CPU PDHG, HTTP page/examples/solve and invalid-input handling.
- The synthetic refinery LP objective was 4865. The synthetic refinery MILP objective was 4985. An external SciPy/HiGHS process returned the same objectives.
- The synthetic QP objective was approximately 5009.500002 with default scaling; accepted original-model KKT residuals were recorded. Scaling off also passed, with a slightly different tolerance-level objective approximation.
- The contradictory-production example returned a Farkas certificate checked exactly using rational arithmetic on the binary64 input model.
- The frozen five-example manifest was executed, including tiny.mps with optimum -11.

## What these checks do not establish

No CUDA device was available for this delivery, so GPU compilation, correctness and speedup remain untested. The package was not run on the user's Mac. No Netlib/MIPLIB/QPLIB performance suite, industrial MRPL dataset, million-variable problem or commercial solver was run. Docker source is supplied but no container build/deployment was executed. HTTP routes were integration-tested; cross-browser visual compatibility has not been comprehensively certified.

`OPTIMAL_VERIFIED` is a declared numerical tolerance result, not a formal proof of exact optimality. MILP lower bounds and accepted Farkas witnesses use exact rational checks, but primal feasibility is numerical. The final audit alone cannot replay the entire MILP tree. There is no guarantee of error-free behavior on arbitrary models.

The supplied blueprint's sparse dual simplex, custom sparse LU/eta updates, general presolve/postsolve, Devex/Harris engineering, cuts, pseudocosts, basis warm starts, full MPS/QPLIB, C ABI and industrial-scale validation remain development work. See the implementation plan for their dependencies and acceptance gates.
