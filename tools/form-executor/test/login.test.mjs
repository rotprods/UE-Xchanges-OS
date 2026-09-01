import test from 'node:test';
import assert from 'node:assert/strict';
import { parseHumanLoginArgs } from '../src/login-args.mjs';
import { humanLoginNavigationDecision } from '../src/login-guard.mjs';


test('human login requires a provider base URL without query secrets', () => {
  const parsed = parseHumanLoginArgs(
    ['--url', 'https://accounts.example.com/', '--allowed-origin', 'https://app.example.com/'],
    '/Users/tester',
  );
  assert.equal(parsed.url, 'https://accounts.example.com/');
  assert.deepEqual(parsed.allowedOrigins, ['https://accounts.example.com', 'https://app.example.com']);
  assert.equal(parsed.profileDir, '/Users/tester/.uexchanges/browser/profile');

  assert.throws(
    () => parseHumanLoginArgs(['--url', 'https://accounts.example.com/?token=secret'], '/Users/tester'),
    /must not contain query or fragment/,
  );
  assert.throws(
    () => parseHumanLoginArgs(['--url', 'https://user:secret@accounts.example.com/'], '/Users/tester'),
    /embedded credentials/,
  );
});


test('human login parser rejects automation and submit flags', () => {
  for (const forbidden of ['--headless', '--submit', '--fill', '--click', '--cookie', '--storage-state']) {
    assert.throws(
      () => parseHumanLoginArgs(['--url', 'https://accounts.example.com/', forbidden], '/Users/tester'),
      /unknown human-login argument/,
    );
  }
});


test('human login top-level navigation is origin allowlisted without method filtering', () => {
  const allowedOrigins = ['https://accounts.example.com', 'https://app.example.com'];
  assert.deepEqual(
    humanLoginNavigationDecision({
      url: 'https://accounts.example.com/session',
      isTopLevelNavigation: true,
      allowedOrigins,
    }),
    { action: 'continue', reason: 'human_login_allowed_origin' },
  );
  assert.deepEqual(
    humanLoginNavigationDecision({
      url: 'https://evil.example/session',
      isTopLevelNavigation: true,
      allowedOrigins,
    }),
    { action: 'abort', reason: 'top_level_origin_not_allowed' },
  );
  assert.deepEqual(
    humanLoginNavigationDecision({
      url: 'https://cdn.example/script.js',
      isTopLevelNavigation: false,
      allowedOrigins,
    }),
    { action: 'continue', reason: 'subresource_human_login' },
  );
});
