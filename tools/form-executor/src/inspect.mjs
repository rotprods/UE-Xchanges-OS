import fs from 'node:fs';
import { chromium } from 'playwright';
import { extractProviderFormSchema } from './providers/provider-extractor.mjs';
import { buildInspectIdentity } from './inspect-identity.mjs';
import { extractValidationSnapshot } from './validate-diff.mjs';
import {
  assertDedicatedProfileDir,
  networkDecision,
  normalizeAllowedOrigins,
  normalizeOrigin,
} from './guard.mjs';

const INSPECT_ONLY_INIT_SCRIPT = `(() => {
  Object.defineProperty(window, '__UEX_INSPECT_ONLY__', { value: true, configurable: false });
  window.addEventListener('submit', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
  if (globalThis.HTMLFormElement) {
    HTMLFormElement.prototype.submit = function () {
      throw new Error('UEX_INSPECT_ONLY_SUBMIT_BLOCKED');
    };
    HTMLFormElement.prototype.requestSubmit = function () {
      throw new Error('UEX_INSPECT_ONLY_SUBMIT_BLOCKED');
    };
  }
})();`;

function ensureAllowedFinalUrl(url, allowedOrigins) {
  const finalOrigin = normalizeOrigin(url);
  if (!normalizeAllowedOrigins(allowedOrigins).includes(finalOrigin)) {
    throw new Error(`final top-level origin is not allowlisted: ${finalOrigin}`);
  }
}

export async function inspectForm({
  url,
  profileDir,
  allowedOrigins,
  headless = false,
  channel = 'chrome',
  timeoutMs = 20_000,
  provider = 'generic_html',
}) {
  const normalizedOrigins = normalizeAllowedOrigins([normalizeOrigin(url), ...allowedOrigins]);
  const dedicatedProfileDir = assertDedicatedProfileDir(profileDir);
  fs.mkdirSync(dedicatedProfileDir, { recursive: true, mode: 0o700 });

  const launchOptions = {
    headless,
    viewport: { width: 1440, height: 1000 },
  };
  if (channel !== 'chromium') launchOptions.channel = channel;

  const context = await chromium.launchPersistentContext(dedicatedProfileDir, launchOptions);
  try {
    await context.addInitScript({ content: INSPECT_ONLY_INIT_SCRIPT });
    const page = context.pages()[0] || (await context.newPage());

    await page.route('**/*', async (route) => {
      const request = route.request();
      const isTopLevelNavigation = request.isNavigationRequest() && request.frame() === page.mainFrame();
      let decision;
      try {
        decision = networkDecision({
          method: request.method(),
          url: request.url(),
          isTopLevelNavigation,
          allowedOrigins: normalizedOrigins,
        });
      } catch {
        decision = { action: 'abort', reason: 'invalid_request_url' };
      }
      if (decision.action === 'abort') await route.abort('blockedbyclient');
      else await route.continue();
    });

    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: timeoutMs });
    ensureAllowedFinalUrl(page.url(), normalizedOrigins);
    const result = await extractProviderFormSchema(page, provider);
    const validationFields = provider === 'generic_html' ? await extractValidationSnapshot(page) : [];
    const identity = buildInspectIdentity({
      provider,
      canonicalFormUrl: page.url(),
      structuralFields: result.fields,
      validationFields,
    });

    result.mode = 'INSPECT_ONLY';
    result.identity_version = identity.identity_version;
    result.provider = identity.provider;
    result.form_fingerprint = identity.form_fingerprint;
    result.validation_signature = identity.validation_signature;
    result.allowed_origins = normalizedOrigins;
    result.profile_mode = 'dedicated_persistent';
    result.browser_channel = channel;
    result.safety = {
      form_values_read: false,
      url_query_material_exported: false,
      cookies_read: false,
      storage_state_exported: false,
      mutating_http_methods_blocked: true,
      submit_events_blocked: true,
    };
    return result;
  } finally {
    await context.close();
  }
}
