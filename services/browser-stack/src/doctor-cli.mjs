#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { defaultCapabilityKeyPath, loadOrCreateCapabilitySecret } from './secrets.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORKER_PACKAGE = path.resolve(HERE, '../../browser-worker/package.json');
const RELAY_MCP = path.resolve(HERE, '../../browser-relay/node_modules/@modelcontextprotocol/server/package.json');
const workerRequire = createRequire(WORKER_PACKAGE);

function parseArgs(argv) {
  const out = { channel: 'chrome', keyPath: defaultCapabilityKeyPath() };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const value = argv[++i];
    if (!value) throw new Error('STACK_DOCTOR_ARG_MISSING');
    if (arg === '--channel') out.channel = value;
    else if (arg === '--key-file') out.keyPath = value;
    else throw new Error('STACK_DOCTOR_ARG_UNKNOWN');
  }
  if (!['chrome', 'chromium', 'msedge'].includes(out.channel)) throw new Error('STACK_DOCTOR_CHANNEL_INVALID');
  return out;
}

function dependencyVersion(filePath, code) {
  if (!fs.existsSync(filePath)) throw new Error(code);
  let value;
  try { value = JSON.parse(fs.readFileSync(filePath, 'utf8')); }
  catch { throw new Error(code); }
  if (typeof value.version !== 'string' || !value.version) throw new Error(code);
  return value.version;
}

async function runWorkerDoctor(channel) {
  let chromium;
  let playwrightPackage;
  try {
    ({ chromium } = workerRequire('playwright'));
    playwrightPackage = workerRequire('playwright/package.json');
  } catch {
    throw new Error('STACK_WORKER_DEPENDENCIES_MISSING');
  }

  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-stack-doctor-'));
  const launchOptions = {
    headless: true,
    viewport: { width: 800, height: 600 },
    args: [
      '--disable-background-networking',
      '--disable-component-update',
      '--disable-default-apps',
      '--disable-sync',
      '--metrics-recording-only',
      '--no-first-run',
    ],
  };
  if (channel !== 'chromium') launchOptions.channel = channel;

  let context;
  try {
    context = await chromium.launchPersistentContext(tempRoot, launchOptions);
    await context.route('**/*', (route) => route.abort('blockedbyclient'));
    const page = context.pages()[0] || (await context.newPage());
    await page.goto('about:blank');
    return {
      status: 'ok',
      node_major: Number(process.versions.node.split('.')[0]),
      playwright_version: playwrightPackage.version,
      browser_channel: channel,
      launch: 'ok',
      network: 'blocked',
      profile: 'ephemeral',
    };
  } catch {
    throw new Error('STACK_WORKER_DOCTOR_FAILED');
  } finally {
    if (context) await context.close();
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  if (!Number.isInteger(nodeMajor) || nodeMajor < 20) throw new Error('STACK_NODE_VERSION_UNSUPPORTED');
  let workerDependencyVersion;
  try { workerDependencyVersion = workerRequire('playwright/package.json').version; }
  catch { throw new Error('STACK_WORKER_DEPENDENCIES_MISSING'); }
  const relayDependencyVersion = dependencyVersion(RELAY_MCP, 'STACK_RELAY_DEPENDENCIES_MISSING');
  const key = loadOrCreateCapabilitySecret({ filePath: args.keyPath });
  const stat = fs.statSync(key.secretPath);
  const doctor = await runWorkerDoctor(args.channel);
  process.stdout.write(`${JSON.stringify({
    status: 'ok',
    node_major: nodeMajor,
    worker_playwright_version: workerDependencyVersion,
    relay_mcp_version: relayDependencyVersion,
    browser: doctor,
    capability_secret_ref: key.secretRef,
    capability_key_mode: (stat.mode & 0o777).toString(8).padStart(3, '0'),
    worker_token_persistence: 'memory_only',
    submit_capability: false,
  }, null, 2)}\n`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    const raw = typeof error?.message === 'string' ? error.message : '';
    const code = /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'STACK_DOCTOR_FAILED';
    process.stderr.write(`UEX_BROWSER_STACK_DOCTOR_ERROR:${code}\n`);
    process.exitCode = 1;
  });
}

export { parseArgs, dependencyVersion, runWorkerDoctor };
