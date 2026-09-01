#!/usr/bin/env node
import { parseInspectArgs } from './args.mjs';

async function main() {
  const options = parseInspectArgs(process.argv.slice(2));
  const { inspectForm } = await import('./inspect.mjs');
  const result = await inspectForm(options);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
