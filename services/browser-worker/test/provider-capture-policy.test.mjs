import test from 'node:test';
import assert from 'node:assert/strict';
import { assertProviderTargetUrl, providerNetworkDecision } from '../src/provider-capture.mjs';

const allowed = ['https://forms.gle', 'https://docs.google.com', 'https://ssl.gstatic.com'];

test('provider capture requires HTTPS for external targets', () => {
  assert.throws(() => assertProviderTargetUrl('http://docs.google.com/forms/x'), /PROVIDER_CAPTURE_HTTPS_REQUIRED/);
  assert.doesNotThrow(() => assertProviderTargetUrl('https://docs.google.com/forms/x'));
});

test('provider capture blocks mutating methods and uncertified origins', () => {
  assert.deepEqual(providerNetworkDecision({ method: 'POST', url: 'https://docs.google.com/forms/x', allowedOrigins: allowed }), {
    action: 'abort', reason: 'mutating_http_method',
  });
  assert.deepEqual(providerNetworkDecision({ method: 'GET', url: 'https://evil.example/form', allowedOrigins: allowed }), {
    action: 'abort', reason: 'origin_not_certified',
  });
  assert.deepEqual(providerNetworkDecision({ method: 'GET', url: 'https://docs.google.com/forms/x', allowedOrigins: allowed }), {
    action: 'continue', reason: 'certified_read_only_request',
  });
});

test('loopback HTTP is available only to explicit test mode', () => {
  assert.throws(() => assertProviderTargetUrl('http://127.0.0.1:9000/form'), /PROVIDER_CAPTURE_HTTPS_REQUIRED/);
  assert.doesNotThrow(() => assertProviderTargetUrl('http://127.0.0.1:9000/form', { allowInsecureLoopback: true }));
});
