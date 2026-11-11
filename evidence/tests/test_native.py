import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence"))
from native import import_source  # noqa: E402

SOURCE = {"name": "s", "description": "d", "refreshCommand": "run it"}


class NativeImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ws = Path(self.temp.name)
        (self.ws / "proj").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, content):
        path = self.ws / "proj" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_missing_output_is_not_run_with_the_refresh_command(self):
        record = import_source(self.ws, "p", "proj", {**SOURCE, "reader": "junit", "glob": "reports/*.xml"})
        self.assertEqual(record["status"], "not-run")
        self.assertIn("run it", record["notes"][0])

    def test_absent_project_is_unavailable_not_failed(self):
        record = import_source(self.ws, "p", "missing", {**SOURCE, "reader": "junit", "glob": "*.xml"})
        self.assertEqual(record["status"], "unavailable")

    def test_junit_counts_keep_failures_and_skips(self):
        self.write("reports/TEST-a.xml", '<testsuite tests="5" failures="1" errors="1" skipped="1" timestamp="2026-11-11T00:00:00"/>')
        record = import_source(self.ws, "p", "proj", {**SOURCE, "reader": "junit", "glob": "reports/*.xml"})
        self.assertEqual(record["headline"], {"tests": 5, "passed": 2, "failures": 1, "errors": 1, "skipped": 1})

    def test_mutation_campaign_reports_killed_survived_and_restoration(self):
        campaign = {"createdAt": "t", "originalUnchanged": True, "restored": {"status": "passed"},
                    "baseline": [{"status": "passed", "tests": [1, 2]}, {"status": "passed", "tests": [1, 2]}],
                    "faults": [{"id": "A", "status": "killed", "attempts": [1, 2]},
                               {"id": "B", "status": "survived", "attempts": [1, 2]},
                               {"id": "C", "status": "inconclusive", "attempts": []}]}
        self.write("runs/x/campaign.json", json.dumps(campaign))
        record = import_source(self.ws, "p", "proj", {**SOURCE, "reader": "mutation-campaign", "glob": "runs/*/campaign.json"})
        h = record["headline"]
        self.assertEqual((h["killed"], h["survived"], h["otherOutcomes"]), (1, 1, {"inconclusive": 1}))
        self.assertTrue(h["restoredGreen"] and h["originalUnchanged"])
        self.assertEqual((h["greenBaselines"], h["testsPerBaseline"]), (2, 2))

    def test_evaluation_keeps_its_evidence_kind_and_only_assessed_capabilities(self):
        report = {"generatedAt": "t", "evidenceKind": "synthetic", "taskId": "T", "cases": [{}],
                  "capabilities": [{"capability": "acceptance_assessment", "cases": 1, "pass": 1, "fail": 0, "needsReview": 0, "notAssessed": 0},
                                   {"capability": "skill_routing", "cases": 0}]}
        self.write("a/evaluation.json", json.dumps(report))
        record = import_source(self.ws, "p", "proj", {**SOURCE, "reader": "pa-evaluation", "glob": "**/evaluation.json"})
        self.assertEqual(record["evidenceKind"], "synthetic")
        self.assertEqual(list(record["headline"]["capabilities"]), ["acceptance_assessment"])

    def test_unreadable_output_is_reported_not_crashed(self):
        self.write("summary.json", "{not json")
        record = import_source(self.ws, "p", "proj", {**SOURCE, "reader": "mockserver-benchmark", "glob": "summary.json"})
        self.assertEqual(record["status"], "unreadable")


if __name__ == "__main__":
    unittest.main()
