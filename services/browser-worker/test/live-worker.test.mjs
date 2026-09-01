import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { BrowserWorkerSession } from '../src/session.mjs';
import { createBrowserWorkerServer } from '../src/server.mjs';

const TOKEN = 'live-worker-token-'.padEnd(48, 'z');

function fixtureHtml() {
  return `<!doctype html><html><head><title>Worker Fixture</title></head><body>
    <form id="application" method="post" action="/submit">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" required value="SECRET-DEFAULT">
      <label for="motivation">Motivation</label>
      <textarea id="motivation" name="motivation" minlength="10" maxlength="250" required>PRIVATE-DEFAULT</textarea>
      <button type="submit">Apply</button>
    </form>
    <script>
      fetch('/telemetry', {method:'POST', body:'LEAK-ME'}).catch(() => {});
      queueMicrotask(() => { try { document.getElementById('application').requestSubmit(); } catch (_) {} });
    </script>
  </body></html>`;
}

async function startFixture() {
  let mutatingRequests = 0;
  const server = http.createServer((request, response) => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) mutatingRequests += 1;
    if (request.url?.startsWith('/form')) {
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end(fixtureHtml());
      return;
    }
    response.writeHead(204);
    response.end();
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('fixture port missing');
  return { server, origin: `http://127.0.0.1:${address.port}`, mutationCount: () => mutatingRequests };
}

async function json(response) {
  return { status: response.status, body: await response.json() };
}

function headers(requestId) {
  return {
    authorization: `Bearer ${TOKEN}`,
    'content-type': 'application/json',
    'x-uex-request-id': requestId,
  };
}

function compiledPlan({ url, inspect }) {
  const answers = {
    email: 'candidate@example.com',
    motivation: 'A genuine motivation answer for this fixture.',
  };
  return {
    plan_id: 'plan-live-worker',
    application_id: 'app-live-worker',
    opportunity_id: 'opp-live-worker',
    canonical_form_url: url,
    provider: 'generic_html',
    form_fingerprint: inspect.form_fingerprint,
    validation_signature: inspect.validation_signature,
    ai_policy: 'ai_assist_only',
    auth_requirement: 'none',
    submit_authority: 'human_only',
    allowed_origins: [new URL(url).origin],
    created_at: new Date().toISOString(),
    expires_at: '2099-01-01T00:00:00.000Z',
    source_version: 'fixture-v1',
    attachments: [],
    state: 'prefill_ready',
    fields: inspect.fields.map((field) => ({
      ...field,
      answer: answers[field.field_key],
      answer_source: `fixture:${field.field_key}`,
      evidence_ids: [`ev-${field.field_key}`],
      ownership: field.field_key === 'email' ? 'green_agent_factual' : 'yellow_agent_assisted_human_review',
      sensitivity: 'private',
      editable_by_agent: true,
    })),
  };
}

test('worker keeps one live Chromium DOM across INSPECT -> PREFILL_LOCAL -> VALIDATE_LOCAL', { timeout: 90_000 }, async () => {
  const fixture = await startFixture();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-browser-worker-'));
  const session = new BrowserWorkerSession({ profileDir, channel: 'chromium', headless: true });
  const worker = createBrowserWorkerServer({ session, token: TOKEN, host: '127.0.0.1', port: 0, allowLocalPrefill: true });
  const address = await worker.listen();
  const base = `http://127.0.0.1:${address.port}`;
  const url = `${fixture.origin}/form?private=QUERY-SECRET#fragment`;
  try {
    const inspectedResponse = await json(await fetch(`${base}/v1/inspect`, {
      method: 'POST',
      headers: headers('req-live-inspect-0001'),
      body: JSON.stringify({ provider: 'generic_html', url, allowed_origins: [fixture.origin] }),
    }));
    assert.equal(inspectedResponse.status, 200);
    const inspect = inspectedResponse.body.result;
    assert.equal(inspect.mode, 'INSPECT_LOCAL_ONLY');
    assert.equal(inspect.safety.cross_origin_requests_allowed, false);
    assert.match(inspect.form_fingerprint, /^sha256:[0-9a-f]{64}$/);
    assert.match(inspect.validation_signature, /^sha256:[0-9a-f]{64}$/);
    assert.equal(inspect.page.url, `${fixture.origin}/form`);
    assert.equal(fixture.mutationCount(), 0);

    const plan = compiledPlan({ url, inspect });
    const prefilledResponse = await json(await fetch(`${base}/v1/prefill-local`, {
      method: 'POST',
      headers: headers('req-live-prefill-0001'),
      body: JSON.stringify({ plan }),
    }));
    assert.equal(prefilledResponse.status, 200);
    assert.equal(prefilledResponse.body.result.write_count, 2);
    assert.deepEqual(prefilledResponse.body.result.invalid_field_keys, []);
    assert.equal(fixture.mutationCount(), 0);

    const validatedResponse = await json(await fetch(`${base}/v1/validate-local`, {
      method: 'POST',
      headers: headers('req-live-validate-0001'),
      body: JSON.stringify({ plan }),
    }));
    assert.equal(validatedResponse.status, 200);
    const validation = validatedResponse.body.result;
    assert.equal(validation.all_values_match, true);
    assert.equal(validation.all_fields_valid, true);
    assert.equal(validation.form_fingerprint_match, true);
    assert.equal(validation.validation_signature_match, true);
    assert.equal(fixture.mutationCount(), 0);

    const status = await json(await fetch(`${base}/v1/status`, { headers: { authorization: `Bearer ${TOKEN}` } }));
    assert.equal(status.status, 200);
    assert.equal(status.body.result.current.application_id, 'app-live-worker');
    assert.equal(status.body.result.transport.submit_endpoint_present, false);
    assert.equal(status.body.result.safety.target_scope, 'loopback_only_v1');

    const serialized = JSON.stringify({ inspect, prefill: prefilledResponse.body.result, validation });
    for (const secret of ['QUERY-SECRET', 'SECRET-DEFAULT', 'PRIVATE-DEFAULT', 'candidate@example.com', 'A genuine motivation answer']) {
      assert.equal(serialized.includes(secret), false, `worker response leaked value: ${secret}`);
    }
  } finally {
    await worker.close();
    await new Promise((resolve) => fixture.server.close(resolve));
    fs.rmSync(profileDir, { recursive: true, force: true });
  }
});
