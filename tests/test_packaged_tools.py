"""Synthetic regression checks for packaged diagnostic tools; no target apps run."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
POLLUTER = ROOT / "skills/root-cause-tracing/find_polluter.py"
TRACE_SCRIPTS = ROOT / "skills/swiftui-expert-skill/scripts"
UI_SCRIPTS = ROOT / "skills/ui-ux-pro-max/scripts"
sys.path.insert(0, str(TRACE_SCRIPTS))

from instruments_parser import correlate, hangs, hitches, swiftui, time_profiler


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PolluterTests(unittest.TestCase):
    def invoke(self, directory, code, pattern="src/**/*.test.ts", runner=None):
        return subprocess.run(
            [sys.executable, str(POLLUTER), "pollution", pattern, "--",
             *(runner or [sys.executable, "-c", code, "{test}"])],
            cwd=directory, capture_output=True, text=True, check=False,
        )

    def prepare(self, directory):
        root = Path(directory)
        (root / "src/nested dir").mkdir(parents=True)
        (root / "src/first.test.ts").touch()
        (root / "src/nested dir/second test.test.ts").touch()
        return root

    def test_recursive_pattern_and_spaces_run_exact_selected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.prepare(tmp)
            result = self.invoke(tmp, "import sys; print('FILE=' + sys.argv[1])")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FILE=" + str(Path("src/first.test.ts")), result.stdout)
        self.assertIn("FILE=" + str(Path("src/nested dir/second test.test.ts")), result.stdout)
        self.assertIn("2 successful test-file runs", result.stdout)

    def test_no_matches_is_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.invoke(tmp, "raise RuntimeError('must not run')")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no test files matched", result.stderr)

    def test_failing_or_missing_runner_never_claims_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp)
            failure = self.invoke(tmp, "import sys; sys.exit(41)")
            missing = self.invoke(tmp, "", runner=[str(Path(tmp) / "missing"), "{test}"])
        for result in (failure, missing):
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("No pollution observed", result.stdout)

    def test_preexisting_pollution_is_preserved_and_runner_does_not_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.prepare(tmp)
            (root / "pollution").write_text("keep me")
            result = self.invoke(tmp, "from pathlib import Path; Path('runner-started').touch()")
            self.assertEqual((root / "pollution").read_text(), "keep me")
            self.assertFalse((root / "runner-started").exists())
        self.assertEqual(result.returncode, 2)

    def test_preexisting_broken_symlink_counts_as_pollution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.prepare(tmp)
            try:
                (root / "pollution").symlink_to("missing")
            except OSError:
                self.skipTest("host does not permit symlink creation")
            result = self.invoke(tmp, "raise RuntimeError('must not run')")
            self.assertTrue((root / "pollution").is_symlink())
        self.assertEqual(result.returncode, 2)

    def test_matching_symlink_outside_working_directory_is_not_run(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "external.test.ts"
            target.touch()
            try:
                (Path(tmp) / "external.test.ts").symlink_to(target)
            except OSError:
                self.skipTest("host does not permit symlink creation")
            result = self.invoke(tmp, "raise RuntimeError('must not run')", pattern="*.test.ts")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot discover tests", result.stderr)

    def test_created_pollution_identifies_runner_and_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.prepare(tmp)
            result = self.invoke(tmp, "from pathlib import Path; Path('pollution').touch()")
            self.assertTrue((root / "pollution").exists())
        self.assertEqual(result.returncode, 1)
        self.assertIn("while running " + str(Path("src/first.test.ts")), result.stdout)
        self.assertNotIn("[2/2]", result.stdout)

    def test_runner_is_mandatory_and_pattern_cannot_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(POLLUTER), "pollution", "*.ts"],
                                    cwd=tmp, capture_output=True, text=True)
            escape = self.invoke(tmp, "", pattern="../*.ts")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(escape.returncode, 2)


class TraceCorrelationTests(unittest.TestCase):
    @staticmethod
    def export_xml(columns):
        schema = "".join(f"<col><mnemonic>{name}</mnemonic></col>" for name in columns)
        return f"<trace><schema>{schema}</schema><row>{''.join(columns.values())}</row></trace>".encode()

    @staticmethod
    def sample(name, pid, symbol="Target.work", time_ns=1_000_000):
        return {"time_ns": time_ns, "weight_ns": 1_000_000, "is_main": True,
                "process": name, "process_identity": {"name": name, "pid": pid},
                "leaf_symbol": symbol}

    @staticmethod
    def lanes(samples, process=None):
        return {"time-profiler": {"available": True, "_samples": samples},
                "hangs": {"available": True, "_events": [{"start_ns": 0,
                    "end_ns": 5_000_000, "hang_type": "Hang", "thread": {"process": process}}]}}

    def test_other_process_cannot_be_attributed_to_target_hang(self):
        lanes = self.lanes([self.sample("Other", 2, "Other.busy")], {"name": "Target", "pid": 1})
        result = correlate.build(lanes)[0]
        self.assertNotIn("time_profiler_main_thread", result)
        self.assertIn("matching process identity", result["notes"][0])

    def test_target_pid_filters_same_named_and_unrelated_processes(self):
        samples = [self.sample("Target", 1), self.sample("Target", 2, "Wrong.work"),
                   self.sample("Other", 3, "Other.work")]
        result = correlate.build(self.lanes(samples, {"name": "Target", "pid": 1}))[0]
        tp = result["time_profiler_main_thread"]
        self.assertEqual(tp["samples_on_main"], 1)
        self.assertEqual([item["symbol"] for item in tp["hot_symbols"]], ["Target.work"])

    def test_unknown_or_ambiguous_identity_declines_attribution(self):
        for process in (None, {"name": "Target"}):
            with self.subTest(process=process):
                samples = [self.sample("Target", 1), self.sample("Target", 2)]
                result = correlate.build(self.lanes(samples, process))[0]
                self.assertNotIn("time_profiler_main_thread", result)
                self.assertTrue(result["notes"])

    def test_name_only_identity_works_when_unambiguous(self):
        result = correlate.build(self.lanes([self.sample("Target", 1)], {"name": "Target"}))[0]
        self.assertEqual(result["time_profiler_main_thread"]["samples_on_main"], 1)

    def test_hitch_and_swiftui_updates_share_only_matching_pid(self):
        lanes = self.lanes([self.sample("Target", 1), self.sample("Other", 2)], {"pid": 1})
        lanes["hitches"] = {"available": True, "_events": [{"start_ns": 0, "end_ns": 5_000_000,
            "frame_duration_ms": None, "hitch_duration_ms": 5, "process_identity": {"pid": 1}}]}
        lanes["swiftui"] = {"available": True, "_events": [
            {"start_ns": 0, "end_ns": 5_000_000, "duration_ms": 5, "start_ms": 0,
             "view": name, "process_identity": {"pid": pid}} for name, pid in (("TargetView", 1), ("OtherView", 2))]}
        for result in correlate.build(lanes):
            self.assertEqual([e["view"] for e in result["swiftui_overlapping_updates"]], ["TargetView"])

    def test_export_parsers_retain_matching_process_identity(self):
        process = '<process fmt="Target (123)"><pid>123</pid></process>'
        thread = f'<thread fmt="Main Thread"><tid>123</tid>{process}</thread>'
        cases = [
            (time_profiler, "time-profile", {"time": "<time>1000000</time>",
                "weight": "<weight>1000000</weight>", "thread": thread,
                "stack": '<stack><backtrace><frame name="Target.work"/></backtrace></stack>'}, "_samples"),
            (hangs, "potential-hangs", {"start": "<start>0</start>",
                "duration": "<duration>5000000</duration>", "thread": thread}, "_events"),
            (hitches, "hitches", {"start": "<start>0</start>",
                "duration": "<duration>5000000</duration>", "process": process}, "_events"),
            (swiftui, "swiftui-updates", {"start": "<start>0</start>",
                "duration": "<duration>5000000</duration>", "process": process}, "_events"),
        ]
        for parser, schema, columns, key in cases:
            with self.subTest(lane=schema):
                with mock.patch.object(parser.xctrace, "export_schema", return_value=self.export_xml(columns)):
                    result = parser.analyze(Path("synthetic.trace"), frozenset({schema}))
                event = result[key][0]
                identity = event["thread"]["process"] if parser is hangs else event["process_identity"]
                self.assertEqual(identity, {"name": "Target", "pid": 123})

    def test_unknown_process_explanation_is_visible_in_markdown_summary(self):
        from instruments_parser import summary
        result = correlate.build(self.lanes([self.sample("Other", 2)]))
        lines = []
        summary._render_correlations(lines, result)
        self.assertIn("trigger process identity is unavailable", "\n".join(lines))

    def test_coverage_summary_states_sampling_assumption_without_blocking_diagnosis(self):
        from instruments_parser import summary
        for samples, expected in (([self.sample("Target", 1)], "low sampled coverage"),
                                  ([self.sample("Target", 1)] * 5, "higher sampled coverage")):
            with self.subTest(expected=expected):
                result = correlate.build(self.lanes(samples, {"pid": 1}))
                lines = []
                summary._render_correlations(lines, result)
                text = "\n".join(lines)
                self.assertIn(expected, text)
                self.assertIn("assuming 1ms/sample", text)
                self.assertIn("does not establish blocking", text)
                self.assertNotIn("— blocked", text)
                self.assertIn("1ms/sample", result[0]["time_profiler_main_thread"]["coverage_assumption"])

    def test_stale_stop_file_never_starts_xctrace_or_deletes_user_file(self):
        recorder = load_module("packaged_record_trace", TRACE_SCRIPTS / "record_trace.py")
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "stop"
            marker.write_text("keep")
            with mock.patch.object(recorder.subprocess, "Popen") as start:
                with contextlib.redirect_stderr(io.StringIO()):
                    code = recorder.main(["--attach", "123", "--stop-file", str(marker),
                                          "--output", str(Path(tmp) / "out.trace")])
                start.assert_not_called()
            self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(code, 2)


class DesignPathTests(unittest.TestCase):
    def test_master_and_page_links_match_actual_persisted_layout(self):
        sys.path.insert(0, str(UI_SCRIPTS))
        try:
            module = load_module("packaged_design_system", UI_SCRIPTS / "design_system.py")
            with tempfile.TemporaryDirectory() as tmp:
                result = module.persist_design_system({"project_name": "Acme App"}, "settings", tmp)
                master = Path(result["master_file"])
                page = master.parent / "pages/settings.md"
                self.assertTrue(page.is_file())
                self.assertIn("`pages/[page-name].md` relative to this Master file", master.read_text(encoding="utf-8"))
                self.assertIn("`../MASTER.md`, relative to this page file", page.read_text(encoding="utf-8"))
                self.assertEqual((page.parent / "../MASTER.md").resolve(), master.resolve())
        finally:
            sys.path.remove(str(UI_SCRIPTS))


if __name__ == "__main__":
    unittest.main()
