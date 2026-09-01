import crypto from 'node:crypto';

export function canonicalizeFormUrl(value) {
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('form URL must be absolute HTTP(S)');
  }
  parsed.hash = '';
  parsed.username = '';
  parsed.password = '';
  return parsed.href;
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export function formSchemaFingerprint({ provider, canonicalFormUrl, fields }) {
  if (typeof provider !== 'string' || !provider.trim()) throw new Error('provider must be non-empty');
  if (!Array.isArray(fields)) throw new Error('fields must be an array');
  const payload = {
    provider: provider.trim().toLowerCase(),
    url: canonicalizeFormUrl(canonicalFormUrl),
    fields: fields.map((field) => ({
      field_key: field.field_key,
      label: field.label,
      field_type: field.field_type,
      required: Boolean(field.required),
      options: Array.isArray(field.options) ? field.options : [],
      maxlength: field.maxlength ?? null,
    })),
  };
  return `sha256:${crypto.createHash('sha256').update(stableJson(payload), 'utf8').digest('hex')}`;
}
