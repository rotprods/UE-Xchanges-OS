import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import {
  envBool,
  minimalSystemEnv,
  startBrowserStack,
  waitForWorkerReady,
} from '../src/process-manager.mjs';

class FakeChild extends EventEmitter {
  constructor() {
    super();
    this.stdout = new PassThrough();
    this.stderr = new PassThrough();
    this.exitCode = null;
    this.signalCode = null;
    this.kills = [];
  }
  kill(signal) {
    this.kills.push(signal);
    this.signalCode = signal;
    queueMicrotask(() => {
      this.exitCode = 0;
      this.emit('exit', 0, signal);
    });
    return true;
  }
}

function tempHome() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'uex-stack-pm-home-'));
}

test('system child environment uses allowlist and drops unrelated host secrets', () => {
  const filtered = minimalSystemEnv({
    HOME: '/tmp/home', PATH: '/usr/bin', LANG: 'C.UTF-8',
    GITHUB_TOKEN: 'secret', OPENAI_API_KEY: 'secret2', UEX_BROWSER_WORKER_TOKEN: 'old',
  });
  assert.deepEqual(filtered, { HOME: '/tmp/home', PATH: '/usr/bin', LANG: 'C.UTF-8' });
});

test('boolean env parser is strict', () => {
  assert.equal(envBool(undefined, true), true);
  assert.equal(envBool('1'), true);
  assert.equal(envBool('true'), true);
  assert.equal(envBool('0', true), false);
  assert.equal(envBool('false', true), false);
  assert.throws(() => envBool('yes'), /STACK_BOOLEAN_ENV_INVALID/);
});

test('supervisor generates one ephemeral worker token, isolates env, and shuts both children', async () => {
  const home = tempHome();
  const calls = [];
  const children = [];
  const spawnImpl = (_command, _args, options) => {
    const child = new FakeChild();
    calls.push(options);
    children.push(child);
    if (calls.length === 1) queueMicrotask(() => child.stdout.write('UEX_BROWSER_WORKER_READY http://127.0.0.1:49123\n'));
    return child;
  };
  try {
    const stack = await startBrowserStack({
      env: {
        HOME: home,
        PATH: process.env.PATH,
        LANG: 'C.UTF-8',
        GITHUB_TOKEN: 'MUST-NOT-PASS',
        OPENAI_API_KEY: 'MUST-NOT-PASS-EITHER',
        UEX_BROWSER_CHANNEL: 'chromium',
        UEX_BROWSER_HEADLESS: '1',
        UEX_BROWSER_STACK_ALLOW_LOCAL_PREFILL: '0',
      },
      stdio: { stdin: 'IN', stdout: 'OUT', stderr: 'ERR' },
      spawnImpl,
    });
    assert.equal(calls.length, 2);
    const workerEnv = calls[0].env;
    const relayEnv = calls[1].env;
    assert.equal(workerEnv.GITHUB_TOKEN, undefined);
    assert.equal(relayEnv.OPENAI_API_KEY, undefined);
    assert.ok(workerEnv.UEX_BROWSER_WORKER_TOKEN.length >= 48);
    assert.equal(relayEnv.UEX_BROWSER_WORKER_TOKEN, workerEnv.UEX_BROWSER_WORKER_TOKEN);
    assert.ok(relayEnv.UEX_BROWSER_RELAY_CAPABILITY_SECRET.length >= 32);
    assert.equal(workerEnv.UEX_BROWSER_RELAY_CAPABILITY_SECRET, undefined);
    assert.equal(stack.safeState.worker_token_persisted, false);
    assert.equal(stack.safeState.worker_url, 'http://127.0.0.1:49123/');
    assert.equal(stack.safeState.submit_capability, false);
    assert.equal(stack.safeState.inherited_env_keys.includes('GITHUB_TOKEN'), false);
    assert.ok(stack.safeState.capability_secret_path.startsWith(path.join(home, '.uexchanges', 'secrets')));

    await stack.close();
    assert.deepEqual(children[0].kills, ['SIGTERM']);
    assert.deepEqual(children[1].kills, ['SIGTERM']);
  } finally { fs.rmSync(home, { recursive: true, force: true }); }
});

test('worker readiness parser accepts only exact loopback marker and bounded output', async () => {
  const child = new FakeChild();
  const ready = waitForWorkerReady(child, 1000);
  queueMicrotask(() => child.stdout.write('noise\nUEX_BROWSER_WORKER_READY http://127.0.0.1:4777\n'));
  assert.equal(await ready, 'http://127.0.0.1:4777/');

  const bad = new FakeChild();
  const rejected = waitForWorkerReady(bad, 1000);
  queueMicrotask(() => bad.stdout.write('x'.repeat(5000)));
  await assert.rejects(rejected, /STACK_WORKER_READY_OUTPUT_INVALID/);
});
