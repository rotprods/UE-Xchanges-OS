#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { canonicalBodyHash, issueRelayCapability } from './capability.mjs';

function parseArgs(argv) {
  const out = { requestId: null, planPath: null, outPath: null, ttl: 120 };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const value = argv[++i];
    if (!value) throw new Error('RELAY_CAPABILITY_ARG_MISSING');
    if (arg === '--request-id') out.requestId = value;
    else if (arg === '--plan') out.planPath = value;
    else if (arg === '--out') out.outPath = value;
    else if (arg === '--ttl') out.ttl = Number(value);
    else throw new Error('RELAY_CAPABILITY_ARG_UNKNOWN');
  }
  if (!out.requestId || !out.planPath || !out.outPath) throw new Error('RELAY_CAPABILITY_ARGS_REQUIRED');
  if (!Number.isInteger(out.ttl) || out.ttl < 1 || out.ttl > 300) throw new Error('RELAY_CAPABILITY_TTL_INVALID');
  return out;
}

function readPlan(planPath) {
  let value;
  try { value = JSON.parse(fs.readFileSync(planPath, 'utf8')); }
  catch { throw new Error('RELAY_CAPABILITY_PLAN_INVALID'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('RELAY_CAPABILITY_PLAN_INVALID');
  return value;
}

function writeSecretFile(outPath, token) {
  const resolved = path.resolve(outPath);
  fs.mkdirSync(path.dirname(resolved), { recursive: true, mode: 0o700 });
  fs.writeFileSync(resolved, `${token}\n`, { mode: 0o600, flag: 'w' });
  fs.chmodSync(resolved, 0o600);
  return resolved;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const secretRaw = process.env.UEX_BROWSER_RELAY_CAPABILITY_SECRET;
  if (typeof secretRaw !== 'string' || secretRaw.length < 32 || /\s/.test(secretRaw)) throw new Error('UEX_BROWSER_RELAY_CAPABILITY_SECRET_INVALID');
  const plan = readPlan(args.planPath);
  const bodyHash = canonicalBodyHash({ plan });
  const token = issueRelayCapability({
    operation: 'prefill-local',
    requestId: args.requestId,
    bodyHash,
    secret: Buffer.from(secretRaw, 'utf8'),
    ttlSeconds: args.ttl,
  });
  const target = writeSecretFile(args.outPath, token);
  process.stdout.write(`${JSON.stringify({ ok: true, operation: 'prefill-local', request_id: args.requestId, body_hash: bodyHash, capability_file: target, token_exported: false })}\n`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    const raw = typeof error?.message === 'string' ? error.message : '';
    const code = /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'RELAY_CAPABILITY_CLI_FAILED';
    process.stderr.write(`UEX_BROWSER_RELAY_CAPABILITY_ERROR:${code}\n`);
    process.exitCode = 1;
  });
}

export { parseArgs, readPlan, writeSecretFile };
