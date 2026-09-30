# Verified Dataset Catalogue

This catalogue records provenance for every dataset used in the active benchmark suite.
Each entry must be complete before the dataset is used in tests or dashboards.
See AGENTS.md for the full requirements.

## Active verified instances

*(Empty — dataset research in progress. See data/legacy_synthetic/ for retired synthetic baseline.)*

## Instances under evaluation

| Name | Source | Dims | Status | Notes |
|------|--------|------|--------|-------|
| AFIRO (Netlib LP) | https://www.netlib.org/lp/data/afiro | TBD | EVALUATING | Checking bound types and parser compatibility |
| SC50A (Netlib LP) | https://www.netlib.org/lp/data/sc50a | TBD | EVALUATING | Checking bound types |
| SC50B (Netlib LP) | https://www.netlib.org/lp/data/sc50b | TBD | EVALUATING | Checking bound types |
| BLEND (Netlib LP) | https://www.netlib.org/lp/data/blend | TBD | EVALUATING | Checking bound types |

## Rejected candidates

*(To be filled as evaluation proceeds)*

## Unsupported features preventing adoption

| Feature | Impact | Gate required |
|---------|--------|---------------|
| FR/MI (free/negative-inf lower) bounds | Most Netlib LPs | Gate 1 (transforms.py) |
| RANGES section | Some Netlib LPs | Gate 1 (mps.py extension) |
| MAX objective | Some instances | Gate 0 extension (mps.py) |
| Objective RHS offset | Some instances | Gate 0 extension (mps.py) |
| Free variables | Most real LPs | Gate 1 (transforms.py) |
| Large dimensions (>250 vars) | Most real instances | Gate 2 (sparse infrastructure) |

## Refinery-specific data

No complete published refinery LP/MILP case with reproducible model inputs has been
identified that satisfies all redistribution and provenance requirements as of this
writing. Specifically:

- MRPL operational data: Not publicly available. Authorized MRPL data would require
  direct institutional access and an explicit data-sharing agreement.
- Generic petroleum-industry LP case studies in published literature often omit the
  actual coefficient values needed to reproduce the model.
- The HAVERLY1/HAVERLY2/HAVERLY3 pooling problems (from Haverly, 1978) are classic
  refinery pooling instances but involve nonlinear (bilinear) constraints that make
  them nonconvex QPs — outside the current solver scope.

The "synthetic refinery" models in data/legacy_synthetic/ are RETIRED. They must not
be re-introduced as real-data evidence.
