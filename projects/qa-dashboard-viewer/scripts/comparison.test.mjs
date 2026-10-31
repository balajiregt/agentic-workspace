import test from 'node:test';
import assert from 'node:assert/strict';
import * as viewer from '../comparison-view.mjs';
import * as shared from '../../../playwright-decision-bench/shared/comparison-view.mjs';

const report = () => ({
  kind: 'playwright-decision-comparison', version: 2,
  requirements: [], inventory: { tests: [] },
  runs: { laya: { cells: [], smoke: { selected: [], reviewCandidates: [],
    estimatedCoveredRequirements: [], mandatoryRequirements: [], missingRequirements: [] } } },
  policy: { minProbability: .8, minPassRate: .98, minRuns: 3, budgetMs: 3000 },
  smokeExecutions: { laya: { passed: 1, failed: 0, skipped: 0, wallMs: 100 } }
});

for (const [name, renderer] of Object.entries({ viewer, shared })) {
  test(`${name}: imports render valid metrics and reject executable metric strings`, () => {
    assert.match(renderer.renderComparison(report()), /Executed: 1 passed/);
    for (const key of ['passed', 'failed', 'skipped', 'wallMs']) {
      const data = report();
      data.smokeExecutions.laya[key] = '<img src=x onerror=alert(1)>';
      assert.throws(() => renderer.renderComparison(data), /execution metrics/);
    }
  });
  test(`${name}: history, policy and synthetic length objects cannot inject HTML`, () => {
    const data = report();
    data.inventory.tests = [{ id: 'test', runs: '<svg onload=alert(1)>', passRate: 1 }];
    assert.throws(() => renderer.renderComparison(data), /history metrics/);
    for (const bad of [-1, Infinity, NaN, '0.8']) {
      const data = report(); data.policy.minProbability = bad;
      assert.throws(() => renderer.renderComparison(data), /policy metrics/);
    }
    const lengths = report();
    lengths.runs.laya.smoke.estimatedCoveredRequirements = { length: '<img src=x>' };
    assert.throws(() => renderer.renderComparison(lengths), /smoke metrics/);
  });
}
