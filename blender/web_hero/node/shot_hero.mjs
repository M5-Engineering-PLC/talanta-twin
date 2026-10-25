// Screenshot the app once hero mode is on (headless Chromium, software GL).
// Run: node blender/web_hero/node/shot_hero.mjs "http://127.0.0.1:5199/?hero" out.png [extra_wait_ms] [key=<k>]
// key=<k> presses that key once hero mode is on (the view chips: 2 = lead06 / camera L06, 3 = lead07 / camera L07).
// with the app served by 'npx vite --port 5199 --host 127.0.0.1' from app/. Software rendering takes about 40 s to
// load and up to a few minutes per frame, hence the long screenshot timeout.
import { chromium } from '/opt/node-tools/node_modules/playwright-core/index.mjs';
const [url, out, waitMs] = process.argv.slice(2).filter((a) => !a.startsWith('key='));
const key = (process.argv.find((a) => a.startsWith('key=')) || '').slice(4);
// The browser comes from Playwright's own install (PLAYWRIGHT_BROWSERS_PATH); PW_CHROME=<path> overrides it.
const b = await chromium.launch({ executablePath: process.env.PW_CHROME || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
let on = false;
p.on('console', (m) => { const t = m.text(); if (/hero|panorama|error|warn/i.test(t)) console.log('[page]', t.slice(0, 300)); if (t.includes('hero mode on')) on = true; });
p.on('pageerror', (e) => console.log('[pageerror]', e.message));
await p.goto(url, { timeout: 120000 });
const t0 = Date.now();
while (!on && Date.now() - t0 < 400000) await p.waitForTimeout(2000);
console.log('hero on:', on, (Date.now() - t0) / 1000, 's');
if (key) { await p.mouse.move(960, 540); await p.keyboard.press(key); console.log('key', key); }
await p.waitForTimeout(+waitMs || 20000);
await p.screenshot({ path: out, timeout: 420000 });
await b.close();
