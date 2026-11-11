import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence"))
import dashboard  # noqa: E402


def context_record(project, status="complete", ratio=3.0):
    return {"kind": "context", "project": project, "profile": "p<script>", "status": status, "missing": [], "notes": [] if status == "complete" else ["run the resolver"],
            "selected": {"tokens": 100, "instructionTokens": 60, "taskTokens": 40}, "corpus": {"tokens": 300},
            "selectedAsPercentOfCorpus": 33.3 if status == "complete" else None, "corpusToSelectedRatio": ratio if status == "complete" else None,
            "source": {"commit": "abc", "uncommittedChanges": False}, "recordedAt": "2026-11-11T00:00:00+00:00"}


class DashboardTests(unittest.TestCase):
    def test_page_escapes_content_and_shows_incomplete_and_missing_states(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "api-workspace").mkdir()
            (base / "api-workspace/context-a.json").write_text(json.dumps(context_record("api-workspace")))
            (base / "mockserver").mkdir()
            (base / "mockserver/context-b.json").write_text(json.dumps(context_record("mockserver", status="incomplete")))
            (base / "mockserver/native-x.json").write_text(json.dumps({"kind": "native", "project": "mockserver", "profile": "x", "description": "d",
                                                                    "status": "not-run", "notes": ["run benchmark"]}))
            page = dashboard.build(base)
            self.assertNotIn("<script>", page)
            self.assertIn("p&lt;script&gt;", page)
            self.assertIn("3.0×", page)
            self.assertIn("Incomplete: run the resolver", page)
            self.assertIn("not-run", page)
            self.assertIn("No context measurement yet", page)  # playwright-agent has no results here
            self.assertIn("No trials recorded yet", page)


if __name__ == "__main__":
    unittest.main()
