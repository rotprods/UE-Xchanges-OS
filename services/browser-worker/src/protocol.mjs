const MAX_BODY_BYTES = 1_000_000;

function assertPlainObject(value, code = 'WORKER_BODY_INVALID') {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(code);
  return value;
}

function assertExactKeys(value, allowed, code = 'WORKER_BODY_KEYS_INVALID') {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new Error(code);
  }
}

function assertHttpUrl(value, code = 'WORKER_URL_INVALID') {
  if (typeof value !== 'string') throw new Error(code);
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) throw new Error(code);
  return value;
}

export async function readJsonBody(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) throw new Error('WORKER_BODY_TOO_LARGE');
    chunks.push(chunk);
  }
  const raw = Buffer.concat(chunks);
  if (!raw.length) throw new Error('WORKER_BODY_REQUIRED');
  let parsed;
  try {
    parsed = JSON.parse(raw.toString('utf8'));
  } catch {
    throw new Error('WORKER_JSON_INVALID');
  }
  return { raw, parsed: assertPlainObject(parsed) };
}

export function parseInspectRequest(value) {
  const body = assertPlainObject(value);
  assertExactKeys(body, new Set(['provider', 'url', 'allowed_origins']));
  if (typeof body.provider !== 'string' || !body.provider.trim()) throw new Error('WORKER_PROVIDER_INVALID');
  assertHttpUrl(body.url);
  if (!Array.isArray(body.allowed_origins) || body.allowed_origins.length === 0) throw new Error('WORKER_ALLOWED_ORIGINS_INVALID');
  const allowedOrigins = body.allowed_origins.map((origin) => {
    assertHttpUrl(origin, 'WORKER_ALLOWED_ORIGINS_INVALID');
    return origin;
  });
  return { provider: body.provider.trim(), url: body.url, allowedOrigins };
}

export function parsePlanRequest(value) {
  const body = assertPlainObject(value);
  assertExactKeys(body, new Set(['plan']));
  const plan = assertPlainObject(body.plan, 'WORKER_PLAN_INVALID');
  return { plan };
}

export function responseEnvelope({ requestId = null, operation, result }) {
  return { ok: true, request_id: requestId, operation, result };
}

export function errorEnvelope({ requestId = null, code }) {
  return { ok: false, request_id: requestId, error: { code } };
}

export function jsonBytes(value) {
  return Buffer.from(JSON.stringify(value), 'utf8');
}
