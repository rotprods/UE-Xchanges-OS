import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs, writeSecretFile } from '../src/capability-cli.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../..');


test('capability CLI requires file-based local issuance arguments', () => {
  const parsed = parseArgs(['--request-id', 'req-prefill-0001', '--plan', '/tmp/plan.json', '--out', '/tmp/prefill.cap', '--ttl', '120']);
  assert.equal(parsed.requestId, 'req-prefill-0001');
  assert.equal(parsed.ttl, 120);
  assert.throws(() => parseArgs(['--secret', 'do-not-allow']), /RELAY_CAPABILITY_ARG_UNKNOWN|RELAY_CAPABILITY_ARGS_REQUIRED/);
});

test('capability token file is mode 0600', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-relay-cap-'));
  try {
    const target = writeSecretFile(path.join(dir, 'prefill.cap'), 'opaque-capability-token');
    const mode = fs.statSync(target).mode & 0o777;
    assert.equal(mode, 0o600);
    assert.equal(fs.readFileSync(target, 'utf8').trim(), 'opaque-capability-token');
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('capability schema is closed and prefill-local only', () => {
  const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'schemas/browser-relay-capability.schema.json'), 'utf8'));
  assert.equal(schema.additionalProperties, false);
  assert.equal(schema.properties.operation.const, 'prefill-local');
  assert.match(schema.properties.body_hash.pattern, /sha256/);
  assert.equal(schema.properties.expires_at.format, 'date-time');
});
