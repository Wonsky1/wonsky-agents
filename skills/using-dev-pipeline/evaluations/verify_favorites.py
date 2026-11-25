"""Check the favorites evaluation contract through fresh CLI processes only."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class FavoritesContract(unittest.TestCase):
    """Observable functionality; no assertions about target implementation shape."""

    target = None

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = Path(self.temporary.name) / "favorites.json"
        self.store.write_text(json.dumps(["alpha", "beta", "gamma", "delta"]) + "\n")

    def invoke(self, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "favorites", "--store", str(self.store), *arguments],
            cwd=self.target, capture_output=True, text=True, timeout=15, check=False,
        )

    def listed(self):
        result = self.invoke("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        return [identifier for identifier in result.stdout.splitlines() if identifier != ""]

    def remove(self, identifiers):
        result = self.invoke("remove-many", json.dumps(identifiers))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_removal_survives_restart_preserves_order_and_ignores_unknown_duplicates(self):
        self.remove(["gamma", "absent", "alpha", "gamma"])
        self.assertEqual(self.listed(), ["beta", "delta"])
        self.assertEqual(json.loads(self.store.read_text()), ["beta", "delta"])

    def test_empty_selection_preserves_contents(self):
        self.remove([])
        self.assertEqual(self.listed(), ["alpha", "beta", "gamma", "delta"])

    def test_all_selected_can_be_removed(self):
        self.remove(["delta", "alpha", "gamma", "beta"])
        self.assertEqual(self.listed(), [])
        self.assertEqual(json.loads(self.store.read_text()), [])

    def test_invalid_requests_fail_before_storage_mutation(self):
        for raw in ('not-json', '{}', 'null', '"alpha"', '[""]', '[1]', '[null]',
                    '[true]', '["alpha", ""]', '["alpha", 2]'):
            with self.subTest(raw=raw):
                before = (self.store.read_bytes(), self.store.stat().st_mtime_ns)
                result = self.invoke("remove-many", raw)
                self.assertNotEqual(result.returncode, 0, raw)
                after = (self.store.read_bytes(), self.store.stat().st_mtime_ns)
                self.assertEqual(after, before, raw)

    def test_invalid_request_does_not_create_missing_store(self):
        self.store.unlink()
        result = self.invoke("remove-many", '["alpha", ""]')
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.store.exists())

    def test_add_and_list_remain_compatible_after_removal(self):
        self.remove(["beta"])
        for identifier in ("epsilon", "alpha"):
            result = self.invoke("add", identifier)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.listed(), ["alpha", "gamma", "delta", "epsilon"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Completed disposable favorites fixture")
    args = parser.parse_args()
    target = args.target.resolve()
    if not (target / "favorites/__main__.py").is_file():
        parser.error("target must contain the favorites CLI fixture")
    FavoritesContract.target = target
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FavoritesContract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
