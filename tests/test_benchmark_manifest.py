"""Immutability, provenance, and integrity tests for frozen benchmark suites.

Verifies:
1. Manifest schema version and metadata integrity
2. Existence and cryptographic SHA-256 match for every referenced file in manifests
3. Directional validity of all MIPLIB safe bounds against published references
4. Exclusion of refinery formulations from public benchmark counts
5. Exclusion of quarantined datasets (e.g. AVGAS) from verified counts
6. Isolation of negative rejection test cases (e.g. QPLIB_0018) from convex counts
7. Alignment between reports/FROZEN_BENCHMARK_SELECTION.md and data/manifest.json
"""

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class TestBenchmarkManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master_file = ROOT / "data/manifest.json"
        with open(cls.master_file, "r") as f:
            cls.master = json.load(f)

        cls.netlib_file = ROOT / "data/manifests/netlib_lp.json"
        with open(cls.netlib_file, "r") as f:
            cls.netlib = json.load(f)

        cls.miplib_file = ROOT / "data/manifests/miplib_milp.json"
        with open(cls.miplib_file, "r") as f:
            cls.miplib = json.load(f)

        cls.qplib_file = ROOT / "data/manifests/qplib_convex_qp.json"
        with open(cls.qplib_file, "r") as f:
            cls.qplib = json.load(f)

    def test_01_manifest_schema_and_version(self):
        self.assertEqual(self.master.get("schema_version"), "2.0.0")
        self.assertEqual(self.master.get("solver_version"), "0.3.1")
        self.assertIn("submanifests", self.master)
        self.assertIn("disclosures", self.master)
        self.assertIn("counts", self.master)

    def test_02_all_referenced_files_exist_with_matching_sha256(self):
        all_manifests = [
            ("Netlib", self.netlib),
            ("MIPLIB", self.miplib),
            ("QPLIB", self.qplib)
        ]
        total_checked = 0
        for suite_name, m_dict in all_manifests:
            for inst_name, entry in m_dict.items():
                local_rel = entry["local_file"]
                local_path = ROOT / local_rel
                self.assertTrue(
                    local_path.is_file(),
                    f"[{suite_name}] Referenced file missing on disk: {local_rel}"
                )
                actual_hash = sha256_file(local_path)
                self.assertEqual(
                    actual_hash, entry["SHA256"],
                    f"[{suite_name}] SHA-256 mismatch for {inst_name} ({local_rel})"
                )
                total_checked += 1
        self.assertGreaterEqual(total_checked, 55, "Expected at least 55 frozen instances")

    def test_03_miplib_bound_directional_safety(self):
        for name, entry in self.miplib.items():
            ref_opt = entry.get("reference_objective")
            ref_bnd = entry.get("reference_bound")
            if ref_opt is not None and ref_bnd is not None:
                self.assertLessEqual(
                    ref_bnd, ref_opt + 1e-6,
                    f"MIPLIB bound violation on {name}: bound {ref_bnd} > opt {ref_opt}"
                )

    def test_04_refinery_excluded_from_public_benchmark_counts(self):
        for name in self.netlib:
            self.assertNotIn("refinery", name.lower())
        for name in self.miplib:
            self.assertNotIn("refinery", name.lower())
        for name in self.qplib:
            self.assertNotIn("refinery", name.lower())

        self.assertIn("proprietary_mrpl_data", self.master["disclosures"])
        self.assertIn("No authorized proprietary MRPL operating data", self.master["disclosures"]["proprietary_mrpl_data"])

    def test_05_quarantined_datasets_excluded_from_verified_counts(self):
        for name in self.netlib:
            self.assertNotEqual(name.lower(), "avgas")
        for name in self.miplib:
            self.assertNotEqual(name.lower(), "avgas")
        for name in self.qplib:
            self.assertNotEqual(name.lower(), "avgas")

    def test_06_negative_rejection_tests_isolated(self):
        qplib_0018 = self.qplib.get("QPLIB_0018")
        self.assertIsNotNone(qplib_0018, "QPLIB_0018 must be retained in QPLIB manifest")
        self.assertFalse(qplib_0018["is_supported"], "QPLIB_0018 must be flagged as unsupported")
        self.assertEqual(qplib_0018["selection_rule"], "UNSUPPORTED_NONCONVEX_QP")

        counts = self.master["counts"]
        self.assertEqual(counts["qplib_convex_selected"], 3)
        self.assertEqual(counts["qplib_negative_tests"], 1)

    def test_07_frozen_selection_report_matches_manifest(self):
        report_file = ROOT / "reports/FROZEN_BENCHMARK_SELECTION.md"
        self.assertTrue(report_file.is_file(), "reports/FROZEN_BENCHMARK_SELECTION.md missing")
        content = report_file.read_text()
        self.assertIn("QPLIB_8845", content)
        self.assertIn("QPLIB_0018", content)
        self.assertIn("WOODINFE", content)
        self.assertIn("FLUGPL", content.upper())

if __name__ == "__main__":
    unittest.main()
