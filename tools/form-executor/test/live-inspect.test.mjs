import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { inspectForm } from '../src/inspect.mjs';


function fixtureHtml() {
  return `<!doctype html>
<html>
<head><title>UEX Fixture Form</title></head>
<body>
  <form id="application" method="post" action="/submit?token=ACTION-SECRET">
    <label for="email">Email address</label>
    <input id="email" name="email" type="email" required value="SECRET-IN-FIELD">

    <label for="motivation">Motivation</label>
    <textarea id="motivation" name="motivation" maxlength="250" required>PRIVATE-MOTIVATION</textarea>

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

    <label for="password">Portal password</label>
    <input id="password" name="password" type="password" value="PASSWORD-SECRET">

    <label for="otp">One-time code</label>
    <input id="otp" name="otp" type="text" autocomplete="one-time-code" value="123456">

    <div role="combobox" aria-label="Custom widget">Unsupported custom widget</div>
    <button type="submit">Send application</button>
  </form>
  <script>
    fetch('/telemetry', {method: 'POST', body: 'SHOULD-NOT-REACH-SERVER'}).catch(() => {});
    queueMicrotask(() => {
      try { document.getElementById('application').requestSubmit(); } catch (_) {}
    });
  </script>
</body>
</html>`;
}


async function startFixtureServer() {
  let mutatingRequests = 0;
  const server = http.createServer((request, response) => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) mutatingRequests += 1;
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
  };
}


test('live inspector extracts structure while blocking mutation and secret export', { timeout: 60_000 }, async () => {
  const fixture = await startFixtureServer();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-inspect-smoke-'));
  try {
    const result = await inspectForm({
      url: `${fixture.origin}/fixture?session=TOP-SECRET-QUERY#private`,
      profileDir,
      allowedOrigins: [fixture.origin],
      headless: true,
      channel: 'chromium',
      timeoutMs: 20_000,
    });

    assert.equal(result.mode, 'INSPECT_ONLY');
    assert.equal(result.page.url, `${fixture.origin}/fixture`);
    assert.equal(result.page.origin, fixture.origin);
    assert.equal(result.forms.length, 1);
    assert.equal(result.forms[0].method, 'POST');
    assert.equal(result.forms[0].action, `${fixture.origin}/submit`);
    assert.equal(result.submit_controls[0].label, 'Send application');
    assert.equal(result.unsupported_custom_control_count, 1);

    const byKey = new Map(result.fields.map((field) => [field.field_key, field]));
    assert.equal(byKey.get('email').field_type, 'email');
    assert.equal(byKey.get('motivation').maxlength, 250);
    assert.deepEqual(byKey.get('country').options, ['Spain', 'Portugal']);
    assert.deepEqual(byKey.get('role').options, ['Participant', 'Group leader']);
    assert.deepEqual(byKey.get('skills').options, ['Video', 'Photography']);
    assert.equal(byKey.get('password').ownership, 'black_secret_or_never_model');
    assert.equal(byKey.get('password').sensitivity, 'secret');
    assert.equal(byKey.get('otp').ownership, 'black_secret_or_never_model');

    const serialized = JSON.stringify(result);
    for (const secret of ['TOP-SECRET-QUERY', 'ACTION-SECRET', 'SECRET-IN-FIELD', 'PRIVATE-MOTIVATION', 'PASSWORD-SECRET', '123456']) {
      assert.equal(serialized.includes(secret), false, `inspector leaked fixture secret: ${secret}`);
    }
    assert.equal(fixture.mutationCount(), 0, 'mutating request reached fixture server');
    assert.deepEqual(result.safety, {
      form_values_read: false,
      url_query_material_exported: false,
      cookies_read: false,
      storage_state_exported: false,
      mutating_http_methods_blocked: true,
      submit_events_blocked: true,
    });
  } finally {
    await new Promise((resolve) => fixture.server.close(resolve));
    fs.rmSync(profileDir, { recursive: true, force: true });
  }
});
