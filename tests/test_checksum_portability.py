"""Tests for Gate 9.1: Cross-Platform Checksum Portability and Provenance Hardening.

Verifies:
1. Canonical LF text files verify under text-lf mode.
2. CRLF-encoded text files verify under text-lf mode (cross-platform EOL portability).
3. Raw mode preserves exact byte fidelity and does not normalize line endings.
4. Benchmark raw-byte modifications correctly fail verification.
5. Missing files are detected and reported descriptively.
6. Genuine text modifications (non-EOL changes) fail verification.
7. Schema validation supports both explicit mode dictionary and legacy string formats.
8. All public benchmark provenance manifests remain frozen and verified in raw mode.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify_checksums import (
    compute_sha256,
    determine_mode,
    generate_checksums,
    verify_checksums,
)

ROOT = Path(__file__).resolve().parent.parent


class TestChecksumPortability(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_lf_text_file_verifies(self):
        """1. LF text file computes correct canonical hash and verifies cleanly."""
        p = self.test_root / "sample.py"
        p.write_bytes(b"def foo():\n    return 42\n")

        expected_hash = hashlib.sha256(b"def foo():\n    return 42\n").hexdigest()
        actual_hash = compute_sha256(p, mode="text-lf")
        self.assertEqual(actual_hash, expected_hash)

    def test_02_crlf_text_file_verifies_under_text_lf_mode(self):
        """2. Same logical text with CRLF line endings produces identical hash under text-lf mode."""
        p_lf = self.test_root / "sample_lf.py"
        p_crlf = self.test_root / "sample_crlf.py"

        content_lf = b"def foo():\n    return 42\n"
        content_crlf = b"def foo():\r\n    return 42\r\n"

        p_lf.write_bytes(content_lf)
        p_crlf.write_bytes(content_crlf)

        hash_lf = compute_sha256(p_lf, mode="text-lf")
        hash_crlf = compute_sha256(p_crlf, mode="text-lf")

        self.assertEqual(hash_lf, hash_crlf, "text-lf mode must yield identical SHA for LF and CRLF")

    def test_03_raw_mode_does_not_normalize_bytes(self):
        """3. Raw mode hashes bytes verbatim and does NOT normalize CRLF to LF."""
        p_lf = self.test_root / "data_lf.mps"
        p_crlf = self.test_root / "data_crlf.mps"

        content_lf = b"NAME          TEST\nROWS\n N  OBJ\n"
        content_crlf = b"NAME          TEST\r\nROWS\r\n N  OBJ\r\n"

        p_lf.write_bytes(content_lf)
        p_crlf.write_bytes(content_crlf)

        hash_lf = compute_sha256(p_lf, mode="raw")
        hash_crlf = compute_sha256(p_crlf, mode="raw")

        self.assertNotEqual(hash_lf, hash_crlf, "raw mode must strictly distinguish CRLF from LF")
        self.assertEqual(hash_lf, hashlib.sha256(content_lf).hexdigest())
        self.assertEqual(hash_crlf, hashlib.sha256(content_crlf).hexdigest())

    def test_04_benchmark_raw_byte_mismatch_fails(self):
        """4. A raw-mode benchmark file with modified bytes fails verification."""
        p = self.test_root / "model.mps"
        p.write_bytes(b"ORIGINAL_BYTES")

        manifest = {
            "model.mps": {
                "sha256": compute_sha256(p, mode="raw"),
                "mode": "raw",
            }
        }
        (self.test_root / "SHA256SUMS.json").write_text(json.dumps(manifest))

        # Corrupt one byte
        p.write_bytes(b"CORRUPTED_BYTE")

        ok, errors = verify_checksums(self.test_root)
        self.assertFalse(ok)
        self.assertTrue(any("Hash mismatch on model.mps (mode=raw)" in err for err in errors))

    def test_05_missing_file_fails(self):
        """5. A file listed in manifest that is missing from disk triggers failure."""
        manifest = {
            "nonexistent.txt": {
                "sha256": "0" * 64,
                "mode": "text-lf",
            }
        }
        (self.test_root / "SHA256SUMS.json").write_text(json.dumps(manifest))

        ok, errors = verify_checksums(self.test_root)
        self.assertFalse(ok)
        self.assertTrue(any("Missing file: nonexistent.txt" in err for err in errors))

    def test_06_modified_text_content_fails(self):
        """6. Genuine text modification (not line ending change) fails verification under text-lf mode."""
        p = self.test_root / "module.py"
        p.write_bytes(b"x = 100\n")

        manifest = {
            "module.py": {
                "sha256": compute_sha256(p, mode="text-lf"),
                "mode": "text-lf",
            }
        }
        (self.test_root / "SHA256SUMS.json").write_text(json.dumps(manifest))

        # Change logic
        p.write_bytes(b"x = 200\n")

        ok, errors = verify_checksums(self.test_root)
        self.assertFalse(ok)
        self.assertTrue(any("Hash mismatch on module.py (mode=text-lf)" in err for err in errors))

    def test_07_schema_validation_and_backward_compatibility(self):
        """7. Verifier supports both explicit mode dictionary and legacy string schemas."""
        p = self.test_root / "file.txt"
        p.write_bytes(b"content\n")
        h = hashlib.sha256(b"content\n").hexdigest()

        # Schema A: Dictionary with explicit mode
        manifest_a = {"file.txt": {"sha256": h, "mode": "raw"}}
        (self.test_root / "SHA256SUMS.json").write_text(json.dumps(manifest_a))
        ok_a, errors_a = verify_checksums(self.test_root)
        self.assertTrue(ok_a, f"Dictionary schema failed: {errors_a}")

        # Schema B: Legacy string hash
        manifest_b = {"file.txt": h}
        (self.test_root / "SHA256SUMS.json").write_text(json.dumps(manifest_b))
        ok_b, errors_b = verify_checksums(self.test_root)
        self.assertTrue(ok_b, f"Legacy string schema failed: {errors_b}")

    def test_08_public_benchmark_provenance_hashes_unchanged(self):
        """8. All 81 public benchmark instances across 5 manifests remain byte-frozen in raw mode."""
        sums_file = ROOT / "SHA256SUMS.json"
        self.assertTrue(sums_file.exists())
        checksums = json.loads(sums_file.read_text())

        manifest_files = [
            ROOT / "data/manifests/netlib_lp.json",
            ROOT / "data/manifests/miplib_milp.json",
            ROOT / "data/manifests/qplib_convex_qp.json",
            ROOT / "data/manifests/gpu_pdhg_lp.json",
            ROOT / "data/manifests/gpu_pdhg_large_public.json",
        ]

        total_checked = 0
        for mf in manifest_files:
            data = json.loads(mf.read_text())
            for name, meta in data.items():
                if isinstance(meta, dict) and "local_file" in meta and "SHA256" in meta:
                    rel_path = meta["local_file"]
                    expected_sha = meta["SHA256"]
                    self.assertIn(rel_path, checksums, f"Manifest file {rel_path} must be in SHA256SUMS.json")
                    entry = checksums[rel_path]
                    self.assertEqual(entry["mode"], "raw", f"{rel_path} must be classified as mode=raw")
                    self.assertEqual(entry["sha256"], expected_sha, f"SHA mismatch for {rel_path}")

                    # Verify actual on-disk file
                    local_f = ROOT / rel_path
                    self.assertTrue(local_f.exists(), f"File missing: {local_f}")
                    disk_sha = hashlib.sha256(local_f.read_bytes()).hexdigest()
                    self.assertEqual(disk_sha, expected_sha, f"Disk SHA mismatch for {rel_path}")
                    total_checked += 1

        self.assertEqual(total_checked, 81, "Expected exactly 81 benchmark instances checked")


if __name__ == "__main__":
    unittest.main()
