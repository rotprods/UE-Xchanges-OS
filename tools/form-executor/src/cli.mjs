#!/usr/bin/env node
import { parseInspectArgs } from './args.mjs';

async function main() {
  const options = parseInspectArgs(process.argv.slice(2));
  const { inspectForm } = await import('./inspect.mjs');
  const result = await inspectForm(options);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error) => {
  const errorType = typeof error?.name === 'string' && error.name ? error.name.replace(/[^A-Za-z0-9_.-]/g, '_') : 'Error';
  process.stderr.write(`UEX_FORM_INSPECT_ERROR:${errorType}\n`);
  process.exitCode = 1;
});
