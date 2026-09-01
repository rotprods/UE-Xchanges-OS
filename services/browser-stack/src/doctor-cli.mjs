#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { defaultCapabilityKeyPath, loadOrCreateCapabilitySecret } from './secrets.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORKER_DOCTOR = path.resolve(HERE, '../../browser-worker/src/doctor-cli.mjs');
const WORKER_PLAYWRIGHT = path.resolve(HERE, '../../browser-worker/node_modules/playwright/package.json');
const RELAY_MCP = path.resolve(HERE, '../../browser-relay/node_modules/@modelcontextprotocol/server/package.json');

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

function doctorChildEnv(env = process.env) {
  const out = {};
  for (const key of ['HOME', 'PATH', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'PLAYWRIGHT_BROWSERS_PATH']) {
    if (typeof env[key] === 'string' && env[key]) out[key] = env[key];
  }
  return out;
}

function runWorkerDoctor(channel) {
  const result = spawnSync(process.execPath, [WORKER_DOCTOR, '--channel', channel], {
    encoding: 'utf8',
    env: doctorChildEnv(),
    maxBuffer: 64 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error('STACK_WORKER_DOCTOR_FAILED');
  if (typeof result.stdout !== 'string' || result.stdout.length > 16 * 1024) throw new Error('STACK_WORKER_DOCTOR_OUTPUT_INVALID');
  let value;
  try { value = JSON.parse(result.stdout); }
  catch { throw new Error('STACK_WORKER_DOCTOR_OUTPUT_INVALID'); }
  const exact = ['status', 'node_major', 'playwright_version', 'browser_channel', 'launch', 'network', 'profile'];
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).sort().join('|') !== exact.sort().join('|')) throw new Error('STACK_WORKER_DOCTOR_OUTPUT_INVALID');
  if (value.status !== 'ok' || value.launch !== 'ok' || value.network !== 'blocked' || value.profile !== 'ephemeral') throw new Error('STACK_WORKER_DOCTOR_FAILED');
  return value;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  if (!Number.isInteger(nodeMajor) || nodeMajor < 20) throw new Error('STACK_NODE_VERSION_UNSUPPORTED');
  const workerDependencyVersion = dependencyVersion(WORKER_PLAYWRIGHT, 'STACK_WORKER_DEPENDENCIES_MISSING');
  const relayDependencyVersion = dependencyVersion(RELAY_MCP, 'STACK_RELAY_DEPENDENCIES_MISSING');
  const key = loadOrCreateCapabilitySecret({ filePath: args.keyPath });
  const stat = fs.statSync(key.secretPath);
  const doctor = runWorkerDoctor(args.channel);
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

export { parseArgs, dependencyVersion, doctorChildEnv, runWorkerDoctor };
