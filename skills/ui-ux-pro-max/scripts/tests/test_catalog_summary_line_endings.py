"""Validate the shipped catalog snapshot without upstream maintenance tooling."""

import hashlib
import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"


class CatalogSummaryLineEndingsTest(unittest.TestCase):
    def test_committed_snapshot_matches_normalized_sources(self):
        summary = json.loads((DATA / "catalog-summary.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["snapshots"], "snapshot must contain source fingerprints")
        for name, snapshot in summary["snapshots"].items():
            with self.subTest(source=name):
                raw = (DATA / name).read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(hashlib.sha256(raw).hexdigest(), snapshot["sha256"])
                simulated_crlf = raw.replace(b"\n", b"\r\n")
                self.assertEqual(
                    hashlib.sha256(simulated_crlf.replace(b"\r\n", b"\n")).hexdigest(),
                    snapshot["sha256"],
                )


if __name__ == "__main__":
    unittest.main()
