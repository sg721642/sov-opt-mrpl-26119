# Checksum Architecture and Cross-Platform Integrity Policy

## 1. Overview and Purpose

SOV-OPT maintains an explicit repository-wide cryptographic integrity manifest (`SHA256SUMS.json`) to guarantee that benchmark datasets, solver sources, test fixtures, and documentation cannot be altered without detection.

In multi-platform development environments (such as cross-testing between macOS/Linux and Windows workstations), text files are subject to Git checkout line-ending transformations (`\r\n` on Windows vs `\n` on POSIX systems). Historically, computing raw byte SHA-256 digests indiscriminately across both binary benchmarks and normal text files caused 175 of 288 files to mismatch when verified across operating systems, despite zero true semantic differences.

Gate 9.1 introduces a dual-mode verification architecture that distinguishes byte-frozen benchmark models from canonical text files without weakening cryptographic provenance.

---

## 2. Dual-Mode Verification Architecture

Every tracked file in `SHA256SUMS.json` is classified under one of two verification modes:

```json
{
  "data/netlib/afiro.mps": {
    "sha256": "fd3562804ff19382a9cd8bcb22ec81bffd24a4143a2290783831d8c64516a24b",
    "mode": "raw"
  },
  "sovopt/pdhg.py": {
    "sha256": "2582845c4883495d465d3ecde1b20be80164c017bc9a0ebf35f8d070b4be911b",
    "mode": "text-lf"
  }
}
```

### 2.1 Mode `raw`: Byte-Exact Canonical Verification
- **Verification Rule:** `hashlib.sha256(path.read_bytes()).hexdigest()`
- **Applied To:**
  - All optimization model and instance files (`*.mps`, `*.qplib`, `*.sol`, `*.solu`, `*.lp`).
  - Primary provenance manifests under `data/manifests/` (`netlib_lp.json`, `miplib_milp.json`, `qplib_convex_qp.json`, `gpu_pdhg_lp.json`, `gpu_pdhg_large_public.json`).
  - Verified benchmark fixture JSONs (`data/verified/*.json`).
  - Raw downloaded artifacts (`data/raw/*_raw`).
  - Any binary media or compiled assets (`.png`, `.pdf`, `.bin`, `.gz`).
- **Enforcement:** These files are declared `-text` in `.gitattributes`. Git is prohibited from performing any CRLF or newline conversion on them during checkout, commit, or transfer. Their byte sequence is identical on all platforms.

### 2.2 Mode `text-lf`: Canonical LF Text Verification
- **Verification Rule:** `hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()`
- **Applied To:**
  - Source code (`sovopt/*.py`, `server.py`).
  - Test suites (`tests/*.py`).
  - Automation scripts (`scripts/*.py`, `scripts/*.sh`).
  - Documentation and reports (`docs/*.md`, `reports/*.md`, `reports/*.json`).
  - Web and configuration files (`web/*.html`, `pyproject.toml`, `.gitattributes`).
- **Rationale:** Normal source and documentation files are subject to local editor conventions and Git line-ending conversions on checkout (`core.autocrlf` or `eol=crlf`). Normalizing `\r\n` to `\n` before computing the digest ensures that verification evaluates the identical canonical text content on Windows, macOS, and Linux.
- **Integrity Guarantee:** Any change to code logic, whitespace, indentation, comments, or values alters the canonical text digest and fails verification. Only the OS carriage-return artifact (`\r`) is normalized.

---

## 3. Benchmark Provenance Protection

Public continuous LP, discrete MILP, and convex QP benchmark datasets (Netlib, MIPLIB, QPLIB) must never have their provenance hashes altered to accommodate local OS quirks.
- All 81 active public benchmark instances across the 5 submanifests are verified exclusively under `mode: "raw"`.
- The SHA-256 digests in `SHA256SUMS.json` match the digests recorded in `data/CATALOGUE.md` and the submanifests bit-for-bit.
- Changing even a single byte in any benchmark model causes `verify_checksums.py` to abort with a verification failure.

---

## 4. Verification Procedure

To verify repository integrity on any platform:

```bash
# Sandboxed / standard command line:
python scripts/verify_checksums.py
```

Expected output on macOS, Linux, and Windows:
```
SUCCESS: All entries in SHA256SUMS.json are valid and match working tree.
```

To update `SHA256SUMS.json` after legitimate code or documentation edits:
```bash
python scripts/verify_checksums.py --update
```
