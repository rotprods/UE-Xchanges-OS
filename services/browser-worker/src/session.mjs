import fs from 'node:fs';
import { chromium } from 'playwright';
import { extractNativeFormSchema } from '../../../tools/form-executor/src/dom-schema.mjs';
import { canonicalizeFormUrl, formSchemaFingerprint } from '../../../tools/form-executor/src/fingerprint.mjs';
import {
  assertDedicatedProfileDir,
  networkDecision,
  normalizeAllowedOrigins,
  normalizeOrigin,
} from '../../../tools/form-executor/src/guard.mjs';
import { validateLocalPrefillPlan } from '../../../tools/form-executor/src/prefill-policy.mjs';
import {
  createValidationExpectation,
  extractValidationSnapshot,
  validatePageAgainstExpectation,
} from '../../../tools/form-executor/src/validate-diff.mjs';
import { validationSignature } from '../../../tools/form-executor/src/validation-signature.mjs';
import { profileRef } from './security.mjs';

const SUBMIT_BLOCK_INIT_SCRIPT = `(() => {
  Object.defineProperty(window, '__UEX_BROWSER_WORKER__', { value: true, configurable: false });
  window.addEventListener('submit', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
  if (globalThis.HTMLFormElement) {
    HTMLFormElement.prototype.submit = function () { throw new Error('UEX_WORKER_SUBMIT_BLOCKED'); };
    HTMLFormElement.prototype.requestSubmit = function () { throw new Error('UEX_WORKER_SUBMIT_BLOCKED'); };
  }
})();`;

function clean(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

async function applyPrefillWrites(page, writes) {
  return page.evaluate((requestedWrites) => {
    const cleanText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const labelFor = (el) => {
      const labels = el.labels ? Array.from(el.labels).map((label) => cleanText(label.textContent)).filter(Boolean) : [];
      if (labels.length) return labels.join(' / ');
      const aria = cleanText(el.getAttribute('aria-label'));
      if (aria) return aria;
      const fieldset = el.closest('fieldset');
      const legend = fieldset ? cleanText(fieldset.querySelector('legend')?.textContent) : '';
      if (legend) return legend;
      return cleanText(el.getAttribute('name')) || cleanText(el.id) || 'Unnamed field';
    };
    const controls = Array.from(document.querySelectorAll('input, textarea, select')).filter((el) => {
      if (el instanceof HTMLInputElement) {
        const type = (el.getAttribute('type') || 'text').toLowerCase();
        return !['hidden', 'button', 'submit', 'reset', 'image'].includes(type);
      }
      return true;
    });
    const keyed = new Map();
    const grouped = new Map();
    const used = new Set();
    for (let index = 0; index < controls.length; index += 1) {
      const el = controls[index];
      const inputType = el instanceof HTMLInputElement ? (el.getAttribute('type') || 'text').toLowerCase() : '';
      const groupable = inputType === 'radio' || inputType === 'checkbox';
      const rawKey = cleanText(el.getAttribute('name')) || cleanText(el.id) || `control-${index + 1}`;
      if (groupable) {
        if (!grouped.has(rawKey)) grouped.set(rawKey, []);
        grouped.get(rawKey).push(el);
        continue;
      }
      let key = rawKey;
      if (used.has(key)) key = `${key}#${index + 1}`;
      used.add(key);
      keyed.set(key, el);
    }
    for (const [key, elements] of grouped) keyed.set(key, elements);

    const event = (name) => new Event(name, { bubbles: true, composed: true });
    const optionIdentity = (el) => labelFor(el) || cleanText(el.value);
    const touched = [];
    const invalid = [];

    for (const write of requestedWrites) {
      const target = keyed.get(write.field_key);
      if (!target) throw new Error('UEX_WORKER_PREFILL_FIELD_NOT_FOUND');

      if (Array.isArray(target)) {
        if (write.field_type === 'radio') {
          const wanted = String(write.answer);
          const match = target.find((el) => optionIdentity(el) === wanted || cleanText(el.value) === wanted);
          if (!match) throw new Error('UEX_WORKER_PREFILL_OPTION_NOT_FOUND');
          for (const el of target) el.checked = el === match;
          match.dispatchEvent(event('input'));
          match.dispatchEvent(event('change'));
        } else if (write.field_type === 'checkbox') {
          const wanted = Array.isArray(write.answer) ? new Set(write.answer.map(String)) : null;
          if (!wanted) throw new Error('UEX_WORKER_CHECKBOX_GROUP_REQUIRES_ARRAY');
          for (const el of target) {
            const identity = optionIdentity(el);
            const next = wanted.has(identity) || wanted.has(cleanText(el.value));
            if (el.checked !== next) {
              el.checked = next;
              el.dispatchEvent(event('input'));
              el.dispatchEvent(event('change'));
            }
          }
        } else throw new Error('UEX_WORKER_GROUP_TYPE_MISMATCH');
      } else if (target instanceof HTMLSelectElement) {
        const wanted = String(write.answer);
        const option = Array.from(target.options).find((item) => cleanText(item.textContent) === wanted || item.value === wanted);
        if (!option) throw new Error('UEX_WORKER_PREFILL_OPTION_NOT_FOUND');
        target.value = option.value;
        target.dispatchEvent(event('input'));
        target.dispatchEvent(event('change'));
      } else if (target instanceof HTMLInputElement && (target.type || '').toLowerCase() === 'checkbox') {
        if (typeof write.answer !== 'boolean') throw new Error('UEX_WORKER_SINGLE_CHECKBOX_REQUIRES_BOOLEAN');
        target.checked = write.answer;
        target.dispatchEvent(event('input'));
        target.dispatchEvent(event('change'));
      } else {
        target.value = String(write.answer);
        target.dispatchEvent(event('input'));
        target.dispatchEvent(event('change'));
      }

      touched.push(write.field_key);
      const validityTargets = Array.isArray(target) ? target : [target];
      if (!validityTargets.some((el) => typeof el.checkValidity !== 'function' || el.checkValidity())) {
        invalid.push(write.field_key);
      }
    }
    return { touched, invalid };
  }, writes);
}

export class BrowserWorkerSession {
  constructor({ profileDir, channel = 'chromium', headless = true }) {
    this.profileDir = assertDedicatedProfileDir(profileDir);
    this.channel = channel;
    this.headless = headless;
    this.context = null;
    this.page = null;
    this.policy = { mode: 'locked', allowedOrigins: [], sameOriginOnly: false };
    this.current = null;
  }

  async start() {
    if (this.context) return;
    fs.mkdirSync(this.profileDir, { recursive: true, mode: 0o700 });
    const launchOptions = { headless: this.headless, viewport: { width: 1440, height: 1000 } };
    if (this.channel !== 'chromium') launchOptions.channel = this.channel;
    this.context = await chromium.launchPersistentContext(this.profileDir, launchOptions);
    await this.context.addInitScript({ content: SUBMIT_BLOCK_INIT_SCRIPT });
    this.page = this.context.pages()[0] || (await this.context.newPage());
    await this.page.route('**/*', async (route) => {
      const request = route.request();
      let decision = { action: 'abort', reason: 'worker_locked' };
      try {
        if (this.policy.mode !== 'locked') {
          const requestOrigin = normalizeOrigin(request.url());
          if (this.policy.sameOriginOnly && requestOrigin !== this.policy.allowedOrigins[0]) {
            decision = { action: 'abort', reason: 'cross_origin_request_blocked' };
          } else {
            const isTopLevelNavigation = request.isNavigationRequest() && request.frame() === this.page.mainFrame();
            decision = networkDecision({
              method: request.method(),
              url: request.url(),
              isTopLevelNavigation,
              allowedOrigins: this.policy.allowedOrigins,
            });
          }
        }
      } catch {
        decision = { action: 'abort', reason: 'invalid_request_url' };
      }
      if (decision.action === 'abort') await route.abort('blockedbyclient');
      else await route.continue();
    });
  }

  status() {
    return {
      worker_session: 'persistent_single_context',
      browser_channel: this.channel,
      headless: this.headless,
      profile_ref: profileRef(this.profileDir),
      current: this.current
        ? {
            provider: this.current.provider,
            page_url: this.current.safePageUrl,
            form_fingerprint: this.current.formFingerprint,
            validation_signature: this.current.validationSignature,
            inspected_at: this.current.inspectedAt,
            application_id: this.current.applicationId,
          }
        : null,
      safety: {
        submit_api_present: false,
        cookies_exported: false,
        storage_state_exported: false,
      },
    };
  }

  async inspect({ provider, url, allowedOrigins }) {
    await this.start();
    const normalizedOrigins = normalizeAllowedOrigins([normalizeOrigin(url), ...allowedOrigins]);
    this.policy = { mode: 'inspect', allowedOrigins: normalizedOrigins, sameOriginOnly: false };
    try {
      await this.page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      if (!normalizedOrigins.includes(normalizeOrigin(this.page.url()))) throw new Error('WORKER_FINAL_ORIGIN_NOT_ALLOWED');
      const structural = await extractNativeFormSchema(this.page);
      const validationFields = await extractValidationSnapshot(this.page);
      const formFingerprint = formSchemaFingerprint({ provider, canonicalFormUrl: url, fields: structural.fields });
      const validationSig = validationSignature({ provider, canonicalFormUrl: url, fields: validationFields });
      const expectation = createValidationExpectation({ provider, canonicalFormUrl: url, fields: validationFields });
      this.current = {
        provider,
        canonicalFormUrl: url,
        safePageUrl: structural.page.url,
        formFingerprint,
        validationSignature: validationSig,
        expectation,
        inspectedAt: new Date().toISOString(),
        applicationId: null,
      };
      return {
        mode: 'INSPECT_ONLY',
        provider,
        page: structural.page,
        forms: structural.forms,
        fields: structural.fields,
        submit_controls: structural.submit_controls,
        unsupported_custom_control_count: structural.unsupported_custom_control_count,
        form_fingerprint: formFingerprint,
        validation_signature: validationSig,
        safety: {
          form_values_read: false,
          url_query_material_exported: false,
          cookies_read: false,
          storage_state_exported: false,
          mutating_http_methods_blocked: true,
          submit_events_blocked: true,
        },
      };
    } finally {
      this.policy = { mode: 'locked', allowedOrigins: [], sameOriginOnly: false };
    }
  }

  assertCurrentPlan(plan) {
    if (!this.current) throw new Error('WORKER_INSPECT_REQUIRED');
    if (canonicalizeFormUrl(plan.canonical_form_url) !== canonicalizeFormUrl(this.current.canonicalFormUrl)) {
      throw new Error('WORKER_PLAN_URL_MISMATCH');
    }
    if (plan.provider !== this.current.provider) throw new Error('WORKER_PLAN_PROVIDER_MISMATCH');
    if (plan.form_fingerprint !== this.current.formFingerprint) throw new Error('WORKER_PLAN_FINGERPRINT_MISMATCH');
    if (plan.validation_signature !== this.current.validationSignature) throw new Error('WORKER_PLAN_VALIDATION_MISMATCH');
  }

  async prefillLocal(plan) {
    await this.start();
    this.assertCurrentPlan(plan);
    const validated = validateLocalPrefillPlan(plan);
    if (normalizeOrigin(this.page.url()) !== validated.origin) throw new Error('WORKER_PAGE_ORIGIN_MISMATCH');
    this.policy = { mode: 'local', allowedOrigins: [validated.origin], sameOriginOnly: true };
    try {
      const before = await extractNativeFormSchema(this.page);
      const beforeFp = formSchemaFingerprint({ provider: plan.provider, canonicalFormUrl: plan.canonical_form_url, fields: before.fields });
      const validationFields = await extractValidationSnapshot(this.page);
      const beforeValidation = validationSignature({ provider: plan.provider, canonicalFormUrl: plan.canonical_form_url, fields: validationFields });
      if (beforeFp !== plan.form_fingerprint) throw new Error('WORKER_FORM_FINGERPRINT_DRIFT');
      if (beforeValidation !== plan.validation_signature) throw new Error('WORKER_VALIDATION_SIGNATURE_DRIFT');

      const written = await applyPrefillWrites(this.page, validated.writes);
      const after = await extractNativeFormSchema(this.page);
      const afterFp = formSchemaFingerprint({ provider: plan.provider, canonicalFormUrl: plan.canonical_form_url, fields: after.fields });
      if (afterFp !== beforeFp) throw new Error('WORKER_FORM_CHANGED_DURING_PREFILL');
      this.current.applicationId = plan.application_id;
      return {
        mode: 'PREFILL_LOCAL_ONLY',
        application_id: plan.application_id,
        form_fingerprint: beforeFp,
        validation_signature: beforeValidation,
        write_count: written.touched.length,
        written_field_keys: written.touched,
        invalid_field_keys: written.invalid,
        protected_field_keys: validated.protectedFields,
        safety: {
          external_origins_allowed: false,
          submit_blocked: true,
          mutating_http_methods_blocked: true,
          cookies_read: false,
          storage_state_exported: false,
          answer_values_exported: false,
        },
      };
    } finally {
      this.policy = { mode: 'locked', allowedOrigins: [], sameOriginOnly: false };
    }
  }

  async validateLocal(plan) {
    await this.start();
    this.assertCurrentPlan(plan);
    if (!this.current.expectation) throw new Error('WORKER_VALIDATION_EXPECTATION_MISSING');
    const report = await validatePageAgainstExpectation({
      page: this.page,
      plan,
      expectation: this.current.expectation,
    });
    return {
      ...report,
      mode: 'VALIDATE_LOCAL_ONLY',
      safety: {
        ...report.safety,
        submit_blocked: true,
      },
    };
  }

  async close() {
    if (this.context) await this.context.close();
    this.context = null;
    this.page = null;
    this.current = null;
    this.policy = { mode: 'locked', allowedOrigins: [], sameOriginOnly: false };
  }
}
