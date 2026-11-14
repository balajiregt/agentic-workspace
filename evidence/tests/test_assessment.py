import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence" / "trials" / "assessment"))
import assessment  # noqa: E402

CASES = assessment.load_cases()


def answer(statuses: dict) -> dict:
    return {"criteria": [{"id": k, "status": v, "test": None, "reason": "r"} for k, v in statuses.items()]}


class AssessmentScoringTests(unittest.TestCase):
    def test_key_marks_planted_gaps_on_top_of_the_documented_one(self):
        self.assertEqual(assessment.truth(CASES, "A")["DASHBOARD-METRIC"], "gap")
        self.assertEqual(assessment.truth(CASES, "B")["VIEWER-READONLY"], "gap")
        self.assertEqual(assessment.truth(CASES, "A")["VIEWER-READONLY"], "covered")
        self.assertEqual(assessment.truth(CASES, "C")["LEAD-CREATE"], "ambiguous")

    def test_correct_answer_is_exact_and_ambiguous_criteria_are_not_scored(self):
        key = assessment.truth(CASES, "C")
        statuses = {k: ("missing" if v == "gap" else "covered") for k, v in key.items()}
        statuses["LEAD-CREATE"] = "partial"  # either answer is acceptable for an ambiguous criterion
        result = assessment.score(answer(statuses), CASES, "C")
        self.assertTrue(result["exact"])
        self.assertEqual((result["gapsFound"], result["gaps"], result["falseAlarms"]), (3, 3, 0))

    def test_name_based_answer_misses_hidden_gap_and_strict_answer_raises_false_alarms(self):
        key = assessment.truth(CASES, "B")
        naive = {k: "covered" for k in key}
        naive["DASHBOARD-METRIC"] = "missing"
        result = assessment.score(answer(naive), CASES, "B")
        self.assertEqual((result["gapsFound"], result["gaps"]), (1, 2))
        alarmist = {k: "partial" for k in key}
        result = assessment.score(answer(alarmist), CASES, "B")
        self.assertEqual(result["gapsFound"], 2)
        self.assertEqual(result["falseAlarms"], sum(v == "covered" for v in key.values()))
        self.assertFalse(result["exact"])

    def test_synonyms_unanswered_and_invalid_answers(self):
        self.assertEqual(assessment.normalise("Not covered"), "missing")
        self.assertEqual(assessment.normalise("Partially covered"), "partial")
        self.assertIsNone(assessment.normalise("maybe"))
        result = assessment.score({"criteria": [{"id": "LOGIN-VALID", "status": "covered"}]}, CASES, "A")
        self.assertEqual(result["unanswered"], 7)
        self.assertFalse(result["allCriteriaAnswered"])
        self.assertEqual(assessment.score({}, CASES, "A")["unanswered"], 8)

    def test_variant_edits_apply_exactly_once_to_the_real_suite(self):
        source = ROOT / "qa/playwright-agent"
        if not source.is_dir():
            self.skipTest("Playwright Agent is not present in this checkout")
        for variant, spec in CASES["variants"].items():
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for edit in spec["edits"]:
                    target = root / edit["file"]
                    if not target.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text((source / edit["file"]).read_text())
                assessment.apply_edits(root, spec["edits"])
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "f.ts").write_text("x\nx\n")
            with self.assertRaises(SystemExit):
                assessment.apply_edits(Path(temp), [{"file": "f.ts", "find": "x", "replace": "y"}])


if __name__ == "__main__":
    unittest.main()
