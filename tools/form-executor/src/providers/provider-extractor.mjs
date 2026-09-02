import { extractNativeFormSchema } from '../dom-schema.mjs';

function clean(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

const GOOGLE_FORM_TYPE = new Map([
  [0, 'text'],
  [1, 'textarea'],
  [2, 'radio'],
  [3, 'select'],
  [4, 'checkbox'],
  [5, 'radio'],
  [9, 'date'],
  [10, 'text'],
]);

export function normalizeGoogleFormQuestionRecords(records) {
  if (!Array.isArray(records)) throw new Error('GOOGLE_FORMS_RECORDS_INVALID');
  return records.map((record, index) => {
    if (!record || typeof record !== 'object' || Array.isArray(record)) throw new Error('GOOGLE_FORMS_RECORD_INVALID');
    const label = clean(record.label) || `Question ${index + 1}`;
    const type = ['text', 'textarea', 'radio', 'checkbox', 'select', 'date', 'file', 'custom'].includes(record.field_type)
      ? record.field_type
      : 'custom';
    const options = Array.isArray(record.options)
      ? [...new Set(record.options.map(clean).filter(Boolean))]
      : [];
    return {
      field_key: `google-form-q-${String(index + 1).padStart(3, '0')}`,
      label,
      field_type: type,
      required: Boolean(record.required),
      options,
      maxlength: Number.isInteger(record.maxlength) && record.maxlength > 0 ? record.maxlength : null,
      ownership: 'unresolved',
      sensitivity: 'private',
      editable_by_agent: false,
    };
  });
}

export function recordsFromGooglePublicLoadData(data) {
  const items = data?.[1]?.[1];
  if (!Array.isArray(items)) return [];
  const records = [];
  for (const item of items) {
    if (!Array.isArray(item) || typeof item[1] !== 'string' || !Number.isInteger(item[3])) continue;
    const entry = Array.isArray(item[4]) ? item[4][0] : null;
    const optionRows = Array.isArray(entry?.[1]) ? entry[1] : [];
    const options = optionRows
      .map((option) => Array.isArray(option) ? clean(option[0]) : '')
      .filter(Boolean);
    records.push({
      label: clean(item[1]),
      field_type: GOOGLE_FORM_TYPE.get(item[3]) || 'custom',
      required: entry?.[2] === 1,
      options,
      maxlength: null,
    });
  }
  return records;
}

export async function extractGoogleFormsSchema(page) {
  const raw = await page.evaluate(() => {
    const cleanText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const safeUrl = (value) => {
      const parsed = new URL(value, location.href);
      return `${parsed.origin}${parsed.pathname}`;
    };
    const textFor = (el) => cleanText(el?.getAttribute?.('aria-label')) || cleanText(el?.textContent);
    const roots = Array.from(document.querySelectorAll('[role="listitem"]')).filter((item) => {
      const heading = item.querySelector('[role="heading"], [aria-level]');
      if (!heading) return false;
      const text = textFor(heading);
      return Boolean(text) && !/^(email|your email)$/i.test(text);
    });
    const questions = roots.map((root) => {
      const heading = root.querySelector('[role="heading"], [aria-level]');
      const label = textFor(heading).replace(/\s*\*\s*$/, '');
      const required = Boolean(
        root.querySelector('[aria-label*="Required" i], [aria-label*="Obligator" i], [aria-label*="Requerid" i]')
        || /\*\s*$/.test(textFor(heading)),
      );
      const radios = Array.from(root.querySelectorAll('[role="radio"]'));
      const checks = Array.from(root.querySelectorAll('[role="checkbox"]'));
      const combo = root.querySelector('[role="combobox"], select');
      const textarea = root.querySelector('textarea');
      const textInput = root.querySelector('input:not([type="hidden"]):not([type="radio"]):not([type="checkbox"]):not([type="file"]), [role="textbox"]');
      const file = root.querySelector('input[type="file"], [aria-label*="file" i], [aria-label*="archivo" i]');
      let fieldType = 'custom';
      let options = [];
      let maxlength = null;
      if (radios.length) {
        fieldType = 'radio';
        options = radios.map(textFor).filter(Boolean);
      } else if (checks.length) {
        fieldType = 'checkbox';
        options = checks.map(textFor).filter(Boolean);
      } else if (combo) {
        fieldType = 'select';
        options = Array.from(root.querySelectorAll('[role="option"], option')).map(textFor).filter(Boolean);
      } else if (textarea) {
        fieldType = 'textarea';
        const rawMax = textarea.getAttribute('maxlength');
        const parsed = rawMax === null ? null : Number(rawMax);
        maxlength = Number.isInteger(parsed) && parsed > 0 ? parsed : null;
      } else if (file) {
        fieldType = 'file';
      } else if (textInput) {
        fieldType = 'text';
        const rawMax = textInput.getAttribute?.('maxlength');
        const parsed = rawMax == null ? null : Number(rawMax);
        maxlength = Number.isInteger(parsed) && parsed > 0 ? parsed : null;
      }
      return { label, field_type: fieldType, required, options, maxlength };
    });

    let publicLoadData = null;
    if (questions.length === 0) {
      const script = Array.from(document.scripts).map((node) => node.textContent || '').find((text) => text.includes('FB_PUBLIC_LOAD_DATA_'));
      if (script) {
        const marker = 'FB_PUBLIC_LOAD_DATA_';
        const equals = script.indexOf('=', script.indexOf(marker));
        const end = script.lastIndexOf(';');
        if (equals !== -1 && end > equals) {
          try { publicLoadData = JSON.parse(script.slice(equals + 1, end).trim()); }
          catch { publicLoadData = null; }
        }
      }
    }

    const submitControls = Array.from(document.querySelectorAll('[role="button"], button, input[type="submit"]'))
      .map((el, index) => ({ index, label: textFor(el), disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true') }))
      .filter((item) => /submit|send|enviar|siguiente|next/i.test(item.label));
    return {
      page: { url: safeUrl(location.href), title: document.title, origin: location.origin },
      questions,
      public_load_data: publicLoadData,
      submit_controls: submitControls,
    };
  });
  let records = raw.questions;
  if (records.length === 0 && raw.public_load_data) records = recordsFromGooglePublicLoadData(raw.public_load_data);
  const fields = normalizeGoogleFormQuestionRecords(records);
  return {
    schema_version: '0.2.1',
    page: raw.page,
    forms: [{ index: 0, id: null, name: null, method: 'PROVIDER_MANAGED', action: raw.page.url }],
    fields,
    submit_controls: raw.submit_controls,
    unsupported_custom_control_count: fields.filter((field) => field.field_type === 'custom').length,
    extraction_source: raw.questions.length > 0 ? 'DOM_ARIA' : raw.public_load_data ? 'FB_PUBLIC_LOAD_DATA' : 'NONE',
  };
}

export async function extractProviderFormSchema(page, provider = 'generic_html') {
  const normalized = String(provider || '').trim().toLowerCase();
  if (normalized === 'google_forms') return extractGoogleFormsSchema(page);
  if (normalized === 'generic_html') return extractNativeFormSchema(page);
  throw new Error('FORM_PROVIDER_EXTRACTOR_NOT_CERTIFIED');
}
