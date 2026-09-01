#!/usr/bin/env node
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { BrowserWorkerClient } from './worker-client.mjs';
import { BrowserRelayCore } from './relay-core.mjs';
import { createRelayMcpServer } from './mcp-server.mjs';

function secretFromEnv(name) {
  const value = process.env[name];
  if (typeof value !== 'string' || value.length < 32 || /\s/.test(value)) throw new Error(`${name}_INVALID`);
  return value;
}

export function createServerFromEnvironment(env = process.env) {
  const workerUrl = env.UEX_BROWSER_WORKER_URL || 'http://127.0.0.1:4777/';
  const workerToken = env.UEX_BROWSER_WORKER_TOKEN;
  const capabilitySecret = env.UEX_BROWSER_RELAY_CAPABILITY_SECRET;
  if (typeof workerToken !== 'string') throw new Error('UEX_BROWSER_WORKER_TOKEN_REQUIRED');
  if (typeof capabilitySecret !== 'string') throw new Error('UEX_BROWSER_RELAY_CAPABILITY_SECRET_REQUIRED');
  const workerClient = new BrowserWorkerClient({ baseUrl: workerUrl, token: secretFromEnv.call({ }, 'UEX_BROWSER_WORKER_TOKEN') });
  const core = new BrowserRelayCore({ workerClient, capabilitySecret: Buffer.from(secretFromEnv.call({ }, 'UEX_BROWSER_RELAY_CAPABILITY_SECRET'), 'utf8') });
  return createRelayMcpServer({ core });
}

async function main() {
  await serveStdio(() => createServerFromEnvironment(process.env));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    const raw = typeof error?.message === 'string' ? error.message : 'RELAY_START_FAILED';
    const code = /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'RELAY_START_FAILED';
    process.stderr.write(`UEX_BROWSER_RELAY_ERROR:${code}\n`);
    process.exitCode = 1;
  });
}
