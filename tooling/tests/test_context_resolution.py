"""Exercise real resolver CLIs in isolated workspaces, without models or services."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling/scripts"))
from context_paths import API_TASK, API_RESOLVED, UI_TASK, UI_RESOLVED, resolved_path
from resolve_context import build_resolved as resolve_api
from resolve_ui_context import build_resolved as resolve_ui
from build_test_graph import build_graph
from build_qa_dashboard import build_dashboard
from context_efficiency_report import task_profile_stats


class ContextResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        for task_path, resolver in [(API_TASK, resolve_api), (UI_TASK, resolve_ui)]:
            task = yaml.safe_load((ROOT / task_path).read_text())
            files = resolver(ROOT, task)["resolved_files"].values()
            for relative in [task_path, *files]:
                target = self.workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)

    def run_resolver(self, ui=False, *args):
        script = "resolve_ui_context.py" if ui else "resolve_context.py"
        return subprocess.run(
            [sys.executable, str(ROOT / "tooling/scripts" / script),
             "--workspace", str(self.workspace), *map(str, args)],
            text=True, capture_output=True,
        )

    def write_task(self, example, name):
        target = self.workspace / example.parent / f"{name}.yml"
        task = yaml.safe_load((self.workspace / example).read_text())
        task["work_item"]["key"] = name
        target.write_text(yaml.safe_dump(task))
        return target

    def test_defaults_use_project_examples_without_recreating_shared_current(self):
        for ui, task, output in [(False, API_TASK, API_RESOLVED), (True, UI_TASK, UI_RESOLVED)]:
            with self.subTest(ui=ui):
                result = self.run_resolver(ui)
                self.assertEqual(result.returncode, 0, result.stderr)
                resolved = yaml.safe_load((self.workspace / output).read_text())
                self.assertEqual(resolved["task_context"]["path"], str(task))
                self.assertEqual(resolved["generated"]["output"], str(output))
                for file in resolved["resolved_files"].values():
                    self.assertTrue((self.workspace / file).is_file(), file)
        self.assertFalse((self.workspace / "agent-system/contexts/current").exists())

    def test_distinct_tasks_keep_separate_outputs_and_actual_provenance(self):
        for ui, example in [(False, API_TASK), (True, UI_TASK)]:
            first = self.write_task(example, "FIRST")
            second = self.write_task(example, "SECOND")
            result = self.run_resolver(ui, "--context", first)
            self.assertEqual(result.returncode, 0, result.stderr)
            original = resolved_path(first).read_bytes()
            result = self.run_resolver(ui, "--context", second.relative_to(self.workspace))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(resolved_path(first).read_bytes(), original)
            resolved = yaml.safe_load(resolved_path(second).read_text())
            self.assertEqual(resolved["task_context"]["path"], str(second.relative_to(self.workspace)))
            self.assertEqual(resolved["task_context"]["work_item"]["key"], "SECOND")
            self.assertEqual(resolved["task_context"]["sha256"], hashlib.sha256(second.read_bytes()).hexdigest())

    def test_output_override_isolates_two_sessions_of_one_task(self):
        for ui, task in [(False, API_TASK), (True, UI_TASK)]:
            for session in ["session-one", "session-two"]:
                output = Path("artifacts") / session / "resolved.yml"
                result = self.run_resolver(ui, "--context", task, "--output", output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((self.workspace / output).is_file())
            self.assertFalse((self.workspace / resolved_path(task)).exists())

    def test_invalid_tasks_and_input_overwrite_fail_without_damaging_source(self):
        for ui, task in [(False, API_TASK), (True, UI_TASK)]:
            source = self.workspace / task
            before = source.read_bytes()
            result = self.run_resolver(ui, "--context", task, "--output", task)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not overwrite", result.stderr)
            self.assertEqual(source.read_bytes(), before)
            invalid = source.with_name("INVALID.yml")
            for content in ["- not a mapping\n", "{}\n"]:
                invalid.write_text(content)
                result = self.run_resolver(ui, "--context", invalid)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(resolved_path(invalid).exists())

    def test_missing_context_and_outside_workspace_fail_without_outputs(self):
        for ui in [False, True]:
            result = self.run_resolver(ui, "--context", "missing.yml")
            self.assertNotEqual(result.returncode, 0)
            result = self.run_resolver(ui, "--context", ROOT / API_TASK)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("inside --workspace", result.stderr)
        self.assertFalse((self.workspace / ".resolved").exists())

    def test_runtime_facts_follow_playwright_config_with_explicit_task_override(self):
        config = self.workspace / UI_TASK.parents[2] / "playwright/playwright.config.ts"
        config.write_text(config.read_text().replace("127.0.0.1:5173", "127.0.0.1:5279"))
        result = self.run_resolver(True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.workspace / UI_RESOLVED
        self.assertEqual(yaml.safe_load(output.read_text())["ui_context"]["runtime"]["app_url"], "http://127.0.0.1:5279")
        task_path = self.workspace / UI_TASK
        task = yaml.safe_load(task_path.read_text())
        task["runtime"] = {"app_url": "http://127.0.0.1:5280"}
        task_path.write_text(yaml.safe_dump(task))
        result = self.run_resolver(True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(yaml.safe_load(output.read_text())["ui_context"]["runtime"]["app_url"], "http://127.0.0.1:5280")

    def test_views_follow_selected_resolved_tasks_instead_of_examples(self):
        outputs = []
        for ui, example in [(False, API_TASK), (True, UI_TASK)]:
            task = self.write_task(example, "SELECTED")
            result = self.run_resolver(ui, "--context", task)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(resolved_path(task).relative_to(self.workspace))
        graph = build_graph(self.workspace, *outputs)
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(nodes["api-context"]["label"], "SELECTED.yml")
        self.assertEqual(nodes["ui-context"]["label"], "SELECTED.yml")
        with patch("build_qa_dashboard.current_commit", return_value=""):
            dashboard = build_dashboard(self.workspace, *outputs)
        self.assertEqual(dashboard["ticket"]["api"]["key"], "SELECTED")
        self.assertEqual(dashboard["ticket"]["ui"]["key"], "SELECTED")

    def test_context_report_profile_uses_selected_task(self):
        task = self.write_task(API_TASK, "REPORT-TASK")
        result = self.run_resolver(False, "--context", task)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = task_profile_stats(self.workspace, "api-test-change", task)
        files = [entry["path"] for entry in report["files"]]
        self.assertIn(str(task.relative_to(self.workspace)), files)
        self.assertIn(str(resolved_path(task).relative_to(self.workspace)), files)
        self.assertNotIn(str(API_TASK), files)

    def test_views_reject_missing_empty_wrong_kind_and_stale_maps(self):
        for ui in [False, True]:
            result = self.run_resolver(ui)
            self.assertEqual(result.returncode, 0, result.stderr)
        invalid = self.workspace / "invalid-selected.yml"
        for build in [build_graph, build_dashboard]:
            with self.subTest(view=build.__name__, case="missing"):
                with self.assertRaisesRegex(SystemExit, "not found"):
                    build(self.workspace, Path("missing-selected.yml"))
            invalid.write_text("{}\n")
            with self.subTest(view=build.__name__, case="empty"):
                with self.assertRaisesRegex(SystemExit, "Invalid resolved api context shape"):
                    build(self.workspace, invalid)
            with self.subTest(view=build.__name__, case="wrong-kind"):
                with self.assertRaisesRegex(SystemExit, "Invalid resolved api context shape"):
                    build(self.workspace, UI_RESOLVED)
        source = self.workspace / API_TASK
        source.write_text(source.read_text() + "\n# task changed after resolution\n")
        for build in [build_graph, build_dashboard]:
            with self.subTest(view=build.__name__, case="stale"):
                with self.assertRaisesRegex(SystemExit, "Stale resolved api context"):
                    build(self.workspace)


if __name__ == "__main__":
    unittest.main()
