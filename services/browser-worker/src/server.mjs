import http from 'node:http';
import {
  assertLoopbackBind,
  assertRequestId,
  assertSafeRequestMetadata,
  assertWorkerToken,
  isAuthorizedRequest,
  safeErrorCode,
  sha256Bytes,
} from './security.mjs';
import {
  errorEnvelope,
  jsonBytes,
  parseInspectRequest,
  parsePlanRequest,
  parseProviderInspectRequest,
  readJsonBody,
  responseEnvelope,
} from './protocol.mjs';

function sendJson(response, statusCode, payload, extraHeaders = {}) {
  const bytes = jsonBytes(payload);
  response.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': String(bytes.length),
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
    ...extraHeaders,
  });
  response.end(bytes);
}

function routePath(request) {
  try {
    return new URL(request.url, 'http://127.0.0.1').pathname;
  } catch {
    throw new Error('WORKER_PATH_INVALID');
  }
}

export function createBrowserWorkerServer({
  session,
  providerCapture = null,
  token,
  host = '127.0.0.1',
  port = 4777,
  allowLocalPrefill = false,
  allowExternalInspect = false,
  maxIdempotencyEntries = 256,
}) {
  if (!session || typeof session.status !== 'function') throw new Error('WORKER_SESSION_INVALID');
  if (allowExternalInspect && (!providerCapture || typeof providerCapture.inspect !== 'function')) throw new Error('WORKER_PROVIDER_CAPTURE_INVALID');
  const bindHost = assertLoopbackBind(host);
  const authToken = assertWorkerToken(token);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('WORKER_PORT_INVALID');
  if (!Number.isInteger(maxIdempotencyEntries) || maxIdempotencyEntries < 1 || maxIdempotencyEntries > 4096) {
    throw new Error('WORKER_IDEMPOTENCY_LIMIT_INVALID');
  }

  const cache = new Map();
  let operationTail = Promise.resolve();
  let busy = false;

  function serialize(operation) {
    const run = operationTail.then(async () => {
      busy = true;
      try {
        return await operation();
      } finally {
        busy = false;
      }
    });
    operationTail = run.catch(() => undefined);
    return run;
  }

  function cacheResponse(requestId, bodyHash, statusCode, payload) {
    cache.set(requestId, { bodyHash, statusCode, payload });
    while (cache.size > maxIdempotencyEntries) {
      const oldest = cache.keys().next().value;
      cache.delete(oldest);
    }
  }

  const server = http.createServer(async (request, response) => {
    let requestId = null;
    try {
      assertSafeRequestMetadata(request);
      const path = routePath(request);

      if (path === '/healthz') {
        if (request.method !== 'GET') return sendJson(response, 405, errorEnvelope({ code: 'WORKER_METHOD_NOT_ALLOWED' }));
        return sendJson(response, 200, { ok: true, status: 'ok' });
      }

      if (!path.startsWith('/v1/')) return sendJson(response, 404, errorEnvelope({ code: 'WORKER_ROUTE_NOT_FOUND' }));
      if (!isAuthorizedRequest(request, authToken)) {
        return sendJson(response, 401, errorEnvelope({ code: 'WORKER_UNAUTHORIZED' }));
      }

      if (path === '/v1/status') {
        if (request.method !== 'GET') return sendJson(response, 405, errorEnvelope({ code: 'WORKER_METHOD_NOT_ALLOWED' }));
        const operations = allowLocalPrefill
          ? ['status', 'inspect', 'prefill-local', 'validate-local']
          : ['status', 'inspect', 'validate-local'];
        if (allowExternalInspect) operations.push('inspect-provider');
        return sendJson(response, 200, responseEnvelope({
          operation: 'status',
          result: {
            ...session.status(),
            busy,
            transport: {
              bind: 'loopback_only',
              bearer_auth: true,
              submit_endpoint_present: false,
              human_takeover: 'local_cli_only',
              operations,
              external_inspect: allowExternalInspect ? 'certified_manifest_only' : false,
              external_prefill: false,
            },
          },
        }));
      }

      if (request.method !== 'POST') return sendJson(response, 405, errorEnvelope({ code: 'WORKER_METHOD_NOT_ALLOWED' }));
      requestId = assertRequestId(request.headers['x-uex-request-id']);
      const { raw, parsed } = await readJsonBody(request);
      const bodyHash = sha256Bytes(raw);
      const cached = cache.get(requestId);
      if (cached) {
        if (cached.bodyHash !== bodyHash) {
          return sendJson(response, 409, errorEnvelope({ requestId, code: 'WORKER_REQUEST_ID_REUSE_MISMATCH' }));
        }
        return sendJson(response, cached.statusCode, cached.payload, { 'x-uex-replayed': '1' });
      }

      let operation;
      let invoke;
      if (path === '/v1/inspect') {
        operation = 'inspect';
        const input = parseInspectRequest(parsed);
        invoke = () => session.inspect(input);
      } else if (path === '/v1/inspect-provider') {
        if (!allowExternalInspect) return sendJson(response, 403, errorEnvelope({ requestId, code: 'WORKER_EXTERNAL_INSPECT_DISABLED' }));
        operation = 'inspect-provider';
        const input = parseProviderInspectRequest(parsed);
        invoke = () => providerCapture.inspect(input);
      } else if (path === '/v1/prefill-local') {
        if (!allowLocalPrefill) return sendJson(response, 403, errorEnvelope({ requestId, code: 'WORKER_LOCAL_PREFILL_DISABLED' }));
        operation = 'prefill-local';
        const input = parsePlanRequest(parsed);
        invoke = () => session.prefillLocal(input.plan);
      } else if (path === '/v1/validate-local') {
        operation = 'validate-local';
        const input = parsePlanRequest(parsed);
        invoke = () => session.validateLocal(input.plan);
      } else {
        return sendJson(response, 404, errorEnvelope({ requestId, code: 'WORKER_ROUTE_NOT_FOUND' }));
      }

      const result = await serialize(invoke);
      const payload = responseEnvelope({ requestId, operation, result });
      cacheResponse(requestId, bodyHash, 200, payload);
      return sendJson(response, 200, payload);
    } catch (error) {
      const code = safeErrorCode(error);
      const statusCode = code === 'WORKER_BODY_TOO_LARGE'
        ? 413
        : code === 'WORKER_CROSS_SITE_REQUEST_BLOCKED' || code === 'WORKER_ORIGIN_NOT_LOOPBACK' || code === 'WORKER_EXTERNAL_INSPECT_DISABLED'
          ? 403
          : 400;
      return sendJson(response, statusCode, errorEnvelope({ requestId, code }));
    }
  });

  return {
    server,
    async listen() {
      await session.start?.();
      const address = await new Promise((resolve, reject) => {
        server.once('error', reject);
        server.listen(port, bindHost, () => resolve(server.address()));
      });
      if (!address || typeof address === 'string') throw new Error('WORKER_LISTEN_FAILED');
      return { host: bindHost, port: address.port };
    },
    async close() {
      await new Promise((resolve) => {
        if (!server.listening) return resolve();
        server.close(() => resolve());
      });
      await session.close?.();
    },
  };
}
