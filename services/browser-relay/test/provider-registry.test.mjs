import test from 'node:test';
import assert from 'node:assert/strict';
import { loadProviderInspectManifest, assertProviderCaptureUrl } from '../src/provider-registry.mjs';

test('google forms inspect manifest is read-only and exact-origin gated', () => {
  const manifest = loadProviderInspectManifest('google_forms');
  assert.equal(manifest.provider_id, 'google_forms');
  assert.equal(manifest.allowed_origins.includes('https://docs.google.com'), true);
  assert.equal(manifest.allowed_origins.includes('https://forms.gle'), true);
  assert.doesNotThrow(() => assertProviderCaptureUrl(manifest, 'https://docs.google.com/forms/d/e/example/viewform'));
  assert.throws(() => assertProviderCaptureUrl(manifest, 'https://evil.example/form'), /RELAY_PROVIDER_TARGET_ORIGIN_NOT_CERTIFIED/);
  assert.throws(() => assertProviderCaptureUrl(manifest, 'http://docs.google.com/forms/x'), /RELAY_PROVIDER_TARGET_INVALID/);
});

test('uncertified provider fails closed', () => {
  assert.throws(() => loadProviderInspectManifest('unknown_provider'), /RELAY_PROVIDER_NOT_CERTIFIED/);
});
