import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  activationRoot,
  assertActivationOutput,
  loadPlan,
  parseArgs,
  writeCapability,
} from '../src/capability-cli.mjs';

function tempHome() { return fs.mkdtempSync(path.join(os.tmpdir(), 'uex-stack-cap-home-')); }

const PLAN = {
  application_id: 'app-1',
  canonical_form_url: 'http://127.0.0.1:39000/form',
  provider: 'generic_html',
  form_fingerprint: `sha256:${'f'.repeat(64)}`,
  validation_signature: `sha256:${'1'.repeat(64)}`,
};

test('capability CLI defaults outputs inside managed activation root', () => {
  const home = tempHome();
  try {
    const args = parseArgs(['--request-id', 'req-prefill-0001', '--plan', '/tmp/plan.json'], home);
    assert.equal(args.outPath, path.join(activationRoot(home), 'prefill.cap'));
    assert.ok(args.keyPath.startsWith(path.join(home, '.uexchanges', 'secrets')));
    assert.equal(args.ttl, 120);
    assert.throws(() => parseArgs(['--request-id', 'bad', '--plan', '/tmp/plan.json'], home), /STACK_CAPABILITY_REQUEST_ID_INVALID/);
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});

test('capability output cannot escape activation root and token file is 0600', () => {
  const home = tempHome();
  try {
    assert.throws(() => assertActivationOutput(path.join(home, 'outside.cap'), home), /STACK_CAPABILITY_OUTPUT_OUTSIDE_ACTIVATION_ROOT/);
    const target = assertActivationOutput(path.join(activationRoot(home), 'prefill.cap'), home);
    writeCapability(target, 'opaque-token-value');
    assert.equal(fs.statSync(target).mode & 0o777, 0o600);
    assert.equal(fs.readFileSync(target, 'utf8').trim(), 'opaque-token-value');
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});

test('plan loader is JSON object and identity strict enough for capability issuance', () => {
  const home = tempHome();
  try {
    const file = path.join(home, 'plan.json');
    fs.writeFileSync(file, JSON.stringify(PLAN));
    assert.equal(loadPlan(file).application_id, 'app-1');
    fs.writeFileSync(file, JSON.stringify({ application_id: 'app-1' }));
    assert.throws(() => loadPlan(file), /STACK_CAPABILITY_PLAN_IDENTITY_INVALID/);
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});
