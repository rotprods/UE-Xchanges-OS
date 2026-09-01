import test from 'node:test';
import assert from 'node:assert/strict';
import { createValidationExpectation, diffValidationSnapshots } from '../src/validate-diff.mjs';
import { validationSignature } from '../src/validation-signature.mjs';

const baseFields = [
  {
    field_key: 'motivation',
    label: 'Motivation',
    field_type: 'textarea',
    required: true,
    options: [],
    constraints: {
      minlength: 20,
      maxlength: 250,
      pattern: null,
      min_value: null,
      max_value: null,
      step: null,
      multiple: false,
      accept: [],
    },
  },
  {
    field_key: 'country',
    label: 'Country',
    field_type: 'select',
    required: true,
    options: ['Spain', 'Portugal'],
    constraints: {
      minlength: null,
      maxlength: null,
      pattern: null,
      min_value: null,
      max_value: null,
      step: null,
      multiple: false,
      accept: [],
    },
  },
];

test('validation expectation signs exact validation snapshot', () => {
  const expectation = createValidationExpectation({
    provider: 'generic_html',
    canonicalFormUrl: 'https://example.org/form?call=2026#private',
    fields: baseFields,
  });
  assert.equal(expectation.signature, validationSignature({
    provider: 'generic_html',
    canonicalFormUrl: 'https://example.org/form?call=2026#private',
    fields: baseFields,
  }));
});

test('diff reports field names and changed property names, not values', () => {
  const changed = structuredClone(baseFields);
  changed[0].constraints.minlength = 50;
  changed[1].options = ['Spain', 'Portugal', 'Italy'];
  changed.push({
    field_key: 'new_field', label: 'New', field_type: 'text', required: false, options: [],
    constraints: {minlength:null, maxlength:null, pattern:null, min_value:null, max_value:null, step:null, multiple:false, accept:[]},
  });
  const diff = diffValidationSnapshots(baseFields, changed);
  assert.deepEqual(diff.added_field_keys, ['new_field']);
  assert.deepEqual(diff.removed_field_keys, []);
  assert.deepEqual(diff.changed_fields, [
    {field_key:'motivation', changed_properties:['constraints.minlength']},
    {field_key:'country', changed_properties:['options']},
  ]);
  const serialized = JSON.stringify(diff);
  assert.equal(serialized.includes('50'), false);
  assert.equal(serialized.includes('Italy'), false);
});

test('validation signature changes for pattern/min/max/multiple/accept changes', () => {
  const first = validationSignature({provider:'generic_html', canonicalFormUrl:'https://example.org/form', fields:baseFields});
  const changed = structuredClone(baseFields);
  changed[0].constraints.pattern = '.{50,}';
  changed[0].constraints.min_value = '1';
  changed[0].constraints.max_value = '9';
  changed[0].constraints.step = '2';
  changed[0].constraints.multiple = true;
  changed[0].constraints.accept = ['image/png'];
  const second = validationSignature({provider:'generic_html', canonicalFormUrl:'https://example.org/form', fields:changed});
  assert.notEqual(first, second);
});
