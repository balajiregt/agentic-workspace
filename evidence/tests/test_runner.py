import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence" / "trials"))
import runner  # noqa: E402


class TrialRunnerTests(unittest.TestCase):
    def test_baseline_loses_all_agent_guidance_including_nested_instruction_files(self):
        with tempfile.TemporaryDirectory() as temp:
            arm = Path(temp)
            for path in ["AGENTS.md", "quality/AGENTS.md", "CLAUDE.md", ".agents/skills/x/SKILL.md",
                         "contexts/tasks/t.yml", "src/app.ts", ".github/workflows/ci.yml"]:
                (arm / path).parent.mkdir(parents=True, exist_ok=True)
                (arm / path).write_text("x")
            removed = runner.remove_guidance(arm, ["AGENTS.md", "CLAUDE.md", ".agents", "contexts"])
            self.assertIn("quality/AGENTS.md", removed)
            remaining = sorted(p.relative_to(arm).as_posix() for p in arm.rglob("*") if p.is_file())
            self.assertEqual(remaining, [".github/workflows/ci.yml", "src/app.ts"])

    def test_framework_arm_gets_outside_files_and_a_pointer_from_agents_md(self):
        with tempfile.TemporaryDirectory() as temp:
            arm = Path(temp)
            (arm / "AGENTS.md").write_text("# Project rules\n")
            profile = {"instructions": ["AGENTS.md", "qa/playwright-agent/AGENTS.md"],
                       "task": "qa/playwright-agent/contexts/tasks/CRM-DEMO-001/epic.md"}
            (arm / ".agents/skills/x").mkdir(parents=True)
            added = runner.add_workspace_context(arm, "qa/playwright-agent", profile)
            self.assertEqual(added, [".workspace-context/AGENTS.md", "contexts/tasks/CRM-DEMO-001/epic.md",
                                     "CLAUDE.md", ".claude/skills -> ../.agents/skills"])
            # Claude Code reads CLAUDE.md and .claude/skills: both must bridge to the same guidance.
            self.assertEqual((arm / "CLAUDE.md").read_text(), "@AGENTS.md\n")
            self.assertEqual((arm / ".claude/skills").resolve(), (arm / ".agents/skills").resolve())
            listing = (arm / ".workspace-context/README.md").read_text()
            self.assertIn("`AGENTS.md`", listing)
            agents = (arm / "AGENTS.md").read_text()
            self.assertTrue(agents.startswith("# Project rules"))
            self.assertIn(".workspace-context/README.md", agents)

    def test_prompt_is_deterministic_and_names_every_required_test(self):
        task = runner.load_task("crm-manager-export")
        self.assertEqual(runner.prompt_text(task), runner.prompt_text(task))
        for title in task["requiredTests"]:
            self.assertIn(f"`{title}`", runner.prompt_text(task))

    def test_output_inside_the_workspace_is_refused(self):
        with self.assertRaises(SystemExit) as raised:
            runner.main(["prepare", "--task", "crm-manager-direct-route", "--out", str(ROOT / "evidence/results/x")])
        self.assertIn("outside the workspace", str(raised.exception))

    def test_every_task_has_a_known_project_profile_and_oracle(self):
        manifest = runner.load_manifest(ROOT)
        for task in runner.json.loads((runner.TRIALS / "tasks.json").read_text()):
            with self.subTest(task=task["id"]):
                target = task["target"]
                self.assertIn(target["contextProfile"], manifest["projects"][target["evidenceProject"]]["contextProfiles"])
                self.assertIn(target["oracle"]["type"], ("playwright", "junit", "assessment-key", "mutation-proof"))
                if target["oracle"]["type"] == "mutation-proof":
                    self.assertIn(task["case"], runner.assessment.load_cases()["mutationCases"])
                if target["oracle"]["type"] == "assessment-key":
                    self.assertTrue((ROOT / target["oracle"]["cases"]).is_file())
                    self.assertIn(task["variant"], runner.assessment.load_cases()["variants"])
                if target["oracle"]["type"] == "playwright":
                    self.assertTrue((ROOT / target["oracle"]["config"]).is_file())


if __name__ == "__main__":
    unittest.main()


class ExecutionEvidenceTests(unittest.TestCase):
    def test_transcript_distinguishes_in_place_edits_from_disposable_copies(self):
        import json as _json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            arm = home / "arm"
            (home / ".claude/projects/p").mkdir(parents=True)
            def turn(uid, name, data, result):
                return [_json.dumps({"message": {"content": [{"type": "tool_use", "id": uid, "name": name, "input": data}]}}),
                        _json.dumps({"message": {"content": [{"type": "tool_result", "tool_use_id": uid, "content": result}]}})]
            lines = []
            lines += turn("1", "Edit", {"file_path": f"{arm}/examples/sample-crm-app/public/assets/app.js"}, "ok")
            lines += turn("2", "Bash", {"command": "npx playwright test tests"}, "  6 passed (4s)")
            lines += turn("3", "Bash", {"command": "cp -R examples/sample-crm-app /tmp/mutant"}, "This command requires approval")
            (home / ".claude/projects/p/s.jsonl").write_text("\n".join(lines))
            with patch.object(runner.Path, "home", return_value=home):
                found = runner.execution_evidence("s", arm)
            self.assertTrue(found["editedRealSource"])
            self.assertFalse(found["usedDisposableCopy"])  # the copy was denied, so it does not count
            self.assertEqual(found["testRuns"], 1)
