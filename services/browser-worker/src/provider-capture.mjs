import { chromium } from 'playwright';
import { extractProviderFormSchema } from '../../../tools/form-executor/src/providers/provider-extractor.mjs';
import { buildInspectIdentity } from '../../../tools/form-executor/src/inspect-identity.mjs';
import { normalizeAllowedOrigins, normalizeOrigin } from '../../../tools/form-executor/src/guard.mjs';

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1']);
const SUBMIT_BLOCK_INIT_SCRIPT = `(() => {
  Object.defineProperty(window, '__UEX_PROVIDER_CAPTURE__', { value: true, configurable: false });
  window.addEventListener('submit', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
  if (globalThis.HTMLFormElement) {
    HTMLFormElement.prototype.submit = function () { throw new Error('UEX_PROVIDER_CAPTURE_SUBMIT_BLOCKED'); };
    HTMLFormElement.prototype.requestSubmit = function () { throw new Error('UEX_PROVIDER_CAPTURE_SUBMIT_BLOCKED'); };
  }
})();`;

function normalizedHost(parsed) {
  const raw = parsed.hostname.toLowerCase();
  return raw.startsWith('[') && raw.endsWith(']') ? raw.slice(1, -1) : raw;
}

export function assertProviderTargetUrl(value, { allowInsecureLoopback = false } = {}) {
  if (typeof value !== 'string') throw new Error('PROVIDER_CAPTURE_URL_INVALID');
  const parsed = new URL(value);
  const host = normalizedHost(parsed);
  const loopback = LOOPBACK_HOSTS.has(host);
  if (parsed.username || parsed.password || parsed.hash) throw new Error('PROVIDER_CAPTURE_URL_INVALID');
  if (parsed.protocol !== 'https:' && !(allowInsecureLoopback && loopback && parsed.protocol === 'http:')) {
    throw new Error('PROVIDER_CAPTURE_HTTPS_REQUIRED');
  }
  return parsed;
}

export function providerNetworkDecision({ method, url, allowedOrigins, allowInsecureLoopback = false }) {
  const normalizedMethod = String(method || '').toUpperCase();
  if (!SAFE_METHODS.has(normalizedMethod)) return { action: 'abort', reason: 'mutating_http_method' };
  let parsed;
  try { parsed = assertProviderTargetUrl(url, { allowInsecureLoopback }); }
  catch { return { action: 'abort', reason: 'invalid_or_insecure_url' }; }
  const origin = parsed.origin.toLowerCase();
  const allowed = new Set(normalizeAllowedOrigins(allowedOrigins));
  if (!allowed.has(origin)) return { action: 'abort', reason: 'origin_not_certified' };
  return { action: 'continue', reason: 'certified_read_only_request' };
}

export class ProviderCaptureService {
  constructor({ channel = 'chromium', headless = true, allowInsecureLoopback = false } = {}) {
    this.channel = channel;
    this.headless = headless;
    this.allowInsecureLoopback = allowInsecureLoopback;
  }

  async inspect({ applicationId, provider, url, allowedOrigins }) {
    if (typeof applicationId !== 'string' || !applicationId.trim()) throw new Error('PROVIDER_CAPTURE_APPLICATION_ID_INVALID');
    if (typeof provider !== 'string' || !provider.trim()) throw new Error('PROVIDER_CAPTURE_PROVIDER_INVALID');
    const target = assertProviderTargetUrl(url, { allowInsecureLoopback: this.allowInsecureLoopback });
    const normalizedOrigins = normalizeAllowedOrigins([target.origin, ...allowedOrigins]);
    for (const origin of normalizedOrigins) assertProviderTargetUrl(origin, { allowInsecureLoopback: this.allowInsecureLoopback });

    const launchOptions = { headless: this.headless };
    if (this.channel !== 'chromium') launchOptions.channel = this.channel;
    const browser = await chromium.launch(launchOptions);
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    try {
      await context.addInitScript({ content: SUBMIT_BLOCK_INIT_SCRIPT });
      const page = await context.newPage();
      context.on('page', async (candidate) => {
        if (candidate !== page) {
          try { await candidate.close(); } catch {}
        }
      });
      await context.route('**/*', async (route) => {
        const request = route.request();
        const decision = providerNetworkDecision({
          method: request.method(),
          url: request.url(),
          allowedOrigins: normalizedOrigins,
          allowInsecureLoopback: this.allowInsecureLoopback,
        });
        if (decision.action === 'abort') await route.abort('blockedbyclient');
        else await route.continue();
      });
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
      if (!normalizedOrigins.includes(normalizeOrigin(page.url()))) throw new Error('PROVIDER_CAPTURE_FINAL_ORIGIN_NOT_CERTIFIED');
      const structural = await extractProviderFormSchema(page, provider);
      if (!Array.isArray(structural.fields) || structural.fields.length === 0) throw new Error('PROVIDER_CAPTURE_SCHEMA_EMPTY');
      const identity = buildInspectIdentity({
        provider,
        canonicalFormUrl: page.url(),
        structuralFields: structural.fields,
        validationFields: [],
      });
      return {
        mode: 'INSPECT_PROVIDER_READ_ONLY',
        application_id: applicationId,
        provider: identity.provider,
        page: structural.page,
        forms: structural.forms,
        fields: structural.fields,
        submit_controls: structural.submit_controls,
        unsupported_custom_control_count: structural.unsupported_custom_control_count,
        form_fingerprint: identity.form_fingerprint,
        validation_signature: identity.validation_signature,
        captured_at: new Date().toISOString(),
        safety: {
          ephemeral_context: true,
          previous_session_cookies_available: false,
          form_values_read: false,
          answer_values_exported: false,
          url_query_material_exported: false,
          cookies_exported: false,
          storage_state_exported: false,
          mutating_http_methods_blocked: true,
          uncertified_origins_blocked: true,
          submit_events_blocked: true,
          external_prefill_available: false,
          submit_available: false,
        },
      };
    } finally {
      await context.close();
      await browser.close();
    }
  }
}
