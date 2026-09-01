import crypto from 'node:crypto';
import path from 'node:path';

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1']);
const REQUEST_ID_RE = /^[A-Za-z0-9._:-]{8,128}$/;

export function assertLoopbackBind(host) {
  if (typeof host !== 'string' || !LOOPBACK_HOSTS.has(host)) {
    throw new Error('WORKER_BIND_MUST_BE_LOOPBACK');
  }
  return host;
}

export function assertWorkerToken(token) {
  if (typeof token !== 'string' || token.length < 32 || /\s/.test(token)) {
    throw new Error('WORKER_TOKEN_INVALID');
  }
  return token;
}

export function isAuthorizedRequest(request, expectedToken) {
  const header = request.headers.authorization;
  if (typeof header !== 'string' || !header.startsWith('Bearer ')) return false;
  const actual = Buffer.from(header.slice(7), 'utf8');
  const expected = Buffer.from(expectedToken, 'utf8');
  if (actual.length !== expected.length) return false;
  return crypto.timingSafeEqual(actual, expected);
}

function hostFromHeader(value) {
  if (typeof value !== 'string' || !value) throw new Error('WORKER_HOST_HEADER_INVALID');
  const parsed = new URL(`http://${value}`);
  return parsed.hostname;
}

export function assertSafeRequestMetadata(request) {
  const host = hostFromHeader(request.headers.host);
  if (!LOOPBACK_HOSTS.has(host)) throw new Error('WORKER_HOST_NOT_LOOPBACK');

  const fetchSite = request.headers['sec-fetch-site'];
  if (typeof fetchSite === 'string' && fetchSite === 'cross-site') {
    throw new Error('WORKER_CROSS_SITE_REQUEST_BLOCKED');
  }

  const origin = request.headers.origin;
  if (typeof origin === 'string') {
    const parsed = new URL(origin);
    if (!LOOPBACK_HOSTS.has(parsed.hostname)) throw new Error('WORKER_ORIGIN_NOT_LOOPBACK');
  }
}

export function assertRequestId(value) {
  if (typeof value !== 'string' || !REQUEST_ID_RE.test(value)) {
    throw new Error('WORKER_REQUEST_ID_INVALID');
  }
  return value;
}

export function sha256Bytes(buffer) {
  return `sha256:${crypto.createHash('sha256').update(buffer).digest('hex')}`;
}

export function profileRef(profileDir) {
  const resolved = path.resolve(profileDir);
  return `profile:${crypto.createHash('sha256').update(resolved, 'utf8').digest('hex')}`;
}

export function safeErrorCode(error) {
  const raw = typeof error?.message === 'string' && error.message ? error.message : 'WORKER_INTERNAL_ERROR';
  if (/^[A-Z0-9_]{3,96}$/.test(raw)) return raw;
  return 'WORKER_OPERATION_FAILED';
}
