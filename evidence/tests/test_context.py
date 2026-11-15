import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence" / "context"))
from measure import load_manifest, measure  # noqa: E402


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class ContextMeasurementTests(unittest.TestCase):
    def make_workspace(self, root: Path, with_resolved=True):
        project = root / "proj"
        (project / "src").mkdir(parents=True)
        (project / "src/app.ts").write_text("export const a = 1;\n" * 40)
        (project / "src/other.ts").write_text("export const b = 2;\n" * 400)
        (project / "notes.md").write_text("# untracked notes\n" * 50)
        (project / "task.yml").write_text("task: demo\n")
        (root / "AGENTS.md").write_text("route to proj\n")
        if with_resolved:
            (project / "resolved.yml").write_text("resolved_files:\n  source: proj/src/app.ts\n  list: [proj/src/app.ts]\n")
        git(project, "init", "-q")
        git(project, "add", "src", "task.yml")
        (root / "evidence").mkdir()
        manifest = {"corpusSuffixes": [".ts", ".yml", ".md"], "projects": {"demo": {
            "root": "proj", "contextProfiles": {"change": {
                "description": "demo", "instructions": ["AGENTS.md"], "task": "proj/task.yml",
                "resolved": "proj/resolved.yml", "resolveCommand": "npm run resolve"}}}}}
        (root / "evidence/projects.json").write_text(json.dumps(manifest))

    def test_selected_context_is_compared_with_tracked_project_files_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_workspace(root)
            record = measure(root, "demo", "change")
            self.assertEqual(record["status"], "complete")
            paths = [item["path"] for item in record["selected"]["items"]]
            self.assertEqual(paths, ["AGENTS.md", "proj/task.yml", "proj/resolved.yml", "proj/src/app.ts"])
            self.assertEqual(record["corpus"]["files"], 3)  # untracked notes.md is excluded
            self.assertGreater(record["selected"]["instructionTokens"], 0)
            self.assertEqual(record["selected"]["tokens"],
                             record["selected"]["instructionTokens"] + record["selected"]["taskTokens"])
            self.assertIsNotNone(record["corpusToSelectedRatio"])

    def test_missing_resolved_context_is_incomplete_with_no_ratio(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_workspace(root, with_resolved=False)
            record = measure(root, "demo", "change")
            self.assertEqual(record["status"], "incomplete")
            self.assertIsNone(record["corpusToSelectedRatio"])
            self.assertIsNone(record["selectedAsPercentOfCorpus"])
            self.assertIn("npm run resolve", record["notes"][0])

    def test_manifest_profiles_point_at_existing_files_for_present_projects(self):
        manifest = load_manifest(ROOT)
        for project, config in manifest["projects"].items():
            if not (ROOT / config["root"]).is_dir():
                continue  # independent nested repositories are absent from a workspace-only checkout
            for name, profile in config["contextProfiles"].items():
                with self.subTest(project=project, profile=name):
                    for path in [*profile.get("instructions", []), profile["task"], *profile.get("files", [])]:
                        self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
