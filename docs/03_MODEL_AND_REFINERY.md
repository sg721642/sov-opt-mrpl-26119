# Model format and refinery interpretation

## Native JSON

```json
{
  "name": "Small production LP",
  "names": ["product_a", "product_b"],
  "c": [-3, -2],
  "A": [[1, 1]],
  "row_lower": [null],
  "row_upper": [4],
  "lower": [0, 0],
  "upper": [3, 3],
  "integer": []
}
```

All models minimize. Negate profit coefficients to maximize profit, and explain the sign when reporting it. Each A row has exactly n columns. `null` is permitted in row bounds only: it means no lower or no upper row side, respectively. Every variable needs finite bounds. Do not add an arbitrary big-M merely to make a model accepted: that changes the problem.

Optional Q uses the convention `0.5*x^T*Q*x`. The full symmetric matrix must be provided, not just one triangle. Optional `integer` contains zero-based variable indices. Bounds `[0,1]` plus an integer index define a binary variable. Variable names are display labels. The API supports Python `Model` objects with validation and JSON/MPS file loading.

## Supported MPS subset

The parser accepts explicit free-format `NAME`, `ROWS`, `COLUMNS`, `RHS`, `BOUNDS`, `ENDATA`, and `OBJSENSE MIN`. Row types are N/L/G/E. Supported bounds are LO/UP/FX/BV/LI/UI. INTORG/INTEND markers are handled. Repeated column coefficients are added. There must be a single objective, RHS set and bound set. Nonzero objective offsets, infinite variable bounds, multiple N rows, RANGES, SOS, quadratic MPS sections, fixed-format continuation shorthand and unrecognized dialects are not supported.

This is not a full Netlib/MIPLIB parser. Rejection is safer than silently interpreting an unsupported file. QPLIB input is not implemented; use the native QP format for this release.

## Refinery family

The examples are deliberately small, synthetic blending models, inspired by refinery planning rather than calibrated to MRPL operations. Two feed types serve two product specifications. All volumes use a common arbitrary volume unit; costs use arbitrary cost units per volume. Sulfur is a linear weighted quality attribute.

| Variable | Meaning |
|---|---|
| `low_to_premium` | Low-sulfur feed allocated to premium product |
| `high_to_premium` | High-sulfur feed allocated to premium product |
| `low_to_regular` | Low-sulfur feed allocated to regular product |
| `high_to_regular` | High-sulfur feed allocated to regular product |
| `high_feed_enabled` | MILP only: whether high-sulfur feed supply is activated |

Premium demand is 60; regular demand is 50. Low-sulfur supply is capped at 85 and high-sulfur at 100. Feed costs are 52 and 34. Low-feed sulfur is 0.5 and high-feed sulfur is 2.5, using consistent quality units. Premium sulfur limit is 1.0, giving `-0.5*x_low + 1.5*x_high <= 0`. Regular limit is 1.8, giving `-1.3*x_low + 0.7*x_high <= 0`.

The LP optimum uses `[45,15,17.5,32.5]`. Low feed totals 62.5; high feed totals 47.5. Therefore `52*62.5 + 34*47.5 = 4865`.

The MILP adds `high_to_premium + high_to_regular <= 100*high_feed_enabled` and a fixed activation cost of 120. The binary solution activates supply, giving `4865+120 = 4985`. The number 100 is the actual declared high-feed capacity, not an invented unbounded big-M. Low-feed capacity 85 means that completely disabling high feed cannot meet total demand 110.

The QP adds a diagonal `Q=0.08*I`. At the LP allocation its penalty is `0.04*(45²+15²+17.5²+32.5²)=144.5`, giving 5009.5. The included KKT check establishes the numerical QP result rather than relying on this evaluation alone.

## Real data needed next

Before industrial claims, obtain authorized feed specifications, product demands, unit capacities, compatibility constraints, inventory balances, blending equations, operating costs, units and time horizon from the problem owner or a cited public case. Preserve source provenance and anonymize confidential data before sharing. Actual nonlinear pooling cannot be validated with this linear blending model.

For time-indexed planning, create variables per feed/product/period, inventory equations across periods and physically justified bounds. First verify a one-period hand-solvable instance, then expand dimensions and measure memory/runtime. Expanding the data generator alone does not establish solver scalability.
