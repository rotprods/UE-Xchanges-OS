import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateEphemeralWorkerToken, loadOrCreateCapabilitySecret } from './secrets.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORKER_ENTRY = path.resolve(HERE, '../../browser-worker/src/server-cli.mjs');
const RELAY_ENTRY = path.resolve(HERE, '../../browser-relay/src/server.mjs');
const READY_RE = /^UEX_BROWSER_WORKER_READY (http:\/\/127\.0\.0\.1:\d+)$/;
const SYSTEM_ENV_ALLOWLIST = [
  'HOME', 'PATH', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'DISPLAY',
  'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'PLAYWRIGHT_BROWSERS_PATH',
];

function minimalSystemEnv(env) {
  const out = {};
  for (const key of SYSTEM_ENV_ALLOWLIST) {
    if (typeof env[key] === 'string' && env[key]) out[key] = env[key];
  }
  return out;
}

function envBool(value, defaultValue = false) {
  if (value === undefined) return defaultValue;
  if (value === '1' || value === 'true') return true;
  if (value === '0' || value === 'false') return false;
  throw new Error('STACK_BOOLEAN_ENV_INVALID');
}

function safeChildStderr(prefix, chunk) {
  const lines = String(chunk).split(/\r?\n/).filter(Boolean);
  for (const line of lines) {
    const safe = line.replace(/[^A-Za-z0-9_:.\- ]/g, '_').slice(0, 256);
    process.stderr.write(`${prefix}${safe}\n`);
  }
}

function waitForWorkerReady(child, timeoutMs = 30_000) {
  return new Promise((resolve, reject) => {
    let buffer = '';
    let settled = false;
    const timer = setTimeout(() => finish(new Error('STACK_WORKER_READY_TIMEOUT')), timeoutMs);

    function cleanup() {
      clearTimeout(timer);
      child.stdout?.off('data', onData);
      child.off('exit', onExit);
      child.off('error', onError);
    }
    function finish(error, value) {
      if (settled) return;
      settled = true;
      cleanup();
      if (error) reject(error); else resolve(value);
    }
    function onData(chunk) {
      buffer += String(chunk);
      if (buffer.length > 4096) return finish(new Error('STACK_WORKER_READY_OUTPUT_INVALID'));
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() || '';
      for (const line of lines) {
        const match = READY_RE.exec(line.trim());
        if (match) return finish(null, `${match[1]}/`);
      }
    }
    function onExit(code) { finish(new Error(code === 0 ? 'STACK_WORKER_EXITED_EARLY' : 'STACK_WORKER_START_FAILED')); }
    function onError() { finish(new Error('STACK_WORKER_SPAWN_FAILED')); }

    child.stdout?.on('data', onData);
    child.once('exit', onExit);
    child.once('error', onError);
  });
}

async function terminateChild(child, graceMs = 5_000) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  child.kill('SIGTERM');
  await Promise.race([
    new Promise((resolve) => child.once('exit', resolve)),
    new Promise((resolve) => setTimeout(resolve, graceMs)),
  ]);
  if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
}

export async function startBrowserStack({ env = process.env, stdio = process, spawnImpl = spawn } = {}) {
  if (!env || typeof env !== 'object') throw new Error('STACK_ENV_INVALID');
  const systemEnv = minimalSystemEnv(env);
  const workerToken = generateEphemeralWorkerToken();
  const secretState = loadOrCreateCapabilitySecret({ filePath: env.UEX_BROWSER_STACK_CAPABILITY_KEY_PATH });
  const capabilitySecret = secretState.secret.toString('utf8');
  const channel = env.UEX_BROWSER_CHANNEL || 'chrome';
  const headless = envBool(env.UEX_BROWSER_HEADLESS, false);
  const allowLocalPrefill = envBool(env.UEX_BROWSER_STACK_ALLOW_LOCAL_PREFILL, false);

  const workerEnv = {
    ...systemEnv,
    UEX_BROWSER_WORKER_TOKEN: workerToken,
    UEX_BROWSER_WORKER_PORT: '0',
    UEX_BROWSER_CHANNEL: channel,
    UEX_BROWSER_HEADLESS: headless ? '1' : '0',
    UEX_BROWSER_WORKER_ALLOW_LOCAL_PREFILL: allowLocalPrefill ? '1' : '0',
  };

  const worker = spawnImpl(process.execPath, [WORKER_ENTRY], { env: workerEnv, stdio: ['ignore', 'pipe', 'pipe'] });
  worker.stderr?.on('data', (chunk) => safeChildStderr('UEX_STACK_WORKER:', chunk));

  let workerUrl;
  try { workerUrl = await waitForWorkerReady(worker); }
  catch (error) { await terminateChild(worker); throw error; }

  const relayEnv = {
    ...systemEnv,
    UEX_BROWSER_WORKER_URL: workerUrl,
    UEX_BROWSER_WORKER_TOKEN: workerToken,
    UEX_BROWSER_RELAY_CAPABILITY_SECRET: capabilitySecret,
  };
  const relay = spawnImpl(process.execPath, [RELAY_ENTRY], { env: relayEnv, stdio: [stdio.stdin, stdio.stdout, stdio.stderr] });

  let closed = false;
  async function close() {
    if (closed) return;
    closed = true;
    await terminateChild(relay);
    await terminateChild(worker);
  }

  return {
    relay,
    worker,
    safeState: {
      worker_url: workerUrl,
      worker_token_persisted: false,
      inherited_env_keys: Object.keys(systemEnv).sort(),
      capability_secret_ref: secretState.secretRef,
      capability_secret_path: secretState.secretPath,
      channel,
      headless,
      local_prefill_enabled: allowLocalPrefill,
      submit_capability: false,
    },
    close,
  };
}

export { waitForWorkerReady, terminateChild, envBool, minimalSystemEnv };
