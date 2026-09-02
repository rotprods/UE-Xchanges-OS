import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeGoogleFormQuestionRecords } from '../src/providers/provider-extractor.mjs';

test('google forms normalization returns value-free deterministic fields', () => {
  const fields = normalizeGoogleFormQuestionRecords([
    { label: 'Why do you want to join?', field_type: 'textarea', required: true, options: [], maxlength: 1200 },
    { label: 'Country', field_type: 'radio', required: true, options: ['Spain', 'Italy', 'Spain'] },
  ]);
  assert.deepEqual(fields[0], {
    field_key: 'google-form-q-001',
    label: 'Why do you want to join?',
    field_type: 'textarea',
    required: true,
    options: [],
    maxlength: 1200,
    ownership: 'unresolved',
    sensitivity: 'private',
    editable_by_agent: false,
  });
  assert.deepEqual(fields[1].options, ['Spain', 'Italy']);
  assert.equal(JSON.stringify(fields).includes('answer'), false);
  assert.equal(JSON.stringify(fields).includes('value'), false);
});

test('google forms normalization fails closed on malformed records', () => {
  assert.throws(() => normalizeGoogleFormQuestionRecords([null]), /GOOGLE_FORMS_RECORD_INVALID/);
});
