/* Record the real deployed website. No fixture responses or simulated UI. */
const { chromium, expect: assertion } = require('/home/ken/Workspace/sip_and_savor/node_modules/@playwright/test');
const expect = assertion.configure({ timeout: 20000 });
const fs = require('node:fs');
const path = require('node:path');
const ROOT = __dirname;
const WORK = path.join(ROOT, 'work');
const BASE = process.env.SIP_DEMO_URL || 'https://sip-and-savor.vercel.app';
const timeline = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json')));
const shots = {};
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const browserErrors = [];
let epoch;
const now = () => (performance.now() - epoch) / 1000;
async function images(page) {
  await page.waitForFunction(() => [...document.querySelectorAll('main img')].filter(image => {
    const rect = image.getBoundingClientRect(); return rect.top < innerHeight && rect.bottom > 0;
  }).every(image => image.complete), null, { timeout: 15000 }).catch(() => {});
  await pause(400);
}
async function ready(page, articles = false) {
  await expect(page.locator('main h1')).toBeVisible({ timeout: 35000 });
  if (articles) await expect(page.locator('article').first()).toBeVisible({ timeout: 35000 });
  await images(page);
}
async function hold(seconds = 2) { const start = now(); await pause(seconds * 1000); return [start, now()]; }
function watch(page) { page.on('pageerror', error => browserErrors.push(error.message)); }
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/home/ken/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome', args: ['--no-sandbox'] });
  try {
    const desktop = await browser.newContext({ viewport: { width: 1440, height: 780 }, recordVideo: { dir: WORK, size: { width: 1440, height: 780 } }, reducedMotion: 'reduce' });
    await desktop.addInitScript(() => { if (!localStorage.getItem('theme')) localStorage.setItem('theme', 'dark'); });
    epoch = performance.now();
    const page = await desktop.newPage();
    watch(page);
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await ready(page, true);
    await page.screenshot({ path: path.join(WORK, 'home-desktop.png') });
    shots.intro = { source: 'desktop', cuts: [await hold(3)] };

    const typing = now();
    await page.getByRole('searchbox', { name: 'Search recipes', exact: true }).pressSequentially('apple', { delay: 115 });
    await pause(200);
    const typed = now();
    await page.locator('main').getByRole('button', { name: 'Search', exact: true }).click();
    await expect(page).toHaveURL(/q=apple/);
    await ready(page, true);
    await page.screenshot({ path: path.join(WORK, 'search-desktop.png') });
    shots.search = { source: 'desktop', cuts: [[typing, typed], await hold(4.4)] };

    await page.locator('main').getByRole('button', { name: 'Meals', exact: true }).click();
    await page.getByRole('button', { name: 'Reset search and filters', exact: true }).click();
    await ready(page, true);
    await page.getByRole('combobox', { name: 'Category', exact: true }).selectOption('Seafood');
    await ready(page, true);
    const seafood = await hold(3);
    await page.getByRole('combobox', { name: 'Cuisine', exact: true }).selectOption('Italian');
    await ready(page, true);
    await page.screenshot({ path: path.join(WORK, 'browse-desktop.png') });
    shots.browse = { source: 'desktop', cuts: [seafood, await hold(3.5)] };

    await page.goto(BASE + '/meal/52772', { waitUntil: 'domcontentloaded' });
    await ready(page);
    await page.screenshot({ path: path.join(WORK, 'meal-desktop.png') });
    const mealHero = await hold(1.8);
    const ingredientHeader = page.getByRole('button', { name: /^Ingredients/ });
    const ingredientId = await ingredientHeader.getAttribute('aria-controls');
    await page.locator('[id="' + ingredientId + '"]').getByRole('button').first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    const ingredient = await hold(1.8);
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: /Save .* to favorites/ }).first().click();
    const instructions = page.getByRole('button', { name: /^Instructions/ });
    await instructions.scrollIntoViewIfNeeded();
    await page.evaluate(() => scrollBy({ top: -180, behavior: 'smooth' }));
    await pause(650);
    await page.screenshot({ path: path.join(WORK, 'instructions-desktop.png') });
    shots.meal = { source: 'desktop', cuts: [mealHero, ingredient, await hold(3.8)] };

    await page.goto(BASE + '/cocktail/11007', { waitUntil: 'domcontentloaded' });
    await ready(page);
    await page.screenshot({ path: path.join(WORK, 'cocktail-desktop.png') });
    const drinkHero = await hold(2.8);
    await page.getByRole('button', { name: /Save .* to favorites/ }).first().click();
    const scrollDrink = now();
    await page.evaluate(() => scrollBy({ top: 390, behavior: 'smooth' }));
    await pause(3600);
    shots.cocktail = { source: 'desktop', cuts: [drinkHero, [scrollDrink, now()]] };
    const storageState = await desktop.storageState();
    const desktopVideo = await page.video().path();
    await desktop.close();
    fs.renameSync(desktopVideo, path.join(WORK, 'desktop.webm'));
    console.log('Desktop captured');

    const mobile = await browser.newContext({ viewport: { width: 390, height: 780 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1, storageState, recordVideo: { dir: WORK, size: { width: 390, height: 780 } }, reducedMotion: 'reduce' });
    epoch = performance.now();
    const phone = await mobile.newPage();
    watch(phone);
    await phone.goto(BASE, { waitUntil: 'domcontentloaded' });
    await ready(phone, true);
    await phone.screenshot({ path: path.join(WORK, 'home-phone.png') });
    await phone.goto(BASE + '/meal/52772', { waitUntil: 'domcontentloaded' });
    await ready(phone);
    await phone.screenshot({ path: path.join(WORK, 'meal-phone.png') });
    const phoneTop = await hold(2.3);
    const phoneScroll = now();
    await phone.evaluate(() => scrollBy({ top: 430, behavior: 'smooth' }));
    await pause(1900);
    await phone.evaluate(() => scrollBy({ top: 330, behavior: 'smooth' }));
    await pause(2900);
    shots.mobile = { source: 'phone', cuts: [phoneTop, [phoneScroll, now()]] };

    await phone.getByRole('button', { name: 'Toggle menu', exact: true }).click();
    await phone.getByRole('link', { name: 'Saved', exact: true }).click();
    await expect(phone).toHaveURL(/favorites/);
    await expect(phone.locator('article')).toHaveCount(2);
    await images(phone);
    await phone.screenshot({ path: path.join(WORK, 'saved-phone.png') });
    const savedOverview = await hold(2.8);
    const savedFilter = now();
    await phone.getByRole('searchbox', { name: 'Find a saved recipe' }).pressSequentially('teriyaki', { delay: 90 });
    await pause(2100);
    shots.saved = { source: 'phone', cuts: [savedOverview, [savedFilter, now()]] };
    await phone.getByRole('searchbox', { name: 'Find a saved recipe' }).fill('');
    await phone.goto(BASE + '/cocktail/11007', { waitUntil: 'domcontentloaded' });
    await ready(phone);
    await phone.screenshot({ path: path.join(WORK, 'cocktail-phone.png') });
    const phoneVideo = await phone.video().path();
    await mobile.close();
    fs.renameSync(phoneVideo, path.join(WORK, 'phone.webm'));
    const capture = { base_url: BASE, app_commit: 'ccc882e', browser_errors: browserErrors, shots, desktop: { width: 1440, height: 780 }, phone: { width: 390, height: 780 }, notes: 'Actual deployed UI and public APIs. Cuts omit loading waits. No mocked responses, click rings, touch markers, or generated imagery.' };
    fs.writeFileSync(path.join(ROOT, 'capture.json'), JSON.stringify(capture, null, 2) + '\n');
    expect(browserErrors).toEqual([]);
    console.log('Desktop and phone captures ready.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
