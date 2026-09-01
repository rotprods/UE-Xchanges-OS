import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { chromium } from 'playwright';

const require = createRequire(import.meta.url);
const playwrightPackage = require('playwright/package.json');

export async function runBrowserDoctor({ channel = 'chrome' } = {}) {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'uex-form-doctor-'));
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
  } finally {
    if (context) await context.close();
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}
