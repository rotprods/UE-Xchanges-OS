const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1']);

function normalizedHostname(parsed) {
  const raw = parsed.hostname.toLowerCase();
  return raw.startsWith('[') && raw.endsWith(']') ? raw.slice(1, -1) : raw;
}

function assertLoopbackWorkerUrl(value) {
  if (typeof value !== 'string') throw new Error('RELAY_WORKER_URL_INVALID');
  const parsed = new URL(value);
  if (parsed.protocol !== 'http:' || !LOOPBACK_HOSTS.has(normalizedHostname(parsed)) || parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error('RELAY_WORKER_URL_MUST_BE_LOOPBACK_HTTP');
  }
  if (parsed.pathname !== '/' && parsed.pathname !== '') throw new Error('RELAY_WORKER_URL_PATH_INVALID');
  return new URL(`${parsed.origin}/`);
}

function assertWorkerToken(value) {
  if (typeof value !== 'string' || value.length < 32 || /\s/.test(value)) throw new Error('RELAY_WORKER_TOKEN_INVALID');
  return value;
}

function requestIdHeader(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9._:-]{8,128}$/.test(value)) throw new Error('RELAY_REQUEST_ID_INVALID');
  return value;
}

async function parseWorkerResponse(response, workerToken) {
  let value;
  try { value = await response.json(); }
  catch { throw new Error('RELAY_WORKER_RESPONSE_INVALID_JSON'); }
  if (!value || typeof value !== 'object' || Array.isArray(value) || typeof value.ok !== 'boolean') throw new Error('RELAY_WORKER_RESPONSE_INVALID');
  const serialized = JSON.stringify(value);
  if (serialized.includes(workerToken)) throw new Error('RELAY_WORKER_SECRET_LEAK_DETECTED');
  if (!response.ok || !value.ok) {
    const code = value?.error?.code;
    if (typeof code === 'string' && /^[A-Z0-9_]{3,96}$/.test(code)) throw new Error(code);
    throw new Error(`RELAY_WORKER_HTTP_${response.status}`);
  }
  if (!('result' in value)) throw new Error('RELAY_WORKER_RESULT_MISSING');
  return value.result;
}

export class BrowserWorkerClient {
  constructor({ baseUrl, token, timeoutMs = 15_000, fetchImpl = fetch }) {
    this.baseUrl = assertLoopbackWorkerUrl(baseUrl);
    this.token = assertWorkerToken(token);
    if (!Number.isInteger(timeoutMs) || timeoutMs < 1000 || timeoutMs > 120_000) throw new Error('RELAY_TIMEOUT_INVALID');
    if (typeof fetchImpl !== 'function') throw new Error('RELAY_FETCH_INVALID');
    this.timeoutMs = timeoutMs;
    this.fetchImpl = fetchImpl;
  }

  safeDescriptor() {
    return { worker_transport: 'loopback_http', worker_origin: this.baseUrl.origin, token_configured: true };
  }

  async _fetch(path, init = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      return await this.fetchImpl(new URL(path, this.baseUrl), {
        ...init,
        signal: controller.signal,
        headers: { authorization: `Bearer ${this.token}`, ...(init.headers || {}) },
      });
    } catch (error) {
      if (error?.name === 'AbortError') throw new Error('RELAY_WORKER_TIMEOUT');
      throw new Error('RELAY_WORKER_UNREACHABLE');
    } finally { clearTimeout(timeout); }
  }

  async status() {
    const response = await this._fetch('/v1/status', { method: 'GET' });
    return parseWorkerResponse(response, this.token);
  }

  async post({ path, requestId, body }) {
    const id = requestIdHeader(requestId);
    const response = await this._fetch(path, {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-uex-request-id': id },
      body: JSON.stringify(body),
    });
    return parseWorkerResponse(response, this.token);
  }

  inspectLocal({ requestId, provider, url, allowedOrigins }) {
    return this.post({ path: '/v1/inspect', requestId, body: { provider, url, allowed_origins: allowedOrigins } });
  }

  validateLocal({ requestId, plan }) { return this.post({ path: '/v1/validate-local', requestId, body: { plan } }); }
  prefillLocal({ requestId, plan }) { return this.post({ path: '/v1/prefill-local', requestId, body: { plan } }); }
}

export { assertLoopbackWorkerUrl, normalizedHostname };
