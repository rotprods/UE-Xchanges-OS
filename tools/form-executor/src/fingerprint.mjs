import crypto from 'node:crypto';

export function canonicalizeFormUrl(value) {
  if (typeof value !== 'string') throw new Error('form URL must be a string');
  const match = value.match(/^(https?):\/\/([^/?#]+)([^?#]*)(\?[^#]*)?(?:#.*)?$/i);
  if (!match) throw new Error('form URL must be absolute HTTP(S)');
  const scheme = match[1].toLowerCase();
  const netloc = match[2].toLowerCase();
  const path = match[3] || '/';
  const query = match[4] || '';
  return `${scheme}://${netloc}${path}${query}`;
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
