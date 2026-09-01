import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER = path.resolve(HERE, '../src/server.mjs');

async function eventuallyUnavailable(origin, timeoutMs = 5_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${origin}/healthz`, { signal: AbortSignal.timeout(300) });
      if (!response.ok) return true;
    } catch { return true; }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return false;
}

test('one stdio process supervises Relay + Worker and kills Worker when MCP closes', { timeout: 120_000 }, async () => {
  const home = process.env.HOME;
  if (!home) throw new Error('HOME_REQUIRED_FOR_E2E');
  const keyPath = path.join(home, '.uexchanges', 'secrets', `stack-e2e-${process.pid}.key`);
  try { fs.rmSync(keyPath, { force: true }); } catch {}

  const env = {
    HOME: home,
    PATH: process.env.PATH || '',
    LANG: process.env.LANG || 'C.UTF-8',
    TMPDIR: process.env.TMPDIR || '/tmp',
    PLAYWRIGHT_BROWSERS_PATH: process.env.PLAYWRIGHT_BROWSERS_PATH || '',
    UEX_BROWSER_CHANNEL: 'chromium',
    UEX_BROWSER_HEADLESS: '1',
    UEX_BROWSER_STACK_ALLOW_LOCAL_PREFILL: '0',
    UEX_BROWSER_STACK_CAPABILITY_KEY_PATH: keyPath,
  };
  const transport = new StdioClientTransport({ command: process.execPath, args: [SERVER], env });
  const client = new Client({ name: 'uex-stack-e2e-client', version: '0.1.0' });
  let workerOrigin;
  try {
    await client.connect(transport);
    const { tools } = await client.listTools();
    assert.deepEqual(tools.map((tool) => tool.name).sort(), [
      'browser_inspect_local',
      'browser_prefill_local',
      'browser_status',
      'browser_validate_local',
    ]);
    assert.equal(tools.some((tool) => /submit|cookie|storage|shell|eval|upload|payment/i.test(tool.name)), false);

    const status = await client.callTool({ name: 'browser_status', arguments: {} });
    assert.equal(status.isError, undefined);
    assert.equal(status.structuredContent.capabilities.submit, false);
    assert.equal(status.structuredContent.capabilities.external_prefill, false);
    assert.equal(status.structuredContent.worker.status.safety.submit_api_present, false);
    assert.equal(status.structuredContent.worker.status.transport.operations.includes('prefill-local'), false);
    workerOrigin = status.structuredContent.worker.descriptor.worker_origin;
    assert.match(workerOrigin, /^http:\/\/127\.0\.0\.1:\d+$/);

    assert.equal(fs.existsSync(keyPath), true);
    assert.equal(fs.statSync(keyPath).mode & 0o777, 0o600);
  } finally {
    await client.close();
  }

  assert.equal(await eventuallyUnavailable(workerOrigin), true, 'supervisor left Browser Worker alive after MCP close');
  fs.rmSync(keyPath, { force: true });
});
