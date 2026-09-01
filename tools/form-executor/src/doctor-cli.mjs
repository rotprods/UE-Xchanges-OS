#!/usr/bin/env node
import { parseDoctorArgs } from './doctor-args.mjs';

async function main() {
  const options = parseDoctorArgs(process.argv.slice(2));
  const { runBrowserDoctor } = await import('./doctor.mjs');
  const result = await runBrowserDoctor(options);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error) => {
  const errorType = typeof error?.name === 'string' && error.name ? error.name.replace(/[^A-Za-z0-9_.-]/g, '_') : 'Error';
  process.stderr.write(`UEX_FORM_BROWSER_DOCTOR_ERROR:${errorType}\n`);
  process.exitCode = 1;
});
