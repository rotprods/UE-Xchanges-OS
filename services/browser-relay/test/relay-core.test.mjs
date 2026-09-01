import test from 'node:test';
import assert from 'node:assert/strict';
import { BrowserRelayCore } from '../src/relay-core.mjs';
import { canonicalBodyHash, issueRelayCapability } from '../src/capability.mjs';

const SECRET = Buffer.from('c'.repeat(48));
const PLAN = {
  application_id: 'app-1',
  canonical_form_url: 'http://127.0.0.1:39000/form',
  provider: 'generic_html',
  form_fingerprint: `sha256:${'f'.repeat(64)}`,
  validation_signature: `sha256:${'1'.repeat(64)}`,
};

function fakeWorker() {
  const calls = [];
  return {
    calls,
    safeDescriptor: () => ({ worker_transport: 'loopback_http', worker_origin: 'http://127.0.0.1:4777', token_configured: true }),
    status: async () => ({ worker_session: 'fake' }),
    inspectLocal: async (input) => { calls.push(['inspect', input]); return { mode: 'INSPECT_LOCAL_ONLY' }; },
    validateLocal: async (input) => { calls.push(['validate', input]); return { all_values_match: true }; },
    prefillLocal: async (input) => { calls.push(['prefill', input]); return { write_count: 1 }; },
  };
}

test('status exposes descriptor/capability ceiling but no secret-bearing fields', async () => {
  const worker = fakeWorker();
  const core = new BrowserRelayCore({ workerClient: worker, capabilitySecret: SECRET });
  const status = await core.status();
  assert.equal(status.capabilities.submit, false);
  assert.equal(status.capabilities.external_prefill, false);
  assert.equal(status.capabilities.prefill_local, 'hmac_capability_required');
  assert.equal(JSON.stringify(status).includes('cccccccccccccccc'), false);
});

test('inspect and validate remain loopback-only', async () => {
  const worker = fakeWorker();
  const core = new BrowserRelayCore({ workerClient: worker, capabilitySecret: SECRET });
  await core.inspectLocal({ requestId: 'req-inspect-0001', provider: 'generic_html', url: PLAN.canonical_form_url, allowedOrigins: ['http://127.0.0.1:39000'] });
  await core.validateLocal({ requestId: 'req-validate-0001', plan: PLAN });
  assert.equal(worker.calls.length, 2);
  assert.throws(() => core.inspectLocal({ requestId: 'req-inspect-0002', provider: 'generic_html', url: 'https://example.com/form', allowedOrigins: ['https://example.com'] }), /RELAY_TARGET_NOT_LOOPBACK/);
});

test('prefill cannot reach worker without a valid exact capability', async () => {
  const worker = fakeWorker();
  const core = new BrowserRelayCore({ workerClient: worker, capabilitySecret: SECRET });
  const requestId = 'req-prefill-0001';
  assert.throws(() => core.prefillLocal({ requestId, plan: PLAN, capability: 'invalid-token-value-that-is-long-enough' }), /RELAY_CAPABILITY_MALFORMED/);
  assert.equal(worker.calls.length, 0);

  const bodyHash = canonicalBodyHash({ plan: PLAN });
  const capability = issueRelayCapability({ operation: 'prefill-local', requestId, bodyHash, secret: SECRET, ttlSeconds: 120 });
  const result = await core.prefillLocal({ requestId, plan: PLAN, capability });
  assert.equal(result.write_count, 1);
  assert.equal(worker.calls.length, 1);

  const changed = { ...PLAN, application_id: 'app-2' };
  assert.throws(() => core.prefillLocal({ requestId, plan: changed, capability }), /RELAY_CAPABILITY_BINDING_MISMATCH/);
  assert.equal(worker.calls.length, 1);
});
