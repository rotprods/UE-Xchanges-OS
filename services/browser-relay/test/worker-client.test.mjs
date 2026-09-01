import test from 'node:test';
import assert from 'node:assert/strict';
import { BrowserWorkerClient, assertLoopbackWorkerUrl } from '../src/worker-client.mjs';

const TOKEN = 'worker-secret-'.padEnd(48, 'w');

function response(value, { status = 200 } = {}) {
  return new Response(JSON.stringify(value), { status, headers: { 'content-type': 'application/json' } });
}

test('worker URL is strictly loopback HTTP', () => {
  for (const value of ['http://127.0.0.1:4777/', 'http://localhost:4777/', 'http://[::1]:4777/']) {
    assert.equal(assertLoopbackWorkerUrl(value).protocol, 'http:');
  }
  for (const value of ['https://127.0.0.1:4777/', 'http://10.0.0.5:4777/', 'http://example.com/', 'http://user:pass@127.0.0.1:4777/', 'http://127.0.0.1:4777/v1']) {
    assert.throws(() => assertLoopbackWorkerUrl(value));
  }
});

test('client sends bearer token locally but never includes it in descriptor or result', async () => {
  const seen = [];
  const fetchImpl = async (url, init) => {
    seen.push({ url: String(url), authorization: init.headers.authorization });
    return response({ ok: true, result: { safe: true } });
  };
  const client = new BrowserWorkerClient({ baseUrl: 'http://127.0.0.1:4777/', token: TOKEN, fetchImpl });
  const result = await client.status();
  assert.deepEqual(result, { safe: true });
  assert.equal(seen[0].authorization, `Bearer ${TOKEN}`);
  assert.equal(JSON.stringify(client.safeDescriptor()).includes(TOKEN), false);
  assert.equal(JSON.stringify(result).includes(TOKEN), false);
});

test('client rejects worker responses that reflect its token', async () => {
  const client = new BrowserWorkerClient({
    baseUrl: 'http://127.0.0.1:4777/',
    token: TOKEN,
    fetchImpl: async () => response({ ok: true, result: { reflected: TOKEN } }),
  });
  await assert.rejects(() => client.status(), /RELAY_WORKER_SECRET_LEAK_DETECTED/);
});

test('post forwards exact request id and maps code-only worker failure', async () => {
  let seen;
  const client = new BrowserWorkerClient({
    baseUrl: 'http://127.0.0.1:4777/',
    token: TOKEN,
    fetchImpl: async (_url, init) => {
      seen = init;
      return response({ ok: false, error: { code: 'WORKER_INSPECT_REQUIRED' } }, { status: 400 });
    },
  });
  await assert.rejects(
    () => client.inspectLocal({ requestId: 'req-inspect-0001', provider: 'generic_html', url: 'http://127.0.0.1:3000/form', allowedOrigins: ['http://127.0.0.1:3000'] }),
    /WORKER_INSPECT_REQUIRED/,
  );
  assert.equal(seen.headers['x-uex-request-id'], 'req-inspect-0001');
});
