import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalBodyHash, issueRelayCapability, verifyRelayCapability } from '../src/capability.mjs';

const SECRET = Buffer.from('r'.repeat(48));
const NOW = new Date('2026-09-01T21:45:00.000Z');
const BODY = { plan: { application_id: 'app-1', fields: [{ field_key: 'email', answer: 'x@example.com' }] } };


test('capability binds operation request id and exact canonical body hash', () => {
  const bodyHash = canonicalBodyHash(BODY);
  const token = issueRelayCapability({ operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: SECRET, now: NOW, ttlSeconds: 120, nonce: 'nonce-fixed-001' });
  const valid = verifyRelayCapability({ token, operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: SECRET, now: new Date(NOW.getTime() + 1000) });
  assert.equal(valid.valid, true);
  assert.equal(valid.claims.body_hash, bodyHash);

  assert.equal(verifyRelayCapability({ token, operation: 'prefill-local', requestId: 'req-prefill-0002', bodyHash, secret: SECRET, now: new Date(NOW.getTime() + 1000) }).code, 'RELAY_CAPABILITY_BINDING_MISMATCH');
  assert.equal(verifyRelayCapability({ token, operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash: canonicalBodyHash({ plan: { application_id: 'app-2' } }), secret: SECRET, now: new Date(NOW.getTime() + 1000) }).code, 'RELAY_CAPABILITY_BINDING_MISMATCH');
});

test('capability rejects tamper wrong secret expiry and excessive ttl', () => {
  const bodyHash = canonicalBodyHash(BODY);
  const token = issueRelayCapability({ operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: SECRET, now: NOW, ttlSeconds: 5, nonce: 'nonce-fixed-002' });
  const parts = token.split('.');
  parts[2] = `${parts[2][0] === '0' ? '1' : '0'}${parts[2].slice(1)}`;
  assert.equal(verifyRelayCapability({ token: parts.join('.'), operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: SECRET, now: NOW }).code, 'RELAY_CAPABILITY_SIGNATURE_INVALID');
  assert.equal(verifyRelayCapability({ token, operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: Buffer.from('x'.repeat(48)), now: NOW }).code, 'RELAY_CAPABILITY_SIGNATURE_INVALID');
  assert.equal(verifyRelayCapability({ token, operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: SECRET, now: new Date(NOW.getTime() + 5000) }).code, 'RELAY_CAPABILITY_EXPIRED');
  assert.throws(() => issueRelayCapability({ operation: 'prefill-local', requestId: 'req-prefill-0001', bodyHash, secret: SECRET, now: NOW, ttlSeconds: 301 }), /RELAY_CAPABILITY_TTL_INVALID/);
});

test('canonical body hash is key-order stable but materially sensitive', () => {
  assert.equal(canonicalBodyHash({ b: 2, a: { y: 2, x: 1 } }), canonicalBodyHash({ a: { x: 1, y: 2 }, b: 2 }));
  assert.notEqual(canonicalBodyHash({ a: 1 }), canonicalBodyHash({ a: 2 }));
  assert.throws(() => canonicalBodyHash({ value: Infinity }), /RELAY_NONFINITE_NUMBER/);
});
