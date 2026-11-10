// Explicit, local-only backport for GHSA-gcqx-w48m-w2h4 while upstream has no fixed release.
// No install hook invokes this script. Re-run deliberately after a tool update if still needed.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';

const prefix = execFileSync('npm', ['prefix', '--global'], {encoding:'utf8'}).trim();
const packageRoot = path.join(prefix, 'lib/node_modules/netlify-cli/node_modules/deepmerge');
const metadata = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json')));
if (metadata.name !== 'deepmerge' || metadata.version !== '4.3.1') throw Error('Review the current upstream version before applying this backport');
const files = ['index.js', 'dist/cjs.js', 'dist/umd.js'].filter(file => fs.existsSync(path.join(packageRoot, file)));
const guard = "\n            if (key === '__proto__' || key === 'constructor' || key === 'prototype') return; // GHSA-gcqx-w48m-w2h4\n";
const receipt = {package:'deepmerge', version:'4.3.1', advisory:'GHSA-gcqx-w48m-w2h4',
  reason:'Backport rejects prototype-mutating keys in both target and source; upstream has no published fixed release.', files:[]};
for (const file of files) {
  const full = path.join(packageRoot, file);
  let source = fs.readFileSync(full, 'utf8');
  if (!source.includes('GHSA-gcqx-w48m-w2h4')) {
    let replacements = 0;
    source = source.replace(/getKeys\((target|source)\)\.forEach\(function\s*\(key\)\s*\{/g, match => {replacements++; return match + guard;});
    if (replacements !== 2) throw Error('Unexpected deepmerge source; no backport applied to ' + file);
    fs.writeFileSync(full, source);
  }
  receipt.files.push({path:path.relative(prefix, full), sha256:crypto.createHash('sha256').update(source).digest('hex')});
}
const require = createRequire(path.join(packageRoot, 'package.json'));
const merge = require(packageRoot);
for (const key of ['__proto__', 'constructor', 'prototype']) {
  const payload = JSON.parse(`{"${key}":{"securityReview":"injected"},"safe":{"value":1}}`);
  for (const [target, source] of [[payload, {}], [{}, payload]]) {
    const result = merge(target, source);
    assert.equal(Object.getPrototypeOf(result), Object.prototype);
    assert.equal(Object.hasOwn(result, key), false);
    assert.equal(result.securityReview, undefined);
    assert.deepEqual(result.safe, {value:1});
  }
}
assert.deepEqual(merge({a:[1],nested:{a:1}}, {a:[2],nested:{b:2}}), {a:[1,2],nested:{a:1,b:2}});
fs.writeFileSync(new URL('./global-tool-security-patches.json', import.meta.url), JSON.stringify([receipt], null, 2)+'\n');
console.log('Deepmerge prototype-poisoning backport verified; ordinary nested/array merges preserved.');
