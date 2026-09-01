#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { canonicalBodyHash, issueRelayCapability } from '../../browser-relay/src/capability.mjs';
import { defaultCapabilityKeyPath, loadOrCreateCapabilitySecret } from './secrets.mjs';

function activationRoot(homeDir = os.homedir()) {
  return path.resolve(homeDir, '.uexchanges', 'activation');
}

function assertActivationOutput(filePath, homeDir = os.homedir()) {
  const root = activationRoot(homeDir);
  const resolved = path.resolve(filePath);
  if (resolved !== root && !resolved.startsWith(`${root}${path.sep}`)) throw new Error('STACK_CAPABILITY_OUTPUT_OUTSIDE_ACTIVATION_ROOT');
  return resolved;
}

function parseArgs(argv, homeDir = os.homedir()) {
  const out = {
    requestId: null,
    planPath: null,
    outPath: path.join(activationRoot(homeDir), 'prefill.cap'),
    keyPath: defaultCapabilityKeyPath(homeDir),
    ttl: 120,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const value = argv[++i];
    if (!value) throw new Error('STACK_CAPABILITY_ARG_MISSING');
    if (arg === '--request-id') out.requestId = value;
    else if (arg === '--plan') out.planPath = value;
    else if (arg === '--out') out.outPath = value;
    else if (arg === '--key-file') out.keyPath = value;
    else if (arg === '--ttl') out.ttl = Number(value);
    else throw new Error('STACK_CAPABILITY_ARG_UNKNOWN');
  }
  if (!out.requestId || !out.planPath) throw new Error('STACK_CAPABILITY_ARGS_REQUIRED');
  if (!/^[A-Za-z0-9._:-]{8,128}$/.test(out.requestId)) throw new Error('STACK_CAPABILITY_REQUEST_ID_INVALID');
  if (!Number.isInteger(out.ttl) || out.ttl < 1 || out.ttl > 300) throw new Error('STACK_CAPABILITY_TTL_INVALID');
  out.outPath = assertActivationOutput(out.outPath, homeDir);
  return out;
}

function loadPlan(planPath) {
  let value;
  try { value = JSON.parse(fs.readFileSync(planPath, 'utf8')); }
  catch { throw new Error('STACK_CAPABILITY_PLAN_INVALID'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('STACK_CAPABILITY_PLAN_INVALID');
  for (const key of ['application_id', 'canonical_form_url', 'provider', 'form_fingerprint', 'validation_signature']) {
    if (typeof value[key] !== 'string' || !value[key]) throw new Error('STACK_CAPABILITY_PLAN_IDENTITY_INVALID');
  }
  return value;
}

function writeCapability(filePath, token) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true, mode: 0o700 });
  fs.writeFileSync(filePath, `${token}\n`, { mode: 0o600, flag: 'w' });
  fs.chmodSync(filePath, 0o600);
  return filePath;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const plan = loadPlan(args.planPath);
  const key = loadOrCreateCapabilitySecret({ filePath: args.keyPath });
  const bodyHash = canonicalBodyHash({ plan });
  const token = issueRelayCapability({
    operation: 'prefill-local',
    requestId: args.requestId,
    bodyHash,
    secret: key.secret,
    ttlSeconds: args.ttl,
  });
  const target = writeCapability(args.outPath, token);
  process.stdout.write(`${JSON.stringify({ ok: true, operation: 'prefill-local', request_id: args.requestId, body_hash: bodyHash, capability_file: target, secret_ref: key.secretRef, token_exported: false })}\n`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    const raw = typeof error?.message === 'string' ? error.message : '';
    const code = /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'STACK_CAPABILITY_FAILED';
    process.stderr.write(`UEX_BROWSER_STACK_CAPABILITY_ERROR:${code}\n`);
    process.exitCode = 1;
  });
}

export { activationRoot, assertActivationOutput, parseArgs, loadPlan, writeCapability };
