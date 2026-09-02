import { McpServer } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

const requestId = z.string().regex(/^[A-Za-z0-9._:-]{8,128}$/);
const url = z.string().url();
const plan = z.record(z.string(), z.unknown());
const applicationId = z.string().regex(/^[A-Za-z0-9._:-]{3,160}$/);

function safeCode(error) {
  const raw = typeof error?.message === 'string' ? error.message : '';
  return /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'RELAY_OPERATION_FAILED';
}

function success(result) {
  return {
    content: [{ type: 'text', text: JSON.stringify(result) }],
    structuredContent: result,
  };
}

function failure(error) {
  const code = safeCode(error);
  return {
    content: [{ type: 'text', text: JSON.stringify({ ok: false, error: { code } }) }],
    structuredContent: { ok: false, error: { code } },
    isError: true,
  };
}

export function createRelayMcpServer({ core }) {
  if (!core) throw new Error('RELAY_CORE_REQUIRED');
  const server = new McpServer(
    { name: 'uex-browser-relay', version: '0.2.0' },
    {
      instructions: [
        'UE-Xchanges Browser Worker relay.',
        'External form capture is read-only and requires a repository-certified provider manifest.',
        'External PREFILL and Submit are not available.',
        'Never request or expose passwords, OTPs, cookies, storage state, worker tokens, or signing secrets.',
        'browser_prefill_local remains loopback-only and requires a short-lived capability bound to the exact request ID and plan hash.',
      ].join(' '),
    },
  );

  server.registerTool(
    'browser_status',
    {
      description: 'Read value-free status/capability ceiling from the local Browser Worker. No browser mutation.',
      inputSchema: z.object({}),
    },
    async () => {
      try { return success(await core.status()); }
      catch (error) { return failure(error); }
    },
  );

  server.registerTool(
    'browser_inspect_local',
    {
      description: 'Inspect a loopback-only fixture form with mutation/submit/cross-origin requests blocked. Returns structure and hashes, never current field values.',
      inputSchema: z.object({
        request_id: requestId,
        provider: z.string().min(1).max(80),
        url,
        allowed_origins: z.array(url).min(1).max(8),
      }),
    },
    async ({ request_id, provider, url: targetUrl, allowed_origins }) => {
      try {
        return success(await core.inspectLocal({ requestId: request_id, provider, url: targetUrl, allowedOrigins: allowed_origins }));
      } catch (error) { return failure(error); }
    },
  );

  server.registerTool(
    'browser_capture_provider_form',
    {
      description: 'Capture the exact value-free schema of a repository-certified external provider form. Ephemeral browser context; GET/HEAD/OPTIONS only; no login, PREFILL or Submit.',
      inputSchema: z.object({
        request_id: requestId,
        application_id: applicationId,
        provider: z.enum(['google_forms']),
        url,
      }),
    },
    async ({ request_id, application_id, provider, url: targetUrl }) => {
      try {
        if (typeof core.inspectProvider !== 'function') throw new Error('RELAY_PROVIDER_CAPTURE_UNAVAILABLE');
        return success(await core.inspectProvider({ requestId: request_id, applicationId: application_id, provider, url: targetUrl }));
      } catch (error) { return failure(error); }
    },
  );

  server.registerTool(
    'browser_validate_local',
    {
      description: 'Validate the current retained loopback DOM against an exact plan. Returns field keys/booleans only, never values.',
      inputSchema: z.object({ request_id: requestId, plan }),
    },
    async ({ request_id, plan: executionPlan }) => {
      try { return success(await core.validateLocal({ requestId: request_id, plan: executionPlan })); }
      catch (error) { return failure(error); }
    },
  );

  server.registerTool(
    'browser_prefill_local',
    {
      description: 'Capability-gated loopback-only PREFILL. Requires a short-lived HMAC capability bound to this request_id and the exact plan. There is no external prefill or submit tool.',
      inputSchema: z.object({
        request_id: requestId,
        plan,
        capability: z.string().min(32).max(4096),
      }),
    },
    async ({ request_id, plan: executionPlan, capability }) => {
      try { return success(await core.prefillLocal({ requestId: request_id, plan: executionPlan, capability })); }
      catch (error) { return failure(error); }
    },
  );

  return server;
}

export { safeCode };
