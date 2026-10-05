# Mittelmann Benchmark Dataset Catalogue — SOV-OPT

This catalogue records the provenance, checksums, problem dimensions, and benchmark metadata
for authentic Linear Programming (LP) benchmark instances acquired from Hans Mittelmann's
authoritative benchmark collection at Arizona State University:
`https://plato.asu.edu/ftp/lptestset/`

All instances are genuine, unmodified open benchmarks used in academic linear programming
evaluations and MIPLIB 2017 LP relaxations.

To prevent repository bloat, authoritative instances are stored in their original compressed
`.mps.bz2` format. SOV-OPT's `read_mps()` parser streams `.bz2` archives directly into sovereign
`CSRMatrix` structures without intermediate physical files. Both compressed archive hashes and
uncompressed stream hashes are cryptographically verified and recorded below.

---

## 1. Instance Overview

| Instance Name | Class | Rows ($m$) | Columns ($n$) | Nonzeros ($nnz$) | Density | Format | Compressed Size | Uncompressed Content Size |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`qap15`** | LP (Continuous) | 6,330 | 22,275 | 94,950 | 0.000673 | MPS (.bz2) | 276 KB | 3.5 MB |
| **`brazil3`** | LP (Continuous) | 14,646 | 23,968 | 133,184 | 0.000379 | MPS (.bz2) | 343 KB | 23.9 MB |
| **`chromaticindex1024-7`** | LP (Continuous) | 67,583 | 73,728 | 270,324 | 0.000054 | MPS (.bz2) | 1.8 MB | 23.0 MB |
| **`supportcase10`** | LP (Continuous) | 165,684 | 14,770 | 555,082 | 0.000227 | MPS (.bz2) | 1.9 MB | 37.7 MB |

---

## 2. Provenance and Cryptographic Manifest

### `qap15`
- **Instance Name**: `qap15`
- **Problem Class**: LP benchmark instance (QAP LP relaxation)
- **Source URL**: `https://plato.asu.edu/ftp/lptestset/`
- **Direct File URL**: `https://plato.asu.edu/ftp/lptestset/qap15.mps.bz2`
- **Retrieval Date**: 2026-10-05T04:38:45+05:30 (ISO 8601)
- **Compressed SHA-256**: `edc084e9e3d8ccc5dd25f30c6593e6dbb00cba86c5e664c471d1de37ae28b68a`
- **Uncompressed Stream SHA-256**: `a24d84de54c73d7ea01ebaf07739e6884d57794d4b1184c0e01a6a4495695712`
- **Provenance / Origin**: LP relaxation of quadratic assignment problem via triangle decomposition (Karisch & Rendl 1995; Ramakrishnan et al. 2002; Mittelmann benchmark index).
- **Licence / Conditions**: Public academic benchmark maintained by Prof. Hans Mittelmann (Arizona State University).
- **Objective Sense**: Minimization
- **Published Reference Objective**: 1040.99 (Hans Mittelmann LP Benchmark, `https://plato.asu.edu/ftp/lpopt.html`)
- **Evaluation Status**: Parsed, validated, and evaluated under bounded execution (LIMIT_REACHED).

### `brazil3`
- **Instance Name**: `brazil3`
- **Problem Class**: LP benchmark instance (MIPLIB 2017 LP relaxation)
- **Source URL**: `https://plato.asu.edu/ftp/lptestset/`
- **Direct File URL**: `https://plato.asu.edu/ftp/lptestset/brazil3.mps.bz2`
- **Retrieval Date**: 2026-10-05T04:38:45+05:30 (ISO 8601)
- **Compressed SHA-256**: `7d92b6b86cbcf24bd2109b6e45931e3a01e79accd3f429971abcb934f0479c7e`
- **Uncompressed Stream SHA-256**: `28cfec922c8c239645c823b7746ae221e38a6208e827a9f040ddf50d9203d125`
- **Provenance / Origin**: Continuous LP relaxation from MIPLIB 2017 (`miplib.zib.de`), converted to LP on Plato ASU benchmark set.
- **Licence / Conditions**: Public academic benchmark maintained by Prof. Hans Mittelmann (Arizona State University).
- **Objective Sense**: Minimization
- **Published Reference Objective**: 2.0 (MIPLIB 2017 continuous relaxation / HiGHS C++ reference)
- **Evaluation Status**: Parsed, validated, and evaluated under bounded execution (LIMIT_REACHED).

### `chromaticindex1024-7`
- **Instance Name**: `chromaticindex1024-7`
- **Problem Class**: LP benchmark instance (MIPLIB 2017 LP relaxation)
- **Source URL**: `https://plato.asu.edu/ftp/lptestset/`
- **Direct File URL**: `https://plato.asu.edu/ftp/lptestset/chromaticindex1024-7.mps.bz2`
- **Retrieval Date**: 2026-10-05T04:38:45+05:30 (ISO 8601)
- **Compressed SHA-256**: `859ce3ee24403567c13176faf44ac3a9b6764c8fdd8c4e5817793b367bf9c275`
- **Uncompressed Stream SHA-256**: `5b6f1d9daf867e4d5928e8a48fd1fc5f5c1a3249a18b738f46945ff2ff721b05`
- **Provenance / Origin**: Continuous LP relaxation from MIPLIB 2017 (`miplib.zib.de`), converted to LP on Plato ASU benchmark set.
- **Licence / Conditions**: Public academic benchmark maintained by Prof. Hans Mittelmann (Arizona State University).
- **Objective Sense**: Minimization
- **Published Reference Objective**: MIPLIB 2017 continuous relaxation
- **Evaluation Status**: Parsed, validated, and evaluated under bounded execution (LIMIT_REACHED).

### `supportcase10`
- **Instance Name**: `supportcase10`
- **Problem Class**: LP benchmark instance (MIPLIB 2017 LP relaxation)
- **Source URL**: `https://plato.asu.edu/ftp/lptestset/`
- **Direct File URL**: `https://plato.asu.edu/ftp/lptestset/supportcase10.mps.bz2`
- **Retrieval Date**: 2026-10-05T04:38:45+05:30 (ISO 8601)
- **Compressed SHA-256**: `7ae9279ef7d66fec1a60be7ccf5831a0f1dbad66831d4a510e7807e293ca2bf7`
- **Uncompressed Stream SHA-256**: `e65868b17479a5a4c408af4a8e6a412c61d681918d7c9d5ad3bbe46966634f0b`
- **Provenance / Origin**: Continuous LP relaxation from MIPLIB 2017 (`miplib.zib.de`), converted to LP on Plato ASU benchmark set.
- **Licence / Conditions**: Public academic benchmark maintained by Prof. Hans Mittelmann (Arizona State University).
- **Objective Sense**: Minimization
- **Published Reference Objective**: MIPLIB 2017 continuous relaxation
- **Evaluation Status**: Parsed, validated, and evaluated under bounded execution (LIMIT_REACHED).

---

## 3. Sovereign Solver Ingestion Guarantees

1. **Zero Densification**: All files are parsed via `sovopt.mps.read_mps(..., sparse=True)` directly from `.bz2` streams into sovereign `CSRMatrix`.
2. **Memory Footprint**: Total memory footprint for all four instances combined is under 18 MB in CSR format, compared to $> 59$ GB required for theoretical dense float64 arrays.
3. **Purity**: Zero external optimizer dependencies are utilized inside `sovopt`. External solvers (e.g. HiGHS) are restricted exclusively to `scripts/baseline_worker.py` for independent differential comparisons.
