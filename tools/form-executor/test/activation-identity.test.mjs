import test from 'node:test';
import assert from 'node:assert/strict';
import { buildInspectIdentity } from '../src/inspect-identity.mjs';

const structuralFields = [
  {
    field_key: 'amount',
    label: 'Amount',
    field_type: 'number',
    required: true,
    options: [],
    maxlength: null,
  },
];

const validationFields = [
  {
    field_key: 'amount',
    label: 'Amount',
    field_type: 'number',
    required: true,
    options: [],
    constraints: {
      minlength: null,
      maxlength: null,
      pattern: null,
      min_value: '1',
      max_value: '10',
      step: '1',
      multiple: false,
      accept: [],
    },
  },
];

test('inspect identity is deterministic, query-sensitive and answer-free', () => {
  const first = buildInspectIdentity({
    provider: 'Generic_HTML',
    canonicalFormUrl: 'https://example.org/apply?call=2026#private',
    structuralFields,
    validationFields,
  });
  const second = buildInspectIdentity({
    provider: 'generic_html',
    canonicalFormUrl: 'https://example.org/apply?call=2026#other-fragment',
    structuralFields: structuralFields.map((field) => ({ ...field, answer: 'SECRET-ANSWER' })),
    validationFields,
  });

  assert.equal(first.provider, 'generic_html');
  assert.match(first.form_fingerprint, /^sha256:[0-9a-f]{64}$/);
  assert.match(first.validation_signature, /^sha256:[0-9a-f]{64}$/);
  assert.equal(first.form_fingerprint, second.form_fingerprint);
  assert.equal(first.validation_signature, second.validation_signature);
  assert.equal(JSON.stringify(first).includes('SECRET-ANSWER'), false);

  const otherQuery = buildInspectIdentity({
    provider: 'generic_html',
    canonicalFormUrl: 'https://example.org/apply?call=2027',
    structuralFields,
    validationFields,
  });
  assert.notEqual(first.form_fingerprint, otherQuery.form_fingerprint);
  assert.notEqual(first.validation_signature, otherQuery.validation_signature);
});

test('validation rule drift changes validation signature without changing structure fingerprint', () => {
  const first = buildInspectIdentity({
    provider: 'generic_html',
    canonicalFormUrl: 'https://example.org/apply',
    structuralFields,
    validationFields,
  });
  const changed = buildInspectIdentity({
    provider: 'generic_html',
    canonicalFormUrl: 'https://example.org/apply',
    structuralFields,
    validationFields: validationFields.map((field) => ({
      ...field,
      constraints: { ...field.constraints, min_value: '2' },
    })),
  });
  assert.equal(first.form_fingerprint, changed.form_fingerprint);
  assert.notEqual(first.validation_signature, changed.validation_signature);
});
