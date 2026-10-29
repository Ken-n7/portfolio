/* Real Django pages, local SQLite sample data, no production connections. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/home/ken/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const ROOT = __dirname;
const OUT = path.join(ROOT, 'work', 'capture');
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH || '/home/ken/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome', args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 820 }, deviceScaleFactor: 1.5, reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    // The capture can only contact this isolated app.
    await page.route('**/*', route => route.request().url().startsWith('http://127.0.0.1:4195/') ? route.continue() : route.abort());
    await page.goto('http://127.0.0.1:4195/login/');
    await page.locator('[name=username]').fill('admin_user');
    await page.locator('[name=password]').fill('efp2025');
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await page.waitForURL('http://127.0.0.1:4195/');
    const pages = [['dashboard','/'],['batches','/batches/'],['movements','/movements/'],['reconciliation','/reconciliation/'],['resolve','/reconciliation/3/resolve/'],['summary','/sales-summary/'],['reports','/reports/'],['audit','/audit/'],['users','/users/']];
    const manifest = [];
    for (const [id, url] of pages) {
      const response = await page.goto('http://127.0.0.1:4195' + url, { waitUntil: 'networkidle' });
      if (response.status() !== 200) throw new Error(`${id}: HTTP ${response.status()}`);
      await page.evaluate(() => { for (const chart of Object.values(window.Chart?.instances || {})) { chart.options.animation = false; chart.update('none'); } });
      await page.waitForTimeout(250);
      await page.screenshot({ path: path.join(OUT, id + '.png') });
      manifest.push({ id, url, title: await page.title(), viewport: [1440,820] });
      console.log('Captured', id);
    }
    fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify({ pages: manifest, errors }, null, 2));
    if (errors.length) throw new Error(errors.join('\n'));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
