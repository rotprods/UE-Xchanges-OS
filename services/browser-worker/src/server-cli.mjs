#!/usr/bin/env node
import os from 'node:os';
import path from 'node:path';
import { BrowserWorkerSession } from './session.mjs';
import { createBrowserWorkerServer } from './server.mjs';

function envFlag(name, defaultValue = false) {
  const raw = process.env[name];
  if (raw === undefined) return defaultValue;
  if (raw === '1' || raw === 'true') return true;
  if (raw === '0' || raw === 'false') return false;
  throw new Error(`${name}_INVALID`);
}

async function main() {
  const token = process.env.UEX_BROWSER_WORKER_TOKEN;
  if (!token) throw new Error('UEX_BROWSER_WORKER_TOKEN_REQUIRED');
  const profileDir = process.env.UEX_BROWSER_PROFILE_DIR || path.join(os.homedir(), '.uexchanges', 'browser', 'profile');
  const channel = process.env.UEX_BROWSER_CHANNEL || 'chrome';
  const portRaw = process.env.UEX_BROWSER_WORKER_PORT || '4777';
  const port = Number(portRaw);
  if (!Number.isInteger(port)) throw new Error('UEX_BROWSER_WORKER_PORT_INVALID');
  const headless = envFlag('UEX_BROWSER_HEADLESS', false);
  const allowLocalPrefill = envFlag('UEX_BROWSER_WORKER_ALLOW_LOCAL_PREFILL', false);

  const session = new BrowserWorkerSession({ profileDir, channel, headless });
  const worker = createBrowserWorkerServer({
    session,
    token,
    host: '127.0.0.1',
    port,
    allowLocalPrefill,
  });
  const address = await worker.listen();
  process.stdout.write(`UEX_BROWSER_WORKER_READY http://${address.host}:${address.port}\n`);
  process.stdout.write('UEX_BROWSER_WORKER_SUBMIT_ENDPOINT=ABSENT\n');

  let closing = false;
  const close = async () => {
    if (closing) return;
    closing = true;
    await worker.close();
    process.exitCode = 0;
  };
  process.on('SIGINT', close);
  process.on('SIGTERM', close);
}

main().catch((error) => {
  const raw = typeof error?.message === 'string' ? error.message : 'WORKER_START_FAILED';
  const code = /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'WORKER_START_FAILED';
  process.stderr.write(`UEX_BROWSER_WORKER_ERROR:${code}\n`);
  process.exitCode = 1;
});
