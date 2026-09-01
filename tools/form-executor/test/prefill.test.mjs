import test from 'node:test';
import assert from 'node:assert/strict';
import { assertLoopbackUrl, validateLocalPrefillPlan } from '../src/prefill.mjs';

const future = new Date(Date.now() + 60_000).toISOString();

function plan(overrides = {}) {
  return {
    plan_id: 'plan-1',
    application_id: 'app-1',
    opportunity_id: 'opp-1',
    canonical_form_url: 'http://127.0.0.1:3000/form',
    provider: 'generic_html',
    form_fingerprint: 'sha256:fp',
    state: 'prefill_ready',
    expires_at: future,
    attachments: [],
    fields: [
      {
        field_key: 'email',
        field_type: 'email',
        answer: 'candidate@example.com',
        ownership: 'green_agent_factual',
        sensitivity: 'private',
        editable_by_agent: true,
      },
      {
        field_key: 'availability',
        field_type: 'text',
        answer: 'Human-owned value',
        ownership: 'red_human_confirmation',
        sensitivity: 'private',
        editable_by_agent: false,
      },
    ],
    ...overrides,
  };
}

test('loopback-only development mode rejects external origins', () => {
  assert.equal(assertLoopbackUrl('http://127.0.0.1:3000/form').hostname, '127.0.0.1');
  assert.equal(assertLoopbackUrl('http://localhost:3000/form').hostname, 'localhost');
  assert.throws(() => assertLoopbackUrl('https://forms.google.com/form'), /rejects non-loopback/);
});

test('validated plan exposes only compiler-approved agent writes', () => {
  const validated = validateLocalPrefillPlan(plan());
  assert.equal(validated.writes.length, 1);
  assert.equal(validated.writes[0].field_key, 'email');
  assert.deepEqual(validated.protectedFields, ['availability']);
});

test('editable RED/BLACK/UNRESOLVED or SECRET fields are rejected', () => {
  for (const [ownership, sensitivity] of [
    ['red_human_confirmation', 'private'],
    ['black_secret_or_never_model', 'secret'],
    ['unresolved', 'private'],
  ]) {
    const bad = plan({
      fields: [{
        field_key: 'danger',
        field_type: 'text',
        answer: 'x',
        ownership,
        sensitivity,
        editable_by_agent: true,
      }],
    });
    assert.throws(() => validateLocalPrefillPlan(bad), /forbidden ownership|cannot be SECRET/);
  }
});

test('files and attachments remain outside PREFILL_LOCAL', () => {
  assert.throws(() => validateLocalPrefillPlan(plan({ attachments: ['drive:file'] })), /attachments are not supported/);
  const fileField = plan({
    fields: [{
      field_key: 'cv',
      field_type: 'file',
      answer: 'drive:file',
      ownership: 'green_agent_factual',
      sensitivity: 'private',
      editable_by_agent: true,
    }],
  });
  assert.throws(() => validateLocalPrefillPlan(fileField), /unsupported editable field type/);
});

test('expired and non-prefill-ready plans are rejected', () => {
  assert.throws(() => validateLocalPrefillPlan(plan({ expires_at: new Date(Date.now() - 1_000).toISOString() })), /expired/);
  assert.throws(() => validateLocalPrefillPlan(plan({ state: 'human_approved' })), /not prefill-ready/);
});

test('checkbox and radio answer shapes are constrained', () => {
  const badCheckbox = plan({ fields: [{
    field_key: 'skills', field_type: 'checkbox', answer: 'Video', ownership: 'yellow_agent_assisted_human_review', sensitivity: 'private', editable_by_agent: true,
  }] });
  assert.throws(() => validateLocalPrefillPlan(badCheckbox), /checkbox answer must be boolean or array/);

  const badRadio = plan({ fields: [{
    field_key: 'role', field_type: 'radio', answer: ['Participant'], ownership: 'green_agent_factual', sensitivity: 'private', editable_by_agent: true,
  }] });
  assert.throws(() => validateLocalPrefillPlan(badRadio), /radio answer must be string/);
});
