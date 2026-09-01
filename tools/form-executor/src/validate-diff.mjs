import { extractNativeFormSchema } from './dom-schema.mjs';
import { formSchemaFingerprint } from './fingerprint.mjs';
import { assertLoopbackUrl } from './prefill-policy.mjs';
import { validationSignature } from './validation-signature.mjs';

function clean(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

export async function extractValidationSnapshot(page) {
  return page.evaluate(() => {
    const cleanText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const labelFor = (el) => {
      const labels = el.labels ? Array.from(el.labels).map((label) => cleanText(label.textContent)).filter(Boolean) : [];
      if (labels.length) return labels.join(' / ');
      const aria = cleanText(el.getAttribute('aria-label'));
      if (aria) return aria;
      const fieldset = el.closest('fieldset');
      const legend = fieldset ? cleanText(fieldset.querySelector('legend')?.textContent) : '';
      if (legend) return legend;
      const placeholder = cleanText(el.getAttribute('placeholder'));
      if (placeholder) return placeholder;
      return cleanText(el.getAttribute('name')) || cleanText(el.id) || 'Unnamed field';
    };
    const controls = Array.from(document.querySelectorAll('input, textarea, select')).filter((el) => {
      if (el instanceof HTMLInputElement) {
        const type = (el.getAttribute('type') || 'text').toLowerCase();
        return !['hidden', 'button', 'submit', 'reset', 'image'].includes(type);
      }
      return true;
    });
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
    const attrInt = (el, name) => {
      const raw = el.getAttribute(name);
      if (raw === null || raw === '') return null;
      const value = Number(raw);
      return Number.isInteger(value) && value >= 0 ? value : null;
    };
    const attrText = (el, name) => {
      const raw = el.getAttribute(name);
      return raw === null || raw === '' ? null : raw;
    };
    const constraintsFor = (el) => ({
      minlength: attrInt(el, 'minlength'),
      maxlength: attrInt(el, 'maxlength'),
      pattern: attrText(el, 'pattern'),
      min_value: attrText(el, 'min'),
      max_value: attrText(el, 'max'),
      step: attrText(el, 'step'),
      multiple: Boolean(el.multiple),
      accept: el instanceof HTMLInputElement && (el.getAttribute('type') || '').toLowerCase() === 'file'
        ? cleanText(el.getAttribute('accept')).split(',').map((item) => item.trim()).filter(Boolean)
        : [],
    });

    const fields = [];
    const groupIndex = new Map();
    const used = new Set();
    for (let index = 0; index < controls.length; index += 1) {
      const el = controls[index];
      const fieldType = mapType(el);
      const rawKey = cleanText(el.getAttribute('name')) || cleanText(el.id) || `control-${index + 1}`;
      const groupable = fieldType === 'radio' || fieldType === 'checkbox';
      const groupKey = `${fieldType}:${rawKey}`;
      const required = Boolean(el.required || el.getAttribute('aria-required') === 'true');
      const optionLabel = labelFor(el);
      let options = [];
      if (el instanceof HTMLSelectElement) {
        options = Array.from(el.options).map((option) => cleanText(option.textContent)).filter(Boolean);
      } else if (groupable && optionLabel) {
        options = [optionLabel];
      }

      if (groupable && groupIndex.has(groupKey)) {
        const existing = fields[groupIndex.get(groupKey)];
        existing.required = existing.required || required;
        existing.options = Array.from(new Set([...existing.options, ...options]));
        continue;
      }

      let fieldKey = rawKey;
      if (!groupable) {
        if (used.has(fieldKey)) fieldKey = `${fieldKey}#${index + 1}`;
        used.add(fieldKey);
      }
      const field = {
        field_key: fieldKey,
        label: labelFor(el),
        field_type: fieldType,
        required,
        options,
        constraints: constraintsFor(el),
      };
      fields.push(field);
      if (groupable) groupIndex.set(groupKey, fields.length - 1);
    }
    return fields;
  });
}

function stableComparable(field) {
  return {
    label: field.label,
    field_type: field.field_type,
    required: Boolean(field.required),
    options: Array.isArray(field.options) ? field.options : [],
    constraints: {
      minlength: field.constraints?.minlength ?? null,
      maxlength: field.constraints?.maxlength ?? null,
      pattern: field.constraints?.pattern ?? null,
      min_value: field.constraints?.min_value ?? null,
      max_value: field.constraints?.max_value ?? null,
      step: field.constraints?.step ?? null,
      multiple: Boolean(field.constraints?.multiple),
      accept: Array.isArray(field.constraints?.accept) ? field.constraints.accept : [],
    },
  };
}

export function diffValidationSnapshots(expectedFields, actualFields) {
  const expected = new Map(expectedFields.map((field) => [field.field_key, field]));
  const actual = new Map(actualFields.map((field) => [field.field_key, field]));
  const added_field_keys = [...actual.keys()].filter((key) => !expected.has(key)).sort();
  const removed_field_keys = [...expected.keys()].filter((key) => !actual.has(key)).sort();
  const changed_fields = [];

  for (const [key, expectedField] of expected) {
    const actualField = actual.get(key);
    if (!actualField) continue;
    const left = stableComparable(expectedField);
    const right = stableComparable(actualField);
    const changed = [];
    for (const property of ['label', 'field_type', 'required', 'options']) {
      if (JSON.stringify(left[property]) !== JSON.stringify(right[property])) changed.push(property);
    }
    for (const property of ['minlength', 'maxlength', 'pattern', 'min_value', 'max_value', 'step', 'multiple', 'accept']) {
      if (JSON.stringify(left.constraints[property]) !== JSON.stringify(right.constraints[property])) changed.push(`constraints.${property}`);
    }
    if (changed.length) changed_fields.push({ field_key: key, changed_properties: changed });
  }
  return { added_field_keys, removed_field_keys, changed_fields };
}

async function compareCurrentValues(page, plan) {
  return page.evaluate((planFields) => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const canonicalize = (fieldType, value) => {
      const nfc = (text) => String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n').normalize('NFC');
      const decimal = (input) => {
        if (typeof input === 'boolean') throw new Error('boolean is not a canonical number');
        let raw;
        if (typeof input === 'number') {
          if (!Number.isFinite(input)) throw new Error('number answers must be finite');
          raw = String(input);
        } else if (typeof input === 'string') raw = input.trim();
        else throw new Error('number answer must be numeric or decimal string');
        const match = raw.match(/^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/);
        if (!match) throw new Error('number answer is not a valid finite decimal');
        const negative = match[1] === '-';
        const integer = match[2];
        const fraction = match[3] || '';
        const exponent = Number(match[4] || '0') - fraction.length;
        if (!Number.isSafeInteger(exponent)) throw new Error('number exponent is outside canonical range');
        let digits = `${integer}${fraction}`.replace(/^0+/, '');
        if (!digits) return '0';
        let rendered;
        if (exponent >= 0) rendered = digits + '0'.repeat(exponent);
        else {
          const point = digits.length + exponent;
          rendered = point <= 0 ? `0.${'0'.repeat(-point)}${digits}` : `${digits.slice(0, point)}.${digits.slice(point)}`;
          rendered = rendered.replace(/0+$/, '').replace(/\.$/, '');
        }
        rendered = rendered.replace(/^0+(?=\d)/, '');
        return negative && rendered !== '0' ? `-${rendered}` : rendered;
      };
      const isoDate = (input) => {
        if (typeof input !== 'string') throw new Error('browser date answer must be ISO string');
        const raw = input.trim();
        if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) throw new Error('date answer must use ISO YYYY-MM-DD');
        const parsed = new Date(`${raw}T00:00:00Z`);
        if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== raw) throw new Error('date answer must be real');
        return raw;
      };
      if (value === null || value === undefined) return null;
      if (fieldType === 'text' || fieldType === 'textarea') {
        if (typeof value !== 'string') throw new Error('text-like answers must be strings');
        return nfc(value);
      }
      if (fieldType === 'email') {
        if (typeof value !== 'string') throw new Error('email answers must be strings');
        return nfc(value).trim();
      }
      if (fieldType === 'number') return decimal(value);
      if (fieldType === 'date') return isoDate(value);
      if (fieldType === 'select' || fieldType === 'radio') {
        if (typeof value !== 'string') throw new Error('choice answers must be strings');
        const normalized = nfc(value).trim();
        if (!normalized) throw new Error('choice answer must be non-empty');
        return normalized;
      }
      if (fieldType === 'checkbox') {
        if (typeof value === 'boolean') return value;
        if (!Array.isArray(value)) throw new Error('checkbox answer must be boolean or array');
        const normalized = value.map((item) => {
          if (typeof item !== 'string') throw new Error('checkbox options must be strings');
          const option = nfc(item).trim();
          if (!option) throw new Error('checkbox option must be non-empty');
          return option;
        });
        return [...new Set(normalized)].sort();
      }
      if (fieldType === 'consent') {
        if (typeof value !== 'boolean') throw new Error('consent answer must be boolean');
        return value;
      }
      if (fieldType === 'file' || fieldType === 'unknown') throw new Error('non-model value type');
      throw new Error('unsupported field type');
    };
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
    const optionIdentity = (el) => labelFor(el) || clean(el.value);

    const results = [];
    for (const field of planFields) {
      const target = keyed.get(field.field_key);
      if (!target) {
        results.push({ field_key: field.field_key, present: false, value_match: false, valid: false });
        continue;
      }
      let actual;
      let valid;
      if (Array.isArray(target)) {
        if (field.field_type === 'radio') {
          const selected = target.find((el) => el.checked);
          actual = selected ? optionIdentity(selected) : null;
        } else if (field.field_type === 'checkbox') {
          actual = target.filter((el) => el.checked).map(optionIdentity);
        } else actual = null;
        valid = target.some((el) => typeof el.checkValidity !== 'function' || el.checkValidity());
      } else if (target instanceof HTMLInputElement && (target.type || '').toLowerCase() === 'checkbox') {
        actual = target.checked;
        valid = target.checkValidity();
      } else if (target instanceof HTMLSelectElement) {
        actual = clean(target.selectedOptions[0]?.textContent) || target.value;
        valid = target.checkValidity();
      } else {
        actual = target.value;
        valid = typeof target.checkValidity !== 'function' || target.checkValidity();
      }

      let valueMatch = false;
      try {
        valueMatch = JSON.stringify(canonicalize(field.field_type, actual)) === JSON.stringify(canonicalize(field.field_type, field.answer));
      } catch {
        valueMatch = false;
      }
      results.push({
        field_key: field.field_key,
        present: true,
        value_match: valueMatch,
        valid: Boolean(valid),
        ownership: field.ownership,
        editable_by_agent: field.editable_by_agent === true,
      });
    }
    return results;
  }, plan.fields);
}

export async function validatePageAgainstExpectation({ page, plan, expectation }) {
  const parsed = assertLoopbackUrl(plan.canonical_form_url);
  if (new URL(page.url()).origin !== parsed.origin) throw new Error('validation page origin does not match plan');
  if (!expectation || typeof expectation !== 'object') throw new Error('validation expectation is required');
  if (expectation.provider !== plan.provider || expectation.canonical_form_url !== plan.canonical_form_url) {
    throw new Error('validation expectation identity does not match plan');
  }

  const structural = await extractNativeFormSchema(page);
  const actualFingerprint = formSchemaFingerprint({
    provider: plan.provider,
    canonicalFormUrl: plan.canonical_form_url,
    fields: structural.fields,
  });
  const actualValidationFields = await extractValidationSnapshot(page);
  const actualValidationSignature = validationSignature({
    provider: plan.provider,
    canonicalFormUrl: plan.canonical_form_url,
    fields: actualValidationFields,
  });
  const diff = diffValidationSnapshots(expectation.fields, actualValidationFields);
  const fieldResults = await compareCurrentValues(page, plan);

  return {
    mode: 'VALIDATE_AND_DIFF_LOCAL_ONLY',
    application_id: plan.application_id,
    form_fingerprint_match: actualFingerprint === plan.form_fingerprint,
    validation_signature_match: actualValidationSignature === expectation.signature,
    schema_diff: diff,
    field_results: fieldResults,
    all_values_match: fieldResults.every((item) => item.present && item.value_match),
    all_fields_valid: fieldResults.every((item) => item.present && item.valid),
    safety: {
      answer_values_exported: false,
      protected_values_exported: false,
      cookies_read: false,
      storage_state_exported: false,
    },
  };
}

export function createValidationExpectation({ provider, canonicalFormUrl, fields }) {
  return {
    provider,
    canonical_form_url: canonicalFormUrl,
    fields,
    signature: validationSignature({ provider, canonicalFormUrl, fields }),
  };
}
