# Benchmark Manifest Amendments Log — SOV-OPT Gate 7.1

**Policy:** Benchmark membership was frozen before result evaluation; subsequent capability-classification amendments are versioned, documented, and retained. Manifest records are never silently altered or instances removed.

---

## Amendment Record: QPLIB_8938 Resource Classification Correction

- **Date / Timestamp:** `2026-10-02T02:35:00+05:30` (Gate 7 Execution)
- **Target File:** `data/manifests/qplib_convex_qp.json` (and master `data/manifest.json`)
- **Original Frozen Manifest SHA-256:** `8d4b57add303523c70421f58a88cf36b7f81d619f078fac1cfb48d8878360a6b`
- **Amended Manifest SHA-256:** `8cfc7d44e71cef3543d825abdd1954f477f40b7839e1a3109d19511d5a18390c`
- **Instance Affected:** `QPLIB_8938` ($n = 4001$, $m = 11999$)
- **Prior Classification:**
  - `is_supported`: `true`
  - `selection_rule`: `SUPPORTED_AND_SELECTED`
- **Amended Classification:**
  - `is_supported`: `false`
  - `selection_rule`: `UNSUPPORTED_RESOURCE_LIMIT`
  - `rejection_reason`: `Dense Q allocation for n=4001 would require approximately 488.4 MB, exceeding the 250 MB memory guard. Parser raises UNSUPPORTED_RESOURCE_LIMIT before unsafe dense Q allocation.`

### Rationale and Preservation Notice

During automated test suite execution, the parser memory guard in `sovopt/qplib.py` correctly identified that allocating an $n \times n = 4001 \times 4001$ float64 dense matrix requires $\approx 488.4$ MB, which exceeds the predeclared environment safety limit of 250 MB (`max_dense_qp_memory_mb: 250`). The parser raises a typed exception `UnsupportedQPLIBError(reason_code="UNSUPPORTED_RESOURCE_LIMIT")`.

**This amendment is a capability/resource-classification correction, not a removal or de-selection of the instance.**

Under the anti-cherry-picking rules of SOV-OPT:
1. `QPLIB_8938` remains an active, permanent member of the frozen public benchmark candidate inventory.
2. It is evaluated and reported in all benchmark reports (Section D of `reports/VERIFIED_BENCHMARKS.md`) under its verified status `UNSUPPORTED_RESOURCE_LIMIT`.
3. It serves as an automated regression test confirming that memory guards prevent unsafe allocations and out-of-memory crashes on consumer hardware.
