import test from 'node:test';
import assert from 'node:assert/strict';
import {
  assertLoopbackBind,
  assertRequestId,
  assertWorkerToken,
  profileRef,
  safeErrorCode,
} from '../src/security.mjs';


test('worker bind is loopback-only', () => {
  for (const host of ['127.0.0.1', 'localhost', '::1']) assert.equal(assertLoopbackBind(host), host);
  for (const host of ['0.0.0.0', '192.168.1.20', 'example.org', '']) {
    assert.throws(() => assertLoopbackBind(host), /WORKER_BIND_MUST_BE_LOOPBACK/);
  }
});

test('worker token and request id have hard minimum contracts', () => {
  assert.equal(assertWorkerToken('x'.repeat(32)), 'x'.repeat(32));
  assert.throws(() => assertWorkerToken('short'), /WORKER_TOKEN_INVALID/);
  assert.throws(() => assertWorkerToken(`${'x'.repeat(31)} `), /WORKER_TOKEN_INVALID/);
  assert.equal(assertRequestId('req-12345678'), 'req-12345678');
  assert.throws(() => assertRequestId('bad'), /WORKER_REQUEST_ID_INVALID/);
  assert.throws(() => assertRequestId('request id with spaces'), /WORKER_REQUEST_ID_INVALID/);
});

test('profile ref is opaque and errors are redacted', () => {
  const ref = profileRef('/Users/example/.uexchanges/browser/profile');
  assert.match(ref, /^profile:[0-9a-f]{64}$/);
  assert.equal(ref.includes('/Users/example'), false);
  assert.equal(safeErrorCode(new Error('https://secret.example/form?token=abc')), 'WORKER_OPERATION_FAILED');
  assert.equal(safeErrorCode(new Error('WORKER_SAFE_CODE')), 'WORKER_SAFE_CODE');
});
