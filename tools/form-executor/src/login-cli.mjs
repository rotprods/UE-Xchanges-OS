#!/usr/bin/env node
import { parseHumanLoginArgs } from './login-args.mjs';

async function main() {
  const options = parseHumanLoginArgs(process.argv.slice(2));
  const { runHumanLogin } = await import('./login.mjs');
  await runHumanLogin(options);
}

main().catch((error) => {
  const errorType = typeof error?.name === 'string' && error.name ? error.name.replace(/[^A-Za-z0-9_.-]/g, '_') : 'Error';
  process.stderr.write(`UEX_HUMAN_LOGIN_ERROR:${errorType}\n`);
  process.exitCode = 1;
});
