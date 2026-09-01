import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  assertManagedSecretPath,
  defaultCapabilityKeyPath,
  generateEphemeralWorkerToken,
  loadOrCreateCapabilitySecret,
  managedSecretsRoot,
} from '../src/secrets.mjs';

function tempHome() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'uex-stack-home-'));
}

test('managed capability secret is created once with 0600 file and 0700 root', () => {
  const home = tempHome();
  try {
    const filePath = defaultCapabilityKeyPath(home);
    const first = loadOrCreateCapabilitySecret({ filePath, homeDir: home });
    const second = loadOrCreateCapabilitySecret({ filePath, homeDir: home });
    assert.equal(first.secret.toString('utf8'), second.secret.toString('utf8'));
    assert.equal((fs.statSync(filePath).mode & 0o777), 0o600);
    assert.equal((fs.statSync(managedSecretsRoot(home)).mode & 0o777), 0o700);
    assert.match(first.secretRef, /^secret:[0-9a-f]{64}$/);
    assert.equal(first.secretRef.includes(home), false);
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});

test('managed secret path cannot escape dedicated root and symlinks are rejected', () => {
  const home = tempHome();
  try {
    assert.throws(() => assertManagedSecretPath(path.join(home, 'outside.key'), home), /STACK_SECRET_PATH_OUTSIDE_MANAGED_ROOT/);
    const root = managedSecretsRoot(home);
    fs.mkdirSync(root, { recursive: true, mode: 0o700 });
    const target = path.join(home, 'real.key');
    fs.writeFileSync(target, 'x'.repeat(48), { mode: 0o600 });
    const link = path.join(root, 'browser-relay-capability.key');
    fs.symlinkSync(target, link);
    assert.throws(() => loadOrCreateCapabilitySecret({ filePath: link, homeDir: home }), /STACK_SECRET_FILE_TYPE_INVALID/);
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});

test('over-permissive existing key fails closed', () => {
  const home = tempHome();
  try {
    const filePath = defaultCapabilityKeyPath(home);
    fs.mkdirSync(path.dirname(filePath), { recursive: true, mode: 0o700 });
    fs.writeFileSync(filePath, `${'x'.repeat(48)}\n`, { mode: 0o644 });
    fs.chmodSync(filePath, 0o644);
    assert.throws(() => loadOrCreateCapabilitySecret({ filePath, homeDir: home }), /STACK_SECRET_FILE_PERMISSIONS_TOO_OPEN/);
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});

test('worker token is high-entropy shape and not persisted by generator', () => {
  const one = generateEphemeralWorkerToken();
  const two = generateEphemeralWorkerToken();
  assert.ok(one.length >= 48);
  assert.ok(two.length >= 48);
  assert.notEqual(one, two);
  assert.equal(/\s/.test(one), false);
});
