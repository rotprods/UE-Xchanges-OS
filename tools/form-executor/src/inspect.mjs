import fs from 'node:fs';
import { chromium } from 'playwright';
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

async function extractNativeFormSchema(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const safeUrl = (value) => {
      const parsed = new URL(value, location.href);
      return `${parsed.origin}${parsed.pathname}`;
    };

    const labelFor = (el) => {
      const labels = el.labels ? Array.from(el.labels).map((label) => clean(label.textContent)).filter(Boolean) : [];
      if (labels.length) return labels.join(' / ');
      const aria = clean(el.getAttribute('aria-label'));
      if (aria) return aria;
      const fieldset = el.closest('fieldset');
      const legend = fieldset ? clean(fieldset.querySelector('legend')?.textContent) : '';
      if (legend) return legend;
      const placeholder = clean(el.getAttribute('placeholder'));
      if (placeholder) return placeholder;
      return clean(el.getAttribute('name')) || clean(el.id) || 'Unnamed field';
    };

    const controls = Array.from(document.querySelectorAll('input, textarea, select')).filter((el) => {
      if (el instanceof HTMLInputElement) {
        const type = (el.getAttribute('type') || 'text').toLowerCase();
        return !['hidden', 'button', 'submit', 'reset', 'image'].includes(type);
      }
      return true;
    });

    const fields = [];
    const groupIndex = new Map();

    const mapType = (el) => {
      if (el instanceof HTMLTextAreaElement) return 'textarea';
      if (el instanceof HTMLSelectElement) return 'select';
      const type = (el.getAttribute('type') || 'text').toLowerCase();
      if (type === 'email') return 'email';
      if (type === 'number' || type === 'range') return 'number';
      if (type === 'date' || type === 'datetime-local' || type === 'month' || type === 'week') return 'date';
      if (type === 'radio') return 'radio';
      if (type === 'checkbox') return 'checkbox';
      if (type === 'file') return 'file';
      return 'text';
    };

    for (let index = 0; index < controls.length; index += 1) {
      const el = controls[index];
      const fieldType = mapType(el);
      const rawKey = clean(el.getAttribute('name')) || clean(el.id) || `control-${index + 1}`;
      const isGroupable = fieldType === 'radio' || fieldType === 'checkbox';
      const groupKey = `${fieldType}:${rawKey}`;
      const optionLabel = labelFor(el);
      const required = Boolean(el.required || el.getAttribute('aria-required') === 'true');
      const maxRaw = el.getAttribute('maxlength');
      const maxParsed = maxRaw === null ? null : Number(maxRaw);
      const maxlength = Number.isInteger(maxParsed) && maxParsed > 0 ? maxParsed : null;
      const isPassword = el instanceof HTMLInputElement && (el.getAttribute('type') || '').toLowerCase() === 'password';
      const autocomplete = clean(el.getAttribute('autocomplete')).toLowerCase();
      const secretLike = isPassword || autocomplete === 'one-time-code';

      let options = [];
      if (el instanceof HTMLSelectElement) {
        options = Array.from(el.options).map((option) => clean(option.textContent)).filter(Boolean);
      } else if (isGroupable) {
        options = optionLabel ? [optionLabel] : [];
      }

      if (isGroupable && groupIndex.has(groupKey)) {
        const existing = fields[groupIndex.get(groupKey)];
        existing.required = existing.required || required;
        existing.options = Array.from(new Set([...existing.options, ...options]));
        if (existing.label === 'Unnamed field' && optionLabel) existing.label = optionLabel;
        continue;
      }

      let fieldKey = rawKey;
      if (!isGroupable) {
        const used = new Set(fields.map((field) => field.field_key));
        if (used.has(fieldKey)) fieldKey = `${fieldKey}#${index + 1}`;
      }

      const field = {
        field_key: fieldKey,
        label: labelFor(el),
        field_type: fieldType,
        required,
        options,
        maxlength,
        ownership: secretLike ? 'black_secret_or_never_model' : 'unresolved',
        sensitivity: secretLike ? 'secret' : 'private',
        editable_by_agent: false,
      };
      fields.push(field);
      if (isGroupable) groupIndex.set(groupKey, fields.length - 1);
    }

    const forms = Array.from(document.forms).map((form, index) => ({
      index,
      id: clean(form.id) || null,
      name: clean(form.getAttribute('name')) || null,
      method: clean(form.getAttribute('method') || 'get').toUpperCase(),
      action: safeUrl(form.getAttribute('action') || location.href),
    }));

    const submitControls = Array.from(document.querySelectorAll('button[type="submit"], input[type="submit"], button:not([type])')).map((el, index) => ({
      index,
      label: clean(el.textContent) || clean(el.getAttribute('value')) || clean(el.getAttribute('aria-label')) || 'Submit control',
      disabled: Boolean(el.disabled),
    }));

    const customControls = Array.from(document.querySelectorAll('[role="combobox"], [role="textbox"], [contenteditable="true"]')).filter(
      (el) => !(el instanceof HTMLInputElement) && !(el instanceof HTMLTextAreaElement) && !(el instanceof HTMLSelectElement),
    );

    return {
      schema_version: '0.1.0',
      mode: 'INSPECT_ONLY',
      page: {
        url: safeUrl(location.href),
        title: document.title,
        origin: location.origin,
      },
      forms,
      fields,
      submit_controls: submitControls,
      unsupported_custom_control_count: customControls.length,
      safety: {
        form_values_read: false,
        url_query_material_exported: false,
        cookies_read: false,
        storage_state_exported: false,
        mutating_http_methods_blocked: true,
        submit_events_blocked: true,
      },
    };
  });
}

export async function inspectForm({
  url,
  profileDir,
  allowedOrigins,
  headless = false,
  channel = 'chrome',
  timeoutMs = 20_000,
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
    const result = await extractNativeFormSchema(page);
    result.allowed_origins = normalizedOrigins;
    result.profile_mode = 'dedicated_persistent';
    result.browser_channel = channel;
    return result;
  } finally {
    await context.close();
  }
}
