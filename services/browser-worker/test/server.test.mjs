import test from 'node:test';
import assert from 'node:assert/strict';
import { createBrowserWorkerServer } from '../src/server.mjs';

const TOKEN = 'worker-token-'.padEnd(48, 'x');

function fakeSession() {
  let inspectCalls = 0;
  return {
    async start() {},
    async close() {},
    status() {
      return { worker_session: 'fake', safety: { submit_api_present: false } };
    },
    async inspect(input) {
      inspectCalls += 1;
      return { provider: input.provider, safe: true, inspect_calls: inspectCalls };
    },
    async prefillLocal(plan) {
      return { application_id: plan.application_id, write_count: 1 };
    },
    async validateLocal(plan) {
      return { application_id: plan.application_id, all_values_match: true };
    },
    get inspectCalls() { return inspectCalls; },
  };
}

async function withWorker(options, fn) {
  const session = options.session || fakeSession();
  const worker = createBrowserWorkerServer({ session, token: TOKEN, host: '127.0.0.1', port: 0, ...options });
  const address = await worker.listen();
  try {
    await fn({ base: `http://127.0.0.1:${address.port}`, session });
  } finally {
    await worker.close();
  }
}

function authHeaders(extra = {}) {
  return { authorization: `Bearer ${TOKEN}`, ...extra };
}

async function json(response) {
  return { status: response.status, body: await response.json(), replayed: response.headers.get('x-uex-replayed') };
}

test('health is minimal and v1 endpoints require bearer auth', async () => {
  await withWorker({}, async ({ base }) => {
    let result = await json(await fetch(`${base}/healthz`));
    assert.equal(result.status, 200);
    assert.deepEqual(result.body, { ok: true, status: 'ok' });

    result = await json(await fetch(`${base}/v1/status`));
    assert.equal(result.status, 401);
    assert.equal(result.body.error.code, 'WORKER_UNAUTHORIZED');

    result = await json(await fetch(`${base}/v1/status`, { headers: authHeaders() }));
    assert.equal(result.status, 200);
    assert.equal(result.body.result.transport.submit_endpoint_present, false);
    assert.equal(result.body.result.transport.human_takeover, 'local_cli_only');
  });
});

test('cross-site origin and submit-shaped routes are blocked', async () => {
  await withWorker({}, async ({ base }) => {
    const crossSite = await json(await fetch(`${base}/v1/status`, {
      headers: authHeaders({ origin: 'https://evil.example' }),
    }));
    assert.equal(crossSite.status, 403);
    assert.equal(crossSite.body.error.code, 'WORKER_ORIGIN_NOT_LOOPBACK');

    const submit = await json(await fetch(`${base}/v1/submit`, {
      method: 'POST',
      headers: authHeaders({ 'content-type': 'application/json', 'x-uex-request-id': 'req-submit-0001' }),
      body: '{}',
    }));
    assert.equal(submit.status, 404);
    assert.equal(submit.body.error.code, 'WORKER_ROUTE_NOT_FOUND');
  });
});

test('request ids are idempotent and cannot be reused for different payloads', async () => {
  await withWorker({}, async ({ base, session }) => {
    const headers = authHeaders({ 'content-type': 'application/json', 'x-uex-request-id': 'req-inspect-0001' });
    const body = JSON.stringify({ provider: 'generic_html', url: 'http://127.0.0.1:3000/form', allowed_origins: ['http://127.0.0.1:3000'] });
    let result = await json(await fetch(`${base}/v1/inspect`, { method: 'POST', headers, body }));
    assert.equal(result.status, 200);
    assert.equal(session.inspectCalls, 1);

    result = await json(await fetch(`${base}/v1/inspect`, { method: 'POST', headers, body }));
    assert.equal(result.status, 200);
    assert.equal(result.replayed, '1');
    assert.equal(session.inspectCalls, 1);

    const changed = JSON.stringify({ provider: 'generic_html', url: 'http://127.0.0.1:3001/form', allowed_origins: ['http://127.0.0.1:3001'] });
    result = await json(await fetch(`${base}/v1/inspect`, { method: 'POST', headers, body: changed }));
    assert.equal(result.status, 409);
    assert.equal(result.body.error.code, 'WORKER_REQUEST_ID_REUSE_MISMATCH');
  });
});

test('local prefill is disabled unless worker is explicitly started with the gate', async () => {
  await withWorker({ allowLocalPrefill: false }, async ({ base }) => {
    const result = await json(await fetch(`${base}/v1/prefill-local`, {
      method: 'POST',
      headers: authHeaders({ 'content-type': 'application/json', 'x-uex-request-id': 'req-prefill-0001' }),
      body: JSON.stringify({ plan: { application_id: 'app-1' } }),
    }));
    assert.equal(result.status, 403);
    assert.equal(result.body.error.code, 'WORKER_LOCAL_PREFILL_DISABLED');
  });
});

test('missing request id and unknown JSON keys fail closed', async () => {
  await withWorker({}, async ({ base }) => {
    let result = await json(await fetch(`${base}/v1/inspect`, {
      method: 'POST',
      headers: authHeaders({ 'content-type': 'application/json' }),
      body: JSON.stringify({ provider: 'generic_html', url: 'http://127.0.0.1:3000/form', allowed_origins: ['http://127.0.0.1:3000'] }),
    }));
    assert.equal(result.status, 400);
    assert.equal(result.body.error.code, 'WORKER_REQUEST_ID_INVALID');

    result = await json(await fetch(`${base}/v1/inspect`, {
      method: 'POST',
      headers: authHeaders({ 'content-type': 'application/json', 'x-uex-request-id': 'req-inspect-0002' }),
      body: JSON.stringify({ provider: 'generic_html', url: 'http://127.0.0.1:3000/form', allowed_origins: ['http://127.0.0.1:3000'], command: 'submit' }),
    }));
    assert.equal(result.status, 400);
    assert.equal(result.body.error.code, 'WORKER_BODY_KEYS_INVALID');
  });
});
