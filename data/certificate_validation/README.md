# Public Certificate-Validation Datasets

This directory contains public optimization problem instances maintained exclusively
for **mathematical certificate validation** (e.g., exact rational Farkas certificates
for infeasible LPs, unbounded recession certificates), as opposed to runtime performance
benchmarking.

Instances in this directory:
- Are authentic instances sourced from authoritative public repositories (e.g., Netlib LP/Infeas).
- Are evaluated for mathematical certificate correctness, not runtime speed or iteration counts.
- Are strictly excluded from solver performance leaderboards, geometric mean runtime calculations,
  and active performance benchmark counts.

## Active Certificate-Validation Instances

### 1. WOODINFE
- **Primary Upstream Collection:** Netlib LP / Infeasible LP collection (`https://www.netlib.org/lp/infeas/`)
- **Curator:** John W. Chinneck (Carleton University), 1993
- **Contributor:** Harvey J. Greenberg (University of Colorado at Denver)
- **Literature Attribution:** Network forestry model analyzed in Greenberg, H.J. (1993),
  "How to Analyze the Results of Linear Programs - Part 3: Infeasibility Diagnosis",
  *Annals of Mathematics and Artificial Intelligence*.
- **MPS SHA-256:** `26cb8633b4d9bb9dcbd60b04534ef7b9b0709a67b0ba62c0a95481a8ea71181f`
- **Reference Mirror:** HiGHS test suite (`check/instances/woodinfe.mps`, commit `ccbcccdf`, MIT License).
- **Target Verification:** `INFEASIBLE_CERTIFIED` via exact binary-rational Farkas certificate
  ($y \ge 0, y^T A \le 0, y^T b > 0$).
