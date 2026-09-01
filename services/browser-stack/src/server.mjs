#!/usr/bin/env node
import { startBrowserStack } from './process-manager.mjs';

function childExit(child, name) {
  return new Promise((resolve) => {
    child.once('exit', (code, signal) => resolve({ type: name, code, signal }));
    child.once('error', () => resolve({ type: name, code: null, signal: 'spawn_error' }));
  });
}

function terminationSignal() {
  return new Promise((resolve) => {
    const handler = (signal) => resolve({ type: 'signal', signal });
    process.once('SIGINT', () => handler('SIGINT'));
    process.once('SIGTERM', () => handler('SIGTERM'));
  });
}

async function main() {
  const stack = await startBrowserStack();
  process.stderr.write(`UEX_BROWSER_STACK_READY worker=loopback worker_token_persisted=false local_prefill=${stack.safeState.local_prefill_enabled ? 'enabled' : 'disabled'} submit=absent\n`);

  try {
    const outcome = await Promise.race([
      childExit(stack.relay, 'relay'),
      childExit(stack.worker, 'worker'),
      terminationSignal(),
    ]);

    if (outcome.type === 'worker') {
      process.stderr.write('UEX_BROWSER_STACK_ERROR:WORKER_EXITED_BEFORE_RELAY\n');
      process.exitCode = 1;
    } else if (outcome.type === 'relay') {
      process.exitCode = outcome.code === 0 || outcome.code === null && outcome.signal === 'SIGTERM' ? 0 : 1;
    } else {
      process.exitCode = 0;
    }
  } finally {
    await stack.close();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    const raw = typeof error?.message === 'string' ? error.message : '';
    const code = /^[A-Z0-9_]{3,96}$/.test(raw) ? raw : 'STACK_START_FAILED';
    process.stderr.write(`UEX_BROWSER_STACK_ERROR:${code}\n`);
    process.exitCode = 1;
  });
}

export { childExit };
