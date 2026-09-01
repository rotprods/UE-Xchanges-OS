import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';
import { extractNativeFormSchema } from '../src/dom-schema.mjs';
import { formSchemaFingerprint } from '../src/fingerprint.mjs';
import {
  createValidationExpectation,
  extractValidationSnapshot,
  validatePageAgainstExpectation,
} from '../src/validate-diff.mjs';

function fixtureHtml() {
  return `<!doctype html><html><head><title>Validate Fixture</title></head><body>
  <form id="application">
    <label for="email">Email address</label>
    <input id="email" name="email" type="email" required>
    <label for="motivation">Motivation</label>
    <textarea id="motivation" name="motivation" minlength="10" maxlength="250" pattern=".{10,}"></textarea>
    <label for="country">Country</label>
    <select id="country" name="country" required><option>Spain</option><option>Portugal</option></select>
    <label for="availability">Availability declaration</label>
    <input id="availability" name="availability" type="text" required>
  </form></body></html>`;
}

async function startServer() {
  const server = http.createServer((request, response) => {
    response.writeHead(200, {'content-type':'text/html; charset=utf-8'});
    response.end(fixtureHtml());
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('no fixture port');
  return {server, origin:`http://127.0.0.1:${address.port}`};
}

async function setValues(page, values) {
  await page.evaluate((payload) => {
    for (const [key, value] of Object.entries(payload)) {
      const el = document.querySelector(`[name="${CSS.escape(key)}"]`);
      if (!el) throw new Error('fixture field missing');
      if (el instanceof HTMLSelectElement) {
        const option = Array.from(el.options).find((item) => item.textContent.trim() === value || item.value === value);
        if (!option) throw new Error('fixture option missing');
        el.value = option.value;
      } else {
        el.value = value;
      }
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
    }
  }, values);
}

function buildPlan(url, structural) {
  const byKey = new Map(structural.fields.map((field) => [field.field_key, field]));
  const fields = [
    {...byKey.get('email'), answer:'candidate@example.com', ownership:'green_agent_factual', sensitivity:'private', editable_by_agent:true},
    {...byKey.get('motivation'), answer:'A real motivation answer', ownership:'yellow_agent_assisted_human_review', sensitivity:'private', editable_by_agent:true},
    {...byKey.get('country'), answer:'Spain', ownership:'green_agent_factual', sensitivity:'public', editable_by_agent:true},
    {...byKey.get('availability'), answer:'I can attend all project dates', ownership:'red_human_confirmation', sensitivity:'private', editable_by_agent:false},
  ];
  return {
    plan_id:'plan-validate', application_id:'app-validate', opportunity_id:'opp-validate',
    canonical_form_url:url, provider:'generic_html',
    form_fingerprint:formSchemaFingerprint({provider:'generic_html', canonicalFormUrl:url, fields:structural.fields}),
    fields,
    state:'human_approved',
  };
}

test('live validation reports matches/mismatches and rule drift without values', {timeout:60_000}, async () => {
  const fixture = await startServer();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-validate-smoke-'));
  let context;
  try {
    context = await chromium.launchPersistentContext(profileDir, {headless:true});
    const page = context.pages()[0] || await context.newPage();
    const url = `${fixture.origin}/form?private=QUERY-CANARY#secret`;
    await page.goto(url, {waitUntil:'domcontentloaded'});

    const structural = await extractNativeFormSchema(page);
    const validationFields = await extractValidationSnapshot(page);
    const expectation = createValidationExpectation({provider:'generic_html', canonicalFormUrl:url, fields:validationFields});
    const plan = buildPlan(url, structural);

    const values = {
      email:'candidate@example.com',
      motivation:'A real motivation answer',
      country:'Spain',
      availability:'I can attend all project dates',
    };
    await setValues(page, values);

    const passing = await validatePageAgainstExpectation({page, plan, expectation});
    assert.equal(passing.form_fingerprint_match, true);
    assert.equal(passing.validation_signature_match, true);
    assert.equal(passing.all_values_match, true);
    assert.equal(passing.all_fields_valid, true);
    assert.deepEqual(passing.schema_diff, {added_field_keys:[], removed_field_keys:[], changed_fields:[]});

    await setValues(page, {motivation:'WRONG-MOTIVATION-CANARY'});
    const mismatched = await validatePageAgainstExpectation({page, plan, expectation});
    assert.equal(mismatched.all_values_match, false);
    assert.deepEqual(
      mismatched.field_results.filter((item) => !item.value_match).map((item) => item.field_key),
      ['motivation'],
    );

    await page.evaluate(() => document.querySelector('[name="motivation"]').setAttribute('minlength', '80'));
    const ruleChanged = await validatePageAgainstExpectation({page, plan, expectation});
    assert.equal(ruleChanged.validation_signature_match, false);
    assert.deepEqual(ruleChanged.schema_diff.changed_fields, [
      {field_key:'motivation', changed_properties:['constraints.minlength']},
    ]);

    for (const report of [passing, mismatched, ruleChanged]) {
      const serialized = JSON.stringify(report);
      for (const canary of [
        'candidate@example.com',
        'A real motivation answer',
        'I can attend all project dates',
        'WRONG-MOTIVATION-CANARY',
        'QUERY-CANARY',
      ]) {
        assert.equal(serialized.includes(canary), false, `validation report leaked value: ${canary}`);
      }
      assert.equal(report.safety.answer_values_exported, false);
      assert.equal(report.safety.protected_values_exported, false);
    }
  } finally {
    if (context) await context.close();
    await new Promise((resolve) => fixture.server.close(resolve));
    fs.rmSync(profileDir, {recursive:true, force:true});
  }
});
