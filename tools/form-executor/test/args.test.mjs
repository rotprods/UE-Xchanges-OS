import test from 'node:test';
import assert from 'node:assert/strict';
import { parseInspectArgs } from '../src/args.mjs';

test('parser auto-allows canonical URL origin and uses dedicated profile', () => {
  const parsed = parseInspectArgs(['--url', 'https://forms.example/apply'], '/Users/tester');
  assert.deepEqual(parsed.allowedOrigins, ['https://forms.example']);
  assert.equal(parsed.profileDir, '/Users/tester/.uexchanges/browser/profile');
  assert.equal(parsed.headless, false);
});

test('parser rejects unknown or submit-capable flags', () => {
  assert.throws(() => parseInspectArgs(['--url', 'https://forms.example', '--submit'], '/Users/tester'), /unknown inspect-only argument/);
  assert.throws(() => parseInspectArgs(['--url', 'https://forms.example', '--fill', 'x'], '/Users/tester'), /unknown inspect-only argument/);
});

test('parser permits explicit redirect origins and bounded timeout', () => {
  const parsed = parseInspectArgs(
    ['--url', 'https://short.example/x', '--allowed-origin', 'https://forms.example/path', '--timeout-ms', '5000', '--headless'],
    '/Users/tester',
  );
  assert.deepEqual(parsed.allowedOrigins, ['https://short.example', 'https://forms.example']);
  assert.equal(parsed.timeoutMs, 5000);
  assert.equal(parsed.headless, true);
});
