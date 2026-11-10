import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workspace_layout import ui_automation_root
from check_workspace import check
from build_qa_dashboard import summarize_ui_automation, test_file_inventory, impacted_recommendations


class WorkspaceLayoutTests(unittest.TestCase):
    def test_retired_shared_context_directory_cannot_return(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            overlay = Path(temp)
            old = 'agent-system/contexts/current/ui-context.yml'
            task = overlay/old
            task.parent.mkdir(parents=True)
            task.write_text('ui_project_name: role-aware-mockserver\n')
            self.assertIn('Retired shared context directory exists: agent-system/contexts', check(root, overlay)['errors'])

    def test_duplicate_registered_paths_are_rejected_even_with_different_spelling(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            overlay = Path(temp)
            registry = json.loads((root/'workspace.projects.json').read_text())
            project = dict(next(p for p in registry['projects'] if p['id'] == 'role-aware-ui'))
            project.update(id='duplicate-ui', path='qa-projects/ui-automation/role-aware-mockserver/../role-aware-mockserver')
            registry['projects'].append(project)
            (overlay/'workspace.projects.json').write_text(json.dumps(registry))
            self.assertTrue(any(e.startswith('Duplicate project path:') for e in check(root, overlay)['errors']))

    def test_retired_working_roots_cannot_silently_return(self):
        root = Path(__file__).resolve().parents[2]
        for retired in ['qa-projects/plawright-role-aware-mockserver',
                        'evaluation/playwright-decision-bench',
                        'projects/qa-dashboard-viewer', 'qa-projects/xyz-service-api-tests']:
            with self.subTest(path=retired), tempfile.TemporaryDirectory() as temp:
                overlay = Path(temp)
                (overlay/retired).mkdir(parents=True)
                self.assertIn('Retired duplicate project root exists: '+retired, check(root, overlay)['errors'])

    def test_categories_match_real_directories_and_editor_groups(self):
        root = Path(__file__).resolve().parents[2]
        self.assertTrue(check(root)['ok'])
        with tempfile.TemporaryDirectory() as temp:
            overlay = Path(temp)
            registry = json.loads((root/'workspace.projects.json').read_text())
            registry['groups'][0]['path'] = 'missing-category'
            (overlay/'workspace.projects.json').write_text(json.dumps(registry))
            errors = check(root, overlay)['errors']
            self.assertIn('Invalid group directory: missing-category', errors)
            self.assertIn('Editor folders do not match the category registry', errors)

    def test_current_location_wins_and_legacy_layout_remains_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root/'projects/ui-automation'
            old.mkdir(parents=True)
            self.assertEqual(ui_automation_root(root), old)
            current = root/'qa-projects/ui-automation'
            current.mkdir(parents=True)
            self.assertEqual(ui_automation_root(root), current)

    def test_reports_and_inventory_follow_the_moved_ui_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root/'qa-projects/ui-automation/role-aware-mockserver'
            report = project/'playwright/playwright-report/index.html'
            report.parent.mkdir(parents=True)
            report.write_text('report fixture')
            last = project/'test-results/.last-run.json'
            last.parent.mkdir()
            last.write_text('{"failedTests": ["role-check"]}')
            spec = project/'playwright/tests/role-ui.spec.ts'
            spec.parent.mkdir()
            spec.write_text('test fixture')
            health = summarize_ui_automation(root)
            self.assertTrue(health['reportExists'])
            self.assertEqual(health['status'], 'fail')
            self.assertEqual(test_file_inventory(root, {}, {})['ui']['totalFiles'], 1)

    def test_recommendations_include_actual_resolved_ui_location(self):
        ui = {'resolved_repositories': {'ui_project': 'qa-projects/ui-automation/role-aware-mockserver'},
              'verification': {'commands': ['run focused checks']}}
        result = impacted_recommendations({}, ui, ['qa-projects/ui-automation/role-aware-mockserver/app/public/app.js'])
        self.assertTrue(any(item['area'] == 'UI automation' for item in result))


if __name__ == '__main__':
    unittest.main()
