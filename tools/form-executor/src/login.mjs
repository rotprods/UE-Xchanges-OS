import fs from 'node:fs';
import { createInterface } from 'node:readline/promises';
import { chromium } from 'playwright';
import { assertDedicatedProfileDir, normalizeAllowedOrigins, normalizeOrigin } from './guard.mjs';
import { humanLoginNavigationDecision } from './login-guard.mjs';

export async function runHumanLogin({
  url,
  profileDir,
  allowedOrigins,
  channel = 'chrome',
  timeoutMs = 20_000,
}) {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    throw new Error('HUMAN_TTY_REQUIRED');
  }

  const normalizedOrigins = normalizeAllowedOrigins([normalizeOrigin(url), ...allowedOrigins]);
  const dedicatedProfileDir = assertDedicatedProfileDir(profileDir);
  fs.mkdirSync(dedicatedProfileDir, { recursive: true, mode: 0o700 });

  const launchOptions = {
    headless: false,
    viewport: { width: 1440, height: 1000 },
  };
  if (channel !== 'chromium') launchOptions.channel = channel;

  const context = await chromium.launchPersistentContext(dedicatedProfileDir, launchOptions);
  let readline;
  try {
    await context.route('**/*', async (route) => {
      const request = route.request();
      const frame = request.frame();
      const isTopLevelNavigation = request.isNavigationRequest() && frame === frame.page().mainFrame();
      const decision = humanLoginNavigationDecision({
        url: request.url(),
        isTopLevelNavigation,
        allowedOrigins: normalizedOrigins,
      });
      if (decision.action === 'abort') await route.abort('blockedbyclient');
      else await route.continue();
    });

    const page = context.pages()[0] || (await context.newPage());
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: timeoutMs });

    process.stdout.write('UEX_HUMAN_LOGIN_READY\n');
    process.stdout.write('Use the visible browser yourself for login/SSO/2FA. The agent is not reading the page.\n');
    readline = createInterface({ input: process.stdin, output: process.stdout });
    const confirmation = (await readline.question('When authentication is complete, type DONE and press Enter: ')).trim();
    if (confirmation !== 'DONE') throw new Error('HUMAN_LOGIN_NOT_CONFIRMED');
    process.stdout.write('UEX_HUMAN_LOGIN_SESSION_COMPLETE\n');
  } finally {
    readline?.close();
    await context.close();
  }
}
