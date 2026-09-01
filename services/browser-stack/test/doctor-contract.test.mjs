import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { doctorChildEnv, parseArgs } from '../src/doctor-cli.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../..');

test('doctor child env drops unrelated secrets', () => {
  const env = doctorChildEnv({
    HOME: '/tmp/home', PATH: '/usr/bin', LANG: 'C.UTF-8',
    GITHUB_TOKEN: 'secret', OPENAI_API_KEY: 'secret2', UEX_BROWSER_WORKER_TOKEN: 'secret3',
  });
  assert.deepEqual(env, { HOME: '/tmp/home', PATH: '/usr/bin', LANG: 'C.UTF-8' });
});

test('doctor args are strict and channel bounded', () => {
  assert.equal(parseArgs([]).channel, 'chrome');
  assert.equal(parseArgs(['--channel', 'chromium']).channel, 'chromium');
  assert.throws(() => parseArgs(['--channel', 'firefox']), /STACK_DOCTOR_CHANNEL_INVALID/);
  assert.throws(() => parseArgs(['--unknown', 'x']), /STACK_DOCTOR_ARG_UNKNOWN/);
});

test('stack doctor schema is closed and explicitly denies Submit capability', () => {
  const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'schemas/browser-stack-doctor.schema.json'), 'utf8'));
  assert.equal(schema.additionalProperties, false);
  assert.equal(schema.properties.submit_capability.const, false);
  assert.equal(schema.properties.worker_token_persistence.const, 'memory_only');
  assert.equal(schema.properties.capability_key_mode.const, '600');
  assert.equal(schema.properties.browser.properties.network.const, 'blocked');
});
