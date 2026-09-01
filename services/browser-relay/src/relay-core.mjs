import { canonicalBodyHash, verifyRelayCapability } from './capability.mjs';
import { assertLoopbackWorkerUrl, normalizedHostname } from './worker-client.mjs';

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1']);

function assertLoopbackTarget(value) {
  if (typeof value !== 'string') throw new Error('RELAY_TARGET_URL_INVALID');
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol) || !LOOPBACK_HOSTS.has(normalizedHostname(parsed)) || parsed.username || parsed.password) {
    throw new Error('RELAY_TARGET_NOT_LOOPBACK');
  }
  return value;
}

function assertPlainPlan(plan) {
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) throw new Error('RELAY_PLAN_INVALID');
  for (const key of ['application_id', 'canonical_form_url', 'provider', 'form_fingerprint', 'validation_signature']) {
    if (typeof plan[key] !== 'string' || !plan[key].trim()) throw new Error('RELAY_PLAN_IDENTITY_INVALID');
  }
  assertLoopbackTarget(plan.canonical_form_url);
  return plan;
}

export class BrowserRelayCore {
  constructor({ workerClient, capabilitySecret }) {
    if (!workerClient || typeof workerClient.status !== 'function') throw new Error('RELAY_WORKER_CLIENT_INVALID');
    if (!Buffer.isBuffer(capabilitySecret) || capabilitySecret.length < 32) throw new Error('RELAY_CAPABILITY_SECRET_INVALID');
    this.workerClient = workerClient;
    this.capabilitySecret = capabilitySecret;
  }

  async status() {
    const worker = await this.workerClient.status();
    return {
      relay_version: '0.1.0',
      transport: 'mcp_stdio_to_loopback_worker',
      worker: { reachable: true, descriptor: this.workerClient.safeDescriptor(), status: worker },
      capabilities: {
        status: true,
        inspect_local: true,
        validate_local: true,
        prefill_local: 'hmac_capability_required',
        external_inspect: false,
        external_prefill: false,
        submit: false,
        upload: false,
        payment: false,
      },
    };
  }

  inspectLocal({ requestId, provider, url, allowedOrigins }) {
    assertLoopbackTarget(url);
    for (const origin of allowedOrigins) assertLoopbackTarget(origin);
    return this.workerClient.inspectLocal({ requestId, provider, url, allowedOrigins });
  }

  validateLocal({ requestId, plan }) {
    assertPlainPlan(plan);
    return this.workerClient.validateLocal({ requestId, plan });
  }

  prefillLocal({ requestId, plan, capability }) {
    assertPlainPlan(plan);
    const bodyHash = canonicalBodyHash({ plan });
    const verification = verifyRelayCapability({ token: capability, operation: 'prefill-local', requestId, bodyHash, secret: this.capabilitySecret });
    if (!verification.valid) throw new Error(verification.code);
    return this.workerClient.prefillLocal({ requestId, plan });
  }
}

export { assertLoopbackTarget, assertPlainPlan, assertLoopbackWorkerUrl };
