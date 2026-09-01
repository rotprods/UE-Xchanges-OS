import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { expect, test } from '@playwright/test';

const signaturePath = process.env.SIGNATURE_PATH;
if (!signaturePath) throw new Error('SIGNATURE_PATH is required');

const pageUrl = `/${signaturePath}`;
const expectedLinks = [
  'mailto:rot.prods@gmail.com',
  'tel:+34681181152',
  'https://www.instagram.com/travelverses/',
  'https://youtube.com/@rotprods',
  'https://www.instagram.com/rot.prods/',
  'https://www.linkedin.com/in/roberto-ortega-b97666348',
  'https://www.instagram.com/oasismedia.es/',
  'https://wa.me/message/5TBPPKPLAWQAK1',
  'https://www.tiktok.com/@rot.prods',
  'https://linktr.ee/Rot.prods'
].sort();

test('repository policy requires the canonical signature for outreach email', () => {
  const policy = readFileSync(resolve(process.cwd(), '../../AGENTS.md'), 'utf8');

  expect(policy).toContain('OUTREACH_SIGNATURE_GATE_FAIL');
  expect(policy).toContain(signaturePath);
  expect(policy).toContain('must not be sent');
});

test.beforeEach(async ({ context, page }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], {
    origin: 'http://127.0.0.1:4173'
  });
  await page.goto(pageUrl, { waitUntil: 'networkidle' });
});

test('all assets, favicon and exact links are live', async ({ page, request }) => {
  const failures = [];
  page.on('console', message => {
    if (message.type() === 'error') failures.push(`console: ${message.text()}`);
  });
  page.on('requestfailed', req => failures.push(`request: ${req.url()}`));
  await page.reload({ waitUntil: 'networkidle' });

  const images = page.locator('#signature img');
  await expect(images).toHaveCount(9);
  for (let index = 0; index < await images.count(); index += 1) {
    const image = images.nth(index);
    await expect(image).toBeVisible();
    expect(await image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
    const source = await image.getAttribute('src');
    const response = await request.get(source);
    expect(response.status(), source).toBe(200);
    expect(response.headers()['content-type'], source).toMatch(/^image\/(png|jpeg)/);
  }

  const favicon = await page.locator('link[rel="icon"]').getAttribute('href');
  const faviconResponse = await request.get(favicon);
  expect(faviconResponse.status()).toBe(200);
  expect(faviconResponse.headers()['content-type']).toMatch(/^image\/jpeg/);

  const links = (await page.locator('#signature a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')))).sort();
  expect(links).toEqual(expectedLinks);
  expect(links.join(' ')).not.toMatch(/utm_|fbclid|[?&]_t=/i);
  expect(failures).toEqual([]);
});

test('responsive screenshots have no page overflow', async ({ page }, testInfo) => {
  for (const width of [1440, 1024, 768, 430, 390, 375, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.locator('#signature')).toBeVisible();
    const bodyFits = await page.evaluate(() => document.body.scrollWidth <= document.documentElement.clientWidth);
    expect(bodyFits, `body overflow at ${width}px`).toBe(true);
    const canvasFits = await page.locator('.canvas').evaluate(node => node.scrollWidth <= node.clientWidth);
    expect(canvasFits, `signature canvas overflow at ${width}px`).toBe(true);
    await page.screenshot({
      path: testInfo.outputPath(`screenshots/signature-${width}px.png`),
      fullPage: true
    });
  }
});

test('copy button writes rich HTML and pastes the complete signature', async ({ page }) => {
  await page.locator('#copy').click();
  await expect(page.locator('#copy')).toHaveAttribute('data-copy-status', 'copied');
  await expect(page.locator('#copy')).toHaveAttribute('data-copy-method', 'clipboard');

  const clipboard = await page.evaluate(async () => {
    const items = await navigator.clipboard.read();
    const item = items[0];
    return {
      types: item.types,
      html: item.types.includes('text/html') ? await (await item.getType('text/html')).text() : '',
      plain: item.types.includes('text/plain') ? await (await item.getType('text/plain')).text() : ''
    };
  });
  expect(clipboard.types).toEqual(expect.arrayContaining(['text/html', 'text/plain']));
  expect(clipboard.html).toContain('Roberto Gil Ortega');
  expect(clipboard.plain).toContain('Roberto Gil Ortega');

  await page.locator('body').evaluate(body => {
    const target = document.createElement('div');
    target.id = 'paste-target';
    target.contentEditable = 'true';
    body.appendChild(target);
    target.focus();
  });
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+V' : 'Control+V');
  await expect(page.locator('#paste-target')).toContainText('Roberto Gil Ortega');
  await expect(page.locator('#paste-target a')).toHaveCount(10);
  await expect(page.locator('#paste-target img')).toHaveCount(9);
});

test('forced Clipboard API failure uses a real copy fallback', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { write: async () => { throw new Error('forced clipboard failure'); } }
    });
    Object.defineProperty(window, 'ClipboardItem', { configurable: true, value: undefined });
    document.execCommand = command => {
      window.__execCopyCalled = command === 'copy';
      return window.__execCopyCalled;
    };
  });
  await page.goto(pageUrl, { waitUntil: 'networkidle' });
  await page.locator('#copy').click();
  await expect(page.locator('#copy')).toHaveAttribute('data-copy-status', 'copied');
  await expect(page.locator('#copy')).toHaveAttribute('data-copy-method', 'exec-command');
  expect(await page.evaluate(() => window.__execCopyCalled)).toBe(true);
  await context.close();
});
