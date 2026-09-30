# Model Format and Verified Benchmark Suite

## 1. Sovereign Model Format

SOV-OPT models can be specified in native JSON or standard MPS/QPS files. The canonical representation is finite-box continuous or mixed-integer optimization, minimized internally with zero third-party solver dependencies.

### Native JSON Schema

```json
{
  "name": "AVGAS",
  "names": ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8"],
  "c": [-2.0, -1.0, -3.0, -2.0, -4.0, -3.0, -5.0, -4.0],
  "A": [
    [-1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0]
  ],
  "row_lower": [-1.0, -1.0, -1.0, -1.0],
  "row_upper": [null, null, null, null],
  "lower": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "upper": [null, null, null, null, null, null, null, null],
  "integer": [],
  "Q": null,
  "maximize": false,
  "obj_offset": 0.0
}
```

#### Fields:
- **`name`**: String identifier for the model.
- **`names`**: List of $n$ unique variable names.
- **`c`**: Linear objective vector $\mathbf{c} \in \mathbb{R}^n$.
- **`A`**: Dense $m \times n$ constraint matrix.
- **`row_lower`**, **`row_upper`**: Row bounds $\mathbf{l}_{\text{row}} \le A \mathbf{x} \le \mathbf{u}_{\text{row}}$. `null` denotes $-\infty$ or $+\infty$.
- **`lower`**, **`upper`**: Variable bounds $\mathbf{l} \le \mathbf{x} \le \mathbf{u}$. `null` defaults to $0.0$ for lower bound, or $+\infty$ for upper bound.
- **`integer`**: List of 0-based indices for integer variables (MILP).
- **`Q`**: Optional symmetric $n \times n$ matrix for quadratic objectives: $\frac{1}{2} \mathbf{x}^T Q \mathbf{x} + \mathbf{c}^T \mathbf{x}$.
- **`maximize`**: Boolean flag. If `true`, the original model is a maximization problem. The solver internally negates $\mathbf{c}$ and reports the correct sign at postsolve.
- **`obj_offset`**: Constant offset added to the objective value (e.g. from MPS RHS constant).

---

## 2. Supported MPS / QPS Subset

The built-in sovereign parser (`sovopt/mps.py`) parses fixed-format and free-format MPS and QPS files directly into canonical `Model` objects without third-party libraries:

- **Sections supported**: `NAME`, `OBJSENSE` (MIN/MAX), `ROWS` (N, L, G, E), `COLUMNS` (with `INTORG`/`INTEND` integer markers), `RHS`, `BOUNDS` (`LO`, `UP`, `FX`, `FR`, `MI`, `PL`, `BV`, `LI`, `UI`), `QUADOBJ` / `QMATRIX` (for convex QPs), and `ENDATA`.
- **Rejection criteria**: Non-symmetric or non-PSD $Q$, RANGES sections, multiple N rows with conflicting senses, and unconstrained infinite models with unbounded rays.

---

## 3. Active Verified Benchmark Suite

In strict compliance with repository integrity rules, all synthetic and fictional refinery models have been removed from the active suite. Every active benchmark problem is a genuine, source-verifiable historical application instance:

| Instance | Class | Application / Domain | Reference Source | Published Reference |
|:---|:---:|:---|:---|:---|
| **AVGAS** | LP | Historical aviation gasoline blending | Symonds (1955) / Charnes et al. (1952) | `-7.75` |
| **AFIRO** | LP | Resource allocation (Stanford SOL) | Netlib LP (MINOS 5.3) | `-464.75314286` |
| **SC50A** | LP | Staircase dynamic production model | Netlib LP (MINOS 5.3) | `-64.575077059` |
| **SC50B** | LP | Staircase dynamic production model | Netlib LP (MINOS 5.3) | `-70.000000000` |
| **BLEND** | LP | Petroleum refinery blending (Murtagh) | Netlib LP (MINOS 5.3) | `-30.812149846` |
| **FLUGPL** | MILP | Airline fleet allocation (Wagner et al.) | MIPLIB 1.0 / 2017 | `1201500.0` (integer optimum) |

---

## 4. Disclosed Empty States

### Proprietary MRPL Refinery Production Data (Empty State)
- **Status:** Empty state.
- **Disclosure:** *No authorized MRPL dataset is available in this project.*
- **Context:** Mangalore Refinery and Petrochemicals Limited (MRPL) operational LP models (crude assay yields, distillation tray cut temperatures, unit utility balances, and transfer prices) are confidential trade secrets. Fictional refinery parameters or placeholder business numbers are strictly prohibited. The repository provides documented historical petroleum blending benchmarks (`AVGAS` and `BLEND`) instead.

### Industrial Convex Quadratic Programs (Empty State)
- **Status:** Empty state.
- **Disclosure:** *No authentic public industrial convex QP benchmark is currently verified in the active suite.*
- **Context:** Synthetic toy QP instances (such as test cases from parser repositories) have been excised. The sovereign QP interior-point solver (`sovopt/qp.py`) is verified using rigorous KKT conditions and eigenvalue inspection, and genuine industrial QP benchmarks will be admitted when public instances with source provenance are available.

