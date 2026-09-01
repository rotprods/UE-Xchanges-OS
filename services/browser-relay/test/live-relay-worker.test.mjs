import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/client';
import { InMemoryTransport } from '@modelcontextprotocol/server';
import { BrowserWorkerSession } from '../../browser-worker/src/session.mjs';
import { createBrowserWorkerServer } from '../../browser-worker/src/server.mjs';
import { canonicalBodyHash, issueRelayCapability } from '../src/capability.mjs';
import { createRelayMcpServer } from '../src/mcp-server.mjs';
import { BrowserRelayCore } from '../src/relay-core.mjs';
import { BrowserWorkerClient } from '../src/worker-client.mjs';

const WORKER_TOKEN = 'e2e-worker-token-'.padEnd(48, 'w');
const CAP_SECRET = Buffer.from('e'.repeat(48));

function fixtureHtml() {
  return `<!doctype html><html><head><title>Relay Fixture</title></head><body>
    <form id="application" method="post" action="/submit">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" required value="PRIVATE-EMAIL-DEFAULT">
      <label for="motivation">Motivation</label>
      <textarea id="motivation" name="motivation" minlength="10" maxlength="250" required>PRIVATE-MOTIVATION-DEFAULT</textarea>
      <button type="submit">Apply</button>
    </form>
    <script>
      fetch('/telemetry', {method:'POST', body:'EXFILTRATE-ME'}).catch(() => {});
      queueMicrotask(() => { try { document.getElementById('application').requestSubmit(); } catch (_) {} });
    </script>
  </body></html>`;
}

async function startFixture() {
  let mutations = 0;
  const server = http.createServer((request, response) => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) mutations += 1;
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
  return { server, origin: `http://127.0.0.1:${address.port}`, mutationCount: () => mutations };
}

function buildPlan(url, inspect) {
  const answers = {
    email: 'candidate@example.com',
    motivation: 'A genuine fixture answer long enough for validation.',
  };
  return {
    plan_id: 'plan-relay-e2e',
    application_id: 'app-relay-e2e',
    opportunity_id: 'opp-relay-e2e',
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

async function mcpPair(core) {
  const server = createRelayMcpServer({ core });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: 'relay-e2e-client', version: '0.1.0' });
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  return { client, server };
}

test('MCP relay drives loopback Worker and one live Chromium DOM without Submit', { timeout: 120_000 }, async () => {
  const fixture = await startFixture();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-relay-e2e-profile-'));
  const workerSession = new BrowserWorkerSession({ profileDir, channel: 'chromium', headless: true });
  const worker = createBrowserWorkerServer({ session: workerSession, token: WORKER_TOKEN, host: '127.0.0.1', port: 0, allowLocalPrefill: true });
  const workerAddress = await worker.listen();
  const workerClient = new BrowserWorkerClient({ baseUrl: `http://127.0.0.1:${workerAddress.port}/`, token: WORKER_TOKEN });
  const core = new BrowserRelayCore({ workerClient, capabilitySecret: CAP_SECRET });
  const { client, server } = await mcpPair(core);
  const targetUrl = `${fixture.origin}/form?private=QUERY-CANARY#fragment`;

  try {
    const inspectedCall = await client.callTool({
      name: 'browser_inspect_local',
      arguments: {
        request_id: 'req-relay-inspect-0001',
        provider: 'generic_html',
        url: targetUrl,
        allowed_origins: [fixture.origin],
      },
    });
    assert.equal(inspectedCall.isError, undefined);
    const inspect = inspectedCall.structuredContent;
    assert.equal(inspect.mode, 'INSPECT_LOCAL_ONLY');
    assert.equal(fixture.mutationCount(), 0);

    const plan = buildPlan(targetUrl, inspect);
    const prefillRequestId = 'req-relay-prefill-0001';
    const bodyHash = canonicalBodyHash({ plan });
    const capability = issueRelayCapability({ operation: 'prefill-local', requestId: prefillRequestId, bodyHash, secret: CAP_SECRET, ttlSeconds: 120 });
    const prefilledCall = await client.callTool({
      name: 'browser_prefill_local',
      arguments: { request_id: prefillRequestId, plan, capability },
    });
    assert.equal(prefilledCall.isError, undefined);
    assert.equal(prefilledCall.structuredContent.write_count, 2);
    assert.equal(fixture.mutationCount(), 0);

    const validatedCall = await client.callTool({
      name: 'browser_validate_local',
      arguments: { request_id: 'req-relay-validate-0001', plan },
    });
    assert.equal(validatedCall.isError, undefined);
    assert.equal(validatedCall.structuredContent.all_values_match, true);
    assert.equal(validatedCall.structuredContent.all_fields_valid, true);
    assert.equal(fixture.mutationCount(), 0);

    const serialized = JSON.stringify({ inspect, prefill: prefilledCall.structuredContent, validate: validatedCall.structuredContent });
    for (const canary of ['QUERY-CANARY', 'PRIVATE-EMAIL-DEFAULT', 'PRIVATE-MOTIVATION-DEFAULT', 'candidate@example.com', 'A genuine fixture answer', WORKER_TOKEN]) {
      assert.equal(serialized.includes(canary), false, `relay output leaked canary: ${canary}`);
    }

    const { tools } = await client.listTools();
    assert.equal(tools.some((tool) => /submit|cookie|storage|shell|eval|payment|upload/i.test(tool.name)), false);
  } finally {
    await client.close();
    await server.close();
    await worker.close();
    await new Promise((resolve) => fixture.server.close(resolve));
    fs.rmSync(profileDir, { recursive: true, force: true });
  }
});
