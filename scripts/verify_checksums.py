#!/usr/bin/env python3
"""Cross-platform checksum verification and generation tool for SOV-OPT.

Supports two verification modes:
  - 'raw': Raw byte-for-byte SHA-256 verification (used for frozen benchmark
    models, manifests, and binary assets).
  - 'text-lf': Canonical LF-normalized SHA-256 verification (used for source code,
    documentation, and repository bookkeeping files subject to OS checkout EOL
    conversions).

Usage:
  .venv/bin/python scripts/verify_checksums.py          # Verify all checksums
  .venv/bin/python scripts/verify_checksums.py --update # Regenerate SHA256SUMS.json
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKSUM_FILE = ROOT / "SHA256SUMS.json"

RAW_EXTENSIONS = {
    ".mps", ".qplib", ".sol", ".solu", ".lp",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
    ".gz", ".zip", ".tar", ".bin", ".pyc",
}


def determine_mode(rel_path: str) -> str:
    """Classify a tracked file as 'raw' (byte-exact) or 'text-lf' (canonical text).

    Rule hierarchy:
    1. Benchmark data files, models, and solutions (*.mps, *.qplib, *.sol, *.solu, *.lp)
       must remain byte-frozen -> 'raw'.
    2. Primary data manifests under data/manifests/ contain frozen SHA-256 provenance -> 'raw'.
    3. Verified JSON benchmark models in data/verified/ -> 'raw'.
    4. Raw benchmark files without standard extensions in data/raw/ (*_raw) -> 'raw'.
    5. Binary media and archives -> 'raw'.
    6. All other repository files (Python source, markdown docs, tests, scripts, web,
       config) are normal text files -> 'text-lf'.
    """
    ext = Path(rel_path).suffix.lower()
    if ext in RAW_EXTENSIONS:
        return "raw"
    if rel_path.startswith("data/raw/") and rel_path.endswith("_raw"):
        return "raw"
    if rel_path.startswith("data/manifests/"):
        return "raw"
    if rel_path.startswith("data/verified/") and ext == ".json":
        return "raw"
    return "text-lf"


def compute_sha256(path: Path, mode: str = "raw") -> str:
    """Compute standard SHA-256 hex digest for a file under specified mode.

    Modes:
      - 'raw': Hashes raw disk bytes without modification.
      - 'text-lf': Hashes canonical text with CRLF normalized to LF (\\r\\n -> \\n).
    """
    data = path.read_bytes()
    if mode == "text-lf":
        data = data.replace(b"\r\n", b"\n")
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def get_tracked_files(root: Path) -> list[str]:
    """Get list of tracked files in the repository, excluding SHA256SUMS.json."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True
        )
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception:
        files = []
        for p in root.rglob("*"):
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts):
                files.append(str(p.relative_to(root)))

    covered = [f for f in files if f != "SHA256SUMS.json" and not f.startswith(".git/")]
    covered.sort()
    return covered


def generate_checksums(root: Path = ROOT) -> dict[str, dict[str, str]]:
    """Generate canonical SHA-256 manifest across all covered files and write SHA256SUMS.json."""
    covered = get_tracked_files(root)
    manifest = {}
    for rel_path in covered:
        p = root / rel_path
        if p.exists() and p.is_file():
            mode = determine_mode(rel_path)
            h = compute_sha256(p, mode=mode)
            manifest[rel_path] = {
                "sha256": h,
                "mode": mode,
            }

    out_path = root / "SHA256SUMS.json"
    content = json.dumps(manifest, indent=2) + "\n"
    out_path.write_bytes(content.encode("utf-8"))
    return manifest


def verify_checksums(root: Path = ROOT) -> tuple[bool, list[str]]:
    """Parse and verify SHA256SUMS.json against current files across operating systems.

    Returns (is_valid, list_of_error_messages).
    """
    out_path = root / "SHA256SUMS.json"
    if not out_path.exists():
        return False, ["SHA256SUMS.json does not exist"]

    raw_bytes = out_path.read_bytes()
    if raw_bytes.endswith(b"\\n"):
        return False, ["SHA256SUMS.json contains literal trailing \\n characters instead of a real newline"]

    try:
        manifest = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        return False, [f"Failed to parse SHA256SUMS.json with json.loads: {e}"]

    errors = []
    if "SHA256SUMS.json" in manifest:
        errors.append("SHA256SUMS.json must not list itself in its checksum entries")

    for rel_path, entry in manifest.items():
        p = root / rel_path
        if not p.exists():
            errors.append(f"Missing file: {rel_path}")
            continue

        if isinstance(entry, dict):
            expected_hash = entry.get("sha256")
            mode = entry.get("mode", "raw")
        elif isinstance(entry, str):
            # Backward compatibility with legacy string-only schema
            expected_hash = entry
            mode = "raw"
        else:
            errors.append(f"Invalid manifest entry format for {rel_path}: {entry}")
            continue

        actual_hash = compute_sha256(p, mode=mode)
        if actual_hash != expected_hash:
            errors.append(
                f"Hash mismatch on {rel_path} (mode={mode}):\n  expected: {expected_hash}\n  actual:   {actual_hash}"
            )

    tracked = set(get_tracked_files(root))
    manifest_files = set(manifest.keys())
    missing_from_manifest = tracked - manifest_files
    for f in sorted(missing_from_manifest):
        errors.append(f"Tracked file not listed in SHA256SUMS.json: {f}")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="SOV-OPT Cross-Platform SHA-256 Checksum Tool")
    parser.add_argument("--update", action="store_true", help="Regenerate SHA256SUMS.json")
    args = parser.parse_args()

    if args.update:
        manifest = generate_checksums(ROOT)
        print(f"Generated SHA256SUMS.json with {len(manifest)} entries.")
        ok, errors = verify_checksums(ROOT)
        if not ok:
            print("Immediate verification failed:", file=sys.stderr)
            for err in errors:
                print(f"  ERROR: {err}", file=sys.stderr)
            sys.exit(1)
        print("Verification passed successfully.")
        sys.exit(0)

    ok, errors = verify_checksums(ROOT)
    if not ok:
        print(f"FAILED: Found {len(errors)} checksum/manifest error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    print("SUCCESS: All entries in SHA256SUMS.json are valid and match working tree.")
    sys.exit(0)


if __name__ == "__main__":
    main()
