import fs from 'node:fs';
import { chromium } from 'playwright';
import { extractNativeFormSchema } from './dom-schema.mjs';
import { formSchemaFingerprint } from './fingerprint.mjs';
import { assertDedicatedProfileDir, networkDecision, normalizeOrigin } from './guard.mjs';

const PREFILL_ALLOWED_STATES = new Set(['answer_pack_resolved', 'prefill_ready']);
const EDITABLE_OWNERSHIP = new Set(['green_agent_factual', 'yellow_agent_assisted_human_review']);
const PLAN_BLOCKING_OWNERSHIP = new Set(['black_secret_or_never_model', 'unresolved']);
const SUPPORTED_TYPES = new Set(['text', 'textarea', 'email', 'number', 'date', 'select', 'radio', 'checkbox']);
const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '[::1]']);

const PREFILL_ONLY_INIT_SCRIPT = `(() => {
  Object.defineProperty(window, '__UEX_PREFILL_ONLY__', { value: true, configurable: false });
  window.addEventListener('submit', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
  if (globalThis.HTMLFormElement) {
    HTMLFormElement.prototype.submit = function () {
      throw new Error('UEX_PREFILL_ONLY_SUBMIT_BLOCKED');
    };
    HTMLFormElement.prototype.requestSubmit = function () {
      throw new Error('UEX_PREFILL_ONLY_SUBMIT_BLOCKED');
    };
  }
})();`;

export function assertLoopbackUrl(value) {
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('prefill URL must use http or https');
  if (!LOOPBACK_HOSTS.has(parsed.hostname)) {
    throw new Error('PREFILL_LOCAL development mode rejects non-loopback origins');
  }
  return parsed;
}

function assertIsoFuture(value, now) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) throw new Error('plan expires_at must be an ISO date-time');
  if (parsed.getTime() <= now.getTime()) throw new Error('execution plan is expired');
}

export function validateLocalPrefillPlan(plan, { now = new Date() } = {}) {
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) throw new Error('plan must be an object');
  for (const key of ['plan_id', 'application_id', 'opportunity_id', 'canonical_form_url', 'provider', 'form_fingerprint', 'state', 'expires_at']) {
    if (typeof plan[key] !== 'string' || !plan[key].trim()) throw new Error(`plan ${key} must be non-empty`);
  }
  const parsedUrl = assertLoopbackUrl(plan.canonical_form_url);
  if (!PREFILL_ALLOWED_STATES.has(plan.state)) throw new Error('plan state is not prefill-ready');
  assertIsoFuture(plan.expires_at, now);
  if (!Array.isArray(plan.fields) || plan.fields.length === 0) throw new Error('plan fields must not be empty');
  if (Array.isArray(plan.attachments) && plan.attachments.length) {
    throw new Error('file attachments are not supported by PREFILL_LOCAL');
  }

  const seen = new Set();
  const writes = [];
  const protectedFields = [];
  for (const field of plan.fields) {
    if (!field || typeof field !== 'object') throw new Error('every field must be an object');
    if (typeof field.field_key !== 'string' || !field.field_key.trim()) throw new Error('field_key must be non-empty');
    if (seen.has(field.field_key)) throw new Error(`duplicate field_key: ${field.field_key}`);
    seen.add(field.field_key);

    const editable = field.editable_by_agent === true;
    const ownership = field.ownership;
    const sensitivity = field.sensitivity;
    if (PLAN_BLOCKING_OWNERSHIP.has(ownership)) {
      throw new Error(`prefill-ready plan cannot contain ${ownership}: ${field.field_key}`);
    }
    if (editable) {
      if (!EDITABLE_OWNERSHIP.has(ownership)) throw new Error(`editable field has forbidden ownership: ${field.field_key}`);
      if (sensitivity === 'secret') throw new Error(`editable field cannot be SECRET: ${field.field_key}`);
      if (!SUPPORTED_TYPES.has(field.field_type)) throw new Error(`unsupported editable field type: ${field.field_key}`);
      if (field.answer === null || field.answer === undefined) throw new Error(`editable field has no answer: ${field.field_key}`);
      if (field.field_type === 'checkbox' && !(typeof field.answer === 'boolean' || Array.isArray(field.answer))) {
        throw new Error(`checkbox answer must be boolean or array: ${field.field_key}`);
      }
      if (field.field_type === 'radio' && typeof field.answer !== 'string') {
        throw new Error(`radio answer must be string: ${field.field_key}`);
      }
      writes.push({
        field_key: field.field_key,
        field_type: field.field_type,
        answer: field.answer,
      });
    } else {
      protectedFields.push(field.field_key);
    }
  }
  if (!writes.length) throw new Error('plan has no agent-editable fields');

  return {
    origin: parsedUrl.origin,
    writes,
    protectedFields,
  };
}

async function applyWrites(page, writes) {
  return page.evaluate((requestedWrites) => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const labelFor = (el) => {
      const labels = el.labels ? Array.from(el.labels).map((label) => clean(label.textContent)).filter(Boolean) : [];
      if (labels.length) return labels.join(' / ');
      const aria = clean(el.getAttribute('aria-label'));
      if (aria) return aria;
      const fieldset = el.closest('fieldset');
      const legend = fieldset ? clean(fieldset.querySelector('legend')?.textContent) : '';
      if (legend) return legend;
      return clean(el.getAttribute('name')) || clean(el.id) || 'Unnamed field';
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
      const rawKey = clean(el.getAttribute('name')) || clean(el.id) || `control-${index + 1}`;
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
    const optionIdentity = (el) => labelFor(el) || clean(el.value);
    const touched = [];
    const invalid = [];

    for (const write of requestedWrites) {
      const target = keyed.get(write.field_key);
      if (!target) throw new Error('UEX_PREFILL_FIELD_NOT_FOUND');

      if (Array.isArray(target)) {
        if (write.field_type === 'radio') {
          const wanted = String(write.answer);
          const match = target.find((el) => optionIdentity(el) === wanted || clean(el.value) === wanted);
          if (!match) throw new Error('UEX_PREFILL_OPTION_NOT_FOUND');
          for (const el of target) el.checked = el === match;
          match.dispatchEvent(event('input'));
          match.dispatchEvent(event('change'));
        } else if (write.field_type === 'checkbox') {
          const wanted = Array.isArray(write.answer) ? new Set(write.answer.map(String)) : null;
          if (!wanted) throw new Error('UEX_PREFILL_CHECKBOX_GROUP_REQUIRES_ARRAY');
          for (const el of target) {
            const identity = optionIdentity(el);
            const next = wanted.has(identity) || wanted.has(clean(el.value));
            if (el.checked !== next) {
              el.checked = next;
              el.dispatchEvent(event('input'));
              el.dispatchEvent(event('change'));
            }
          }
        } else {
          throw new Error('UEX_PREFILL_GROUP_TYPE_MISMATCH');
        }
      } else if (target instanceof HTMLSelectElement) {
        const wanted = String(write.answer);
        const option = Array.from(target.options).find((item) => clean(item.textContent) === wanted || item.value === wanted);
        if (!option) throw new Error('UEX_PREFILL_OPTION_NOT_FOUND');
        target.value = option.value;
        target.dispatchEvent(event('input'));
        target.dispatchEvent(event('change'));
      } else if (target instanceof HTMLInputElement && (target.type || '').toLowerCase() === 'checkbox') {
        if (typeof write.answer !== 'boolean') throw new Error('UEX_PREFILL_SINGLE_CHECKBOX_REQUIRES_BOOLEAN');
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

export async function prefillLocalForm({
  plan,
  profileDir,
  headless = true,
  channel = 'chromium',
  timeoutMs = 20_000,
  now = new Date(),
}) {
  const validated = validateLocalPrefillPlan(plan, { now });
  const dedicatedProfileDir = assertDedicatedProfileDir(profileDir);
  fs.mkdirSync(dedicatedProfileDir, { recursive: true, mode: 0o700 });

  const launchOptions = { headless, viewport: { width: 1440, height: 1000 } };
  if (channel !== 'chromium') launchOptions.channel = channel;

  const context = await chromium.launchPersistentContext(dedicatedProfileDir, launchOptions);
  try {
    await context.addInitScript({ content: PREFILL_ONLY_INIT_SCRIPT });
    const page = context.pages()[0] || (await context.newPage());
    await page.route('**/*', async (route) => {
      const request = route.request();
      let decision;
      try {
        if (normalizeOrigin(request.url()) !== validated.origin) {
          decision = { action: 'abort', reason: 'cross_origin_request_blocked' };
        } else {
          const isTopLevelNavigation = request.isNavigationRequest() && request.frame() === page.mainFrame();
          decision = networkDecision({
            method: request.method(),
            url: request.url(),
            isTopLevelNavigation,
            allowedOrigins: [validated.origin],
          });
        }
      } catch {
        decision = { action: 'abort', reason: 'invalid_request_url' };
      }
      if (decision.action === 'abort') await route.abort('blockedbyclient');
      else await route.continue();
    });

    await page.goto(plan.canonical_form_url, { waitUntil: 'domcontentloaded', timeout: timeoutMs });
    if (normalizeOrigin(page.url()) !== validated.origin) throw new Error('PREFILL_LOCAL final origin changed');

    const before = await extractNativeFormSchema(page);
    const actualFingerprint = formSchemaFingerprint({
      provider: plan.provider,
      canonicalFormUrl: plan.canonical_form_url,
      fields: before.fields,
    });
    if (actualFingerprint !== plan.form_fingerprint) throw new Error('FORM_FINGERPRINT_MISMATCH');

    const writeResult = await applyWrites(page, validated.writes);
    const after = await extractNativeFormSchema(page);
    const afterFingerprint = formSchemaFingerprint({
      provider: plan.provider,
      canonicalFormUrl: plan.canonical_form_url,
      fields: after.fields,
    });
    if (afterFingerprint !== actualFingerprint) throw new Error('FORM_STRUCTURE_CHANGED_DURING_PREFILL');

    return {
      mode: 'PREFILL_LOCAL_ONLY',
      application_id: plan.application_id,
      form_fingerprint: actualFingerprint,
      write_count: writeResult.touched.length,
      written_field_keys: writeResult.touched,
      invalid_field_keys: writeResult.invalid,
      protected_field_keys: validated.protectedFields,
      safety: {
        external_origins_allowed: false,
        same_origin_requests_only: true,
        submit_blocked: true,
        mutating_http_methods_blocked: true,
        cookies_read: false,
        storage_state_exported: false,
        protected_values_exported: false,
        answer_values_exported: false,
      },
    };
  } finally {
    await context.close();
  }
}
