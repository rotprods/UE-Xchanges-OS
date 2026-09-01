import crypto from 'node:crypto';
import { canonicalizeFormUrl } from './fingerprint.mjs';

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export function validationSignature({ provider, canonicalFormUrl, fields }) {
  if (typeof provider !== 'string' || !provider.trim()) throw new Error('provider must be non-empty');
  if (!Array.isArray(fields)) throw new Error('validation fields must be an array');
  const keys = fields.map((field) => field.field_key);
  if (new Set(keys).size !== keys.length) throw new Error('validation field keys must be unique');
  const payload = {
    provider: provider.trim().toLowerCase(),
    url: canonicalizeFormUrl(canonicalFormUrl),
    fields: fields.map((field) => ({
      field_key: field.field_key,
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
    })),
  };
  return `sha256:${crypto.createHash('sha256').update(stableJson(payload), 'utf8').digest('hex')}`;
}
