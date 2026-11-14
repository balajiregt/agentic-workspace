import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence/trials/crm-scale"))
import analyze  # noqa: E402

PA = ROOT / "qa/playwright-agent"
HERE = ROOT / "evidence/trials/crm-scale"


def assessment_row(run, arm, found, gaps=13, alarms=0, model="claude-opus-5-5", cost=1.0):
    return {"trialId": f"{run}-{arm}", "taskId": "crm-scale-assessment-B", "arm": arm, "modelVersion": model,
            "gaps": gaps, "gapsFound": found, "falseAlarms": alarms, "covered": 72, "exact": found == gaps and not alarms,
            "agent": {"costUsd": cost, "inputTokens": 1000, "outputTokens": 100, "turns": 5, "guidanceReceived": arm == "framework",
                      "effort": {"toolCalls": 10, "distinctFilesRead": 8}, "workspaceAccess": []}}


class AnalysisRuleTests(unittest.TestCase):
    def run_analysis(self, rows):
        with tempfile.TemporaryDirectory() as temp:
            results = Path(temp)
            (results / "assessments").mkdir()
            for row in rows:
                (results / "assessments" / f"{row['trialId']}.json").write_text(json.dumps(row))
            with patch.object(analyze, "RESULTS", results):
                analyze.main()
                return json.loads((results / "crm-scale-analysis.json").read_text())

    def test_ten_point_recall_gain_with_more_wins_adds_accuracy(self):
        rows = []
        for i in range(3):
            rows += [assessment_row(f"r{i}", "baseline", 9), assessment_row(f"r{i}", "framework", 12)]
        result = self.run_analysis(rows)["models"]["opus"]["assessment"]
        self.assertEqual(result["verdict"], "Playwright Agent adds accuracy")
        self.assertIsNone(result["efficiency"])

    def test_tie_at_ceiling_is_judged_on_efficiency(self):
        rows = []
        for i in range(6):
            rows += [assessment_row(f"r{i}", "baseline", 13, cost=2.0), assessment_row(f"r{i}", "framework", 13, cost=1.5)]
        result = self.run_analysis(rows)["models"]["opus"]["assessment"]
        self.assertTrue(result["ceiling"])
        self.assertEqual(result["verdict"], "no measurable difference")
        self.assertEqual(result["efficiency"]["verdict"], "Playwright Agent adds efficiency")

    def test_workspace_access_excludes_the_pair_and_models_are_not_pooled(self):
        leaked = assessment_row("r0", "framework", 13)
        leaked["agent"]["workspaceAccess"] = ["Read: {...}"]
        rows = [assessment_row("r0", "baseline", 9), leaked,
                assessment_row("h0", "baseline", 5, model="claude-haiku-5-5"), assessment_row("h0", "framework", 6, model="claude-haiku-5-5")]
        models = self.run_analysis(rows)["models"]
        self.assertEqual(models["opus"]["assessment"]["pairs"], 0)
        self.assertEqual(models["opus"]["assessment"]["excluded"][0]["reason"], "touched the workspace")
        self.assertEqual(models["haiku"]["assessment"]["pairs"], 1)


class AnswerKeyStaticTests(unittest.TestCase):
    """Cheap checks; the behavioural proof is benchmark.py validate."""

    def setUp(self):
        self.cases = json.loads((HERE / "cases.json").read_text())
        self.faults = json.loads((HERE / "faults.json").read_text())["faults"]

    def test_every_edit_and_fault_patch_applies_exactly_once(self):
        for name, variant in self.cases["variants"].items():
            texts = {}
            for edit in variant["edits"]:
                text = texts.get(edit["file"]) or (PA / edit["file"]).read_text()
                self.assertEqual(text.count(edit["find"]), 1, f"variant {name}: {edit['find'][:50]!r}")
                texts[edit["file"]] = text.replace(edit["find"], edit["replace"])
        for name, fault in self.faults.items():
            for edit in fault["edits"]:
                self.assertEqual((PA / edit["file"]).read_text().count(edit["find"]), 1, f"fault {name}")

    def test_key_covers_every_criterion_and_names_known_faults(self):
        criteria = json.loads((ROOT / self.cases["criteriaSource"]).read_text())["requirements"]
        self.assertEqual(sorted(self.cases["baseTruth"]), sorted(c["id"] for c in criteria))
        for fault in list(self.cases["naturalGaps"].values()) + list(self.cases["coveredFaults"].values()):
            self.assertIn(fault, self.faults)
        for variant in self.cases["variants"].values():
            for gap in variant["gaps"]:
                self.assertEqual(self.cases["baseTruth"][gap], "covered")
                self.assertIn(gap, self.cases["coveredFaults"])

    def test_application_contains_no_fault_switches(self):
        source = (PA / "examples/crm-scale/app/api.mjs").read_text() + (PA / "examples/crm-scale/app/server.mjs").read_text()
        self.assertNotIn("CRM_SCALE_FAULT", source)
        self.assertNotRegex(source, r"\bfault\b")


if __name__ == "__main__":
    unittest.main()
