import test from 'node:test';
import assert from 'node:assert/strict';
import { Client } from '@modelcontextprotocol/client';
import { InMemoryTransport } from '@modelcontextprotocol/server';
import { createRelayMcpServer } from '../src/mcp-server.mjs';

function fakeCore() {
  return {
    status: async () => ({ relay_version: 'test', capabilities: { submit: false } }),
    inspectLocal: async () => ({ mode: 'INSPECT_LOCAL_ONLY', form_fingerprint: `sha256:${'f'.repeat(64)}` }),
    validateLocal: async () => ({ mode: 'VALIDATE_LOCAL_ONLY', all_values_match: true }),
    prefillLocal: async ({ capability }) => {
      if (capability !== 'valid-capability-token'.padEnd(40, 'x')) throw new Error('RELAY_CAPABILITY_MALFORMED');
      return { mode: 'PREFILL_LOCAL_ONLY', write_count: 1 };
    },
  };
}

async function withMcp(fn) {
  const server = createRelayMcpServer({ core: fakeCore() });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: 'uex-relay-test-client', version: '0.1.0' });
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  try { await fn(client); }
  finally {
    await client.close();
    await server.close();
  }
}

test('MCP tool surface contains no Submit/browser-generic escape hatch', async () => {
  await withMcp(async (client) => {
    const { tools } = await client.listTools();
    const names = tools.map((tool) => tool.name).sort();
    assert.deepEqual(names, [
      'browser_inspect_local',
      'browser_prefill_local',
      'browser_status',
      'browser_validate_local',
    ]);
    assert.equal(names.some((name) => /submit|cookie|storage|eval|shell|upload|payment/i.test(name)), false);
  });
});

test('status call returns structured value-free result', async () => {
  await withMcp(async (client) => {
    const result = await client.callTool({ name: 'browser_status', arguments: {} });
    assert.equal(result.isError, undefined);
    assert.equal(result.structuredContent.capabilities.submit, false);
  });
});

test('prefill handler returns code-only error when capability is invalid', async () => {
  await withMcp(async (client) => {
    const result = await client.callTool({
      name: 'browser_prefill_local',
      arguments: {
        request_id: 'req-prefill-0001',
        plan: { application_id: 'app-1' },
        capability: 'not-a-valid-capability-token-but-long-enough',
      },
    });
    assert.equal(result.isError, true);
    assert.equal(JSON.stringify(result).includes('RELAY_CAPABILITY_MALFORMED'), true);
    assert.equal(JSON.stringify(result).includes('stack'), false);
  });
});
