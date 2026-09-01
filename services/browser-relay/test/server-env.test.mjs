import test from 'node:test';
import assert from 'node:assert/strict';
import { createServerFromEnvironment } from '../src/server.mjs';

const TOKEN = 'worker-token-'.padEnd(48, 'w');
const CAP = 'cap-secret-'.padEnd(48, 'c');


test('server factory requires local secrets but not secret values in arguments', () => {
  assert.throws(() => createServerFromEnvironment({}), /UEX_BROWSER_WORKER_TOKEN_INVALID/);
  assert.throws(() => createServerFromEnvironment({ UEX_BROWSER_WORKER_TOKEN: TOKEN }), /UEX_BROWSER_RELAY_CAPABILITY_SECRET_INVALID/);
  const server = createServerFromEnvironment({
    UEX_BROWSER_WORKER_TOKEN: TOKEN,
    UEX_BROWSER_RELAY_CAPABILITY_SECRET: CAP,
    UEX_BROWSER_WORKER_URL: 'http://127.0.0.1:4777/',
  });
  assert.ok(server);
});

test('server factory rejects external worker URLs before MCP serves', () => {
  assert.throws(
    () => createServerFromEnvironment({
      UEX_BROWSER_WORKER_TOKEN: TOKEN,
      UEX_BROWSER_RELAY_CAPABILITY_SECRET: CAP,
      UEX_BROWSER_WORKER_URL: 'http://10.0.0.8:4777/',
    }),
    /RELAY_WORKER_URL_MUST_BE_LOOPBACK_HTTP/,
  );
});
