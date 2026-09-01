import crypto from 'node:crypto';

const PREFIX = 'uexrel1';
const DOMAIN = Buffer.from('UEX_BROWSER_RELAY_CAPABILITY_V1\0', 'utf8');
const MAX_TTL_SECONDS = 300;
const MIN_SECRET_BYTES = 32;
const ALLOWED_OPERATIONS = new Set(['prefill-local']);
const REQUEST_ID_RE = /^[A-Za-z0-9._:-]{8,128}$/;
const SHA256_RE = /^sha256:[0-9a-f]{64}$/;

function stableJson(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('RELAY_NONFINITE_NUMBER');
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  throw new Error('RELAY_UNSERIALIZABLE_VALUE');
}

export function canonicalBodyHash(value) {
  const encoded = Buffer.from(stableJson(value), 'utf8');
  return `sha256:${crypto.createHash('sha256').update(encoded).digest('hex')}`;
}

function assertSecret(secret) {
  if (!Buffer.isBuffer(secret) || secret.length < MIN_SECRET_BYTES) throw new Error('RELAY_CAPABILITY_SECRET_INVALID');
}

function assertOperation(value) {
  if (!ALLOWED_OPERATIONS.has(value)) throw new Error('RELAY_CAPABILITY_OPERATION_INVALID');
  return value;
}

function assertRequestId(value) {
  if (typeof value !== 'string' || !REQUEST_ID_RE.test(value)) throw new Error('RELAY_CAPABILITY_REQUEST_ID_INVALID');
  return value;
}

function b64url(value) {
  return Buffer.from(value).toString('base64url');
}

function decodeB64url(value) {
  return Buffer.from(value, 'base64url');
}

function sign(payload, secret) {
  return crypto.createHmac('sha256', secret).update(DOMAIN).update(payload).digest('hex');
}

function encodeClaims(claims) {
  return Buffer.from(stableJson(claims), 'utf8');
}

export function issueRelayCapability({ operation, requestId, bodyHash, secret, now = new Date(), ttlSeconds = 120, nonce = crypto.randomBytes(18).toString('base64url') }) {
  assertSecret(secret);
  assertOperation(operation);
  assertRequestId(requestId);
  if (typeof bodyHash !== 'string' || !SHA256_RE.test(bodyHash)) throw new Error('RELAY_CAPABILITY_BODY_HASH_INVALID');
  if (!(now instanceof Date) || Number.isNaN(now.getTime())) throw new Error('RELAY_CAPABILITY_TIME_INVALID');
  if (!Number.isInteger(ttlSeconds) || ttlSeconds < 1 || ttlSeconds > MAX_TTL_SECONDS) throw new Error('RELAY_CAPABILITY_TTL_INVALID');
  if (typeof nonce !== 'string' || nonce.length < 8 || nonce.length > 128) throw new Error('RELAY_CAPABILITY_NONCE_INVALID');

  const issuedAt = now.toISOString();
  const expiresAt = new Date(now.getTime() + ttlSeconds * 1000).toISOString();
  const capabilityId = `relaycap:${crypto.createHash('sha256').update(`${operation}|${requestId}|${bodyHash}|${issuedAt}|${nonce}`).digest('hex')}`;
  const claims = {
    capability_id: capabilityId,
    operation,
    request_id: requestId,
    body_hash: bodyHash,
    issued_at: issuedAt,
    expires_at: expiresAt,
    nonce,
  };
  const payload = encodeClaims(claims);
  return `${PREFIX}.${b64url(payload)}.${sign(payload, secret)}`;
}

export function verifyRelayCapability({ token, operation, requestId, bodyHash, secret, now = new Date() }) {
  assertSecret(secret);
  assertOperation(operation);
  assertRequestId(requestId);
  if (typeof bodyHash !== 'string' || !SHA256_RE.test(bodyHash)) throw new Error('RELAY_CAPABILITY_BODY_HASH_INVALID');
  if (!(now instanceof Date) || Number.isNaN(now.getTime())) throw new Error('RELAY_CAPABILITY_TIME_INVALID');

  try {
    if (typeof token !== 'string') return { valid: false, code: 'RELAY_CAPABILITY_MALFORMED' };
    const [prefix, payloadPart, signature, extra] = token.split('.');
    if (prefix !== PREFIX || !payloadPart || !signature || extra !== undefined) return { valid: false, code: 'RELAY_CAPABILITY_MALFORMED' };
    const payload = decodeB64url(payloadPart);
    const expected = Buffer.from(sign(payload, secret), 'ascii');
    const actual = Buffer.from(signature, 'ascii');
    if (actual.length !== expected.length || !crypto.timingSafeEqual(actual, expected)) return { valid: false, code: 'RELAY_CAPABILITY_SIGNATURE_INVALID' };
    const claims = JSON.parse(payload.toString('utf8'));
    const exactKeys = ['capability_id', 'operation', 'request_id', 'body_hash', 'issued_at', 'expires_at', 'nonce'];
    if (!claims || typeof claims !== 'object' || Array.isArray(claims) || Object.keys(claims).sort().join('|') !== [...exactKeys].sort().join('|')) {
      return { valid: false, code: 'RELAY_CAPABILITY_CLAIMS_INVALID' };
    }
    if (claims.operation !== operation || claims.request_id !== requestId || claims.body_hash !== bodyHash) return { valid: false, code: 'RELAY_CAPABILITY_BINDING_MISMATCH' };
    if (typeof claims.capability_id !== 'string' || !claims.capability_id.startsWith('relaycap:') || typeof claims.nonce !== 'string') return { valid: false, code: 'RELAY_CAPABILITY_CLAIMS_INVALID' };
    const issuedAt = new Date(claims.issued_at);
    const expiresAt = new Date(claims.expires_at);
    if (Number.isNaN(issuedAt.getTime()) || Number.isNaN(expiresAt.getTime()) || expiresAt <= issuedAt) return { valid: false, code: 'RELAY_CAPABILITY_CLAIMS_INVALID' };
    if (now < issuedAt) return { valid: false, code: 'RELAY_CAPABILITY_NOT_YET_VALID' };
    if (now >= expiresAt) return { valid: false, code: 'RELAY_CAPABILITY_EXPIRED' };
    if ((expiresAt.getTime() - issuedAt.getTime()) / 1000 > MAX_TTL_SECONDS) return { valid: false, code: 'RELAY_CAPABILITY_TTL_INVALID' };
    return { valid: true, code: 'RELAY_CAPABILITY_VALID', claims };
  } catch {
    return { valid: false, code: 'RELAY_CAPABILITY_MALFORMED' };
  }
}

export const RELAY_CAPABILITY_MAX_TTL_SECONDS = MAX_TTL_SECONDS;
