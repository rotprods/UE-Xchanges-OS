import test from 'node:test';
import assert from 'node:assert/strict';
import {
  assertDedicatedProfileDir,
  defaultProfileDir,
  networkDecision,
  normalizeAllowedOrigins,
  normalizeOrigin,
} from '../src/guard.mjs';

test('normalizes origins and deduplicates', () => {
  assert.equal(normalizeOrigin('HTTPS://Example.COM/path?q=1'), 'https://example.com');
  assert.deepEqual(normalizeAllowedOrigins(['https://example.com/a', 'https://example.com/b']), ['https://example.com']);
});

test('blocks every mutating HTTP method in inspect-only mode', () => {
  for (const method of ['POST', 'PUT', 'PATCH', 'DELETE']) {
    assert.deepEqual(
      networkDecision({ method, url: 'https://example.com/x', isTopLevelNavigation: false, allowedOrigins: ['https://example.com'] }),
      { action: 'abort', reason: 'mutating_http_method' },
    );
  }
});

test('blocks top-level navigation outside allowlist but permits subresources', () => {
  assert.equal(
    networkDecision({ method: 'GET', url: 'https://evil.example/x', isTopLevelNavigation: true, allowedOrigins: ['https://forms.example'] }).action,
    'abort',
  );
  assert.equal(
    networkDecision({ method: 'GET', url: 'https://cdn.example/x.js', isTopLevelNavigation: false, allowedOrigins: ['https://forms.example'] }).action,
    'continue',
  );
});

test('default profile is dedicated and personal Chrome profile is rejected', () => {
  const home = '/Users/tester';
  assert.equal(defaultProfileDir(home), '/Users/tester/.uexchanges/browser/profile');
  assert.throws(
    () => assertDedicatedProfileDir('/Users/tester/Library/Application Support/Google/Chrome/Default', home),
    /dedicated UEX profile/,
  );
  assert.equal(assertDedicatedProfileDir('/Users/tester/.uexchanges/browser/profile', home), '/Users/tester/.uexchanges/browser/profile');
});
