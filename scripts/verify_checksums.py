#!/usr/bin/env python3
"""Checksum verification and generation tool for SOV-OPT.

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


def compute_sha256(path: Path) -> str:
    """Compute standard SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
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


def generate_checksums(root: Path = ROOT) -> dict[str, str]:
    """Generate SHA-256 manifest across all covered files and write SHA256SUMS.json."""
    covered = get_tracked_files(root)
    manifest = {}
    for rel_path in covered:
        p = root / rel_path
        if p.exists() and p.is_file():
            manifest[rel_path] = compute_sha256(p)

    out_path = root / "SHA256SUMS.json"
    content = json.dumps(manifest, indent=2) + "\n"
    out_path.write_bytes(content.encode("utf-8"))
    return manifest


def verify_checksums(root: Path = ROOT) -> tuple[bool, list[str]]:
    """Parse and verify SHA256SUMS.json against current files.

    Returns (is_valid, list_of_error_messages).
    """
    out_path = root / "SHA256SUMS.json"
    if not out_path.exists():
        return False, ["SHA256SUMS.json does not exist"]

    raw_bytes = out_path.read_bytes()
    if raw_bytes.endswith(b"\\n"):
        return False, ["SHA256SUMS.json contains literal trailing \n characters instead of a real newline"]

    try:
        manifest = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        return False, [f"Failed to parse SHA256SUMS.json with json.loads: {e}"]

    errors = []
    if "SHA256SUMS.json" in manifest:
        errors.append("SHA256SUMS.json must not list itself in its checksum entries")

    for rel_path, expected_hash in manifest.items():
        p = root / rel_path
        if not p.exists():
            errors.append(f"Missing file: {rel_path}")
        else:
            actual_hash = compute_sha256(p)
            if actual_hash != expected_hash:
                errors.append(
                    f"Hash mismatch on {rel_path}:\n  expected: {expected_hash}\n  actual:   {actual_hash}"
                )

    tracked = set(get_tracked_files(root))
    manifest_files = set(manifest.keys())
    missing_from_manifest = tracked - manifest_files
    for f in sorted(missing_from_manifest):
        errors.append(f"Tracked file not listed in SHA256SUMS.json: {f}")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="SOV-OPT SHA-256 Checksum Tool")
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
