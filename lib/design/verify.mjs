#!/usr/bin/env node
// Headless verification for design artifacts.
//
//   node verify.mjs <file.html | dir> [options]
//
// Serves the target over a throwaway localhost server, loads it in headless
// Chromium, and reports what a browser actually sees: console errors, failed
// requests, horizontal overflow, broken images, fonts, and a screenshot.
//
// Options:
//   --out <path.png>     screenshot path (default: ./verify.png)
//   --width <px>         viewport width (default 1440)
//   --height <px>        viewport height (default 900)
//   --full               full-page screenshot (default: viewport only)
//   --each <selector>    also screenshot every match, e.g. --each "section"
//   --step               with --each: step through frames by keypress instead
//                        of element capture (use for scaled decks)
//   --key <key>          key pressed in --step mode (default: ArrowRight)
//   --step-wait <ms>     pause after each keypress (default: 500)
//   --each-out <dir>     directory for --each shots (default: ./slides)
//   --settle <ms>        extra wait after load before measuring (default 600)
//   --scale <n>          device scale factor (default 2)
//   --headed             show the browser window instead of running headless
//   --hold               with --headed: keep the window open until closed
//   --quiet              suppress the human summary (JSON only)
//
// Exit code 1 when the page has errors, failed requests, or horizontal
// overflow. 0 otherwise. Always prints JSON on stdout.

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const argv = process.argv.slice(2);
const positional = argv.filter((a) => !a.startsWith('--'));
const after = (name) => {
  const i = argv.indexOf(`--${name}`);
  if (i === -1 || i + 1 >= argv.length || argv[i + 1].startsWith('--')) return null;
  return argv[i + 1];
};
const has = (name) => argv.includes(`--${name}`);

const target = positional[0];
if (!target) {
  console.error('usage: node verify.mjs <file.html | dir> [--out shot.png] [--full] [--each selector]');
  process.exit(2);
}

const abs = path.resolve(target);
if (!fs.existsSync(abs)) {
  console.error(`not found: ${abs}`);
  process.exit(2);
}

const root = fs.statSync(abs).isDirectory() ? abs : path.dirname(abs);
const entry = fs.statSync(abs).isDirectory() ? '/index.html' : `/${path.basename(abs)}`;
const outPath = path.resolve(after('out') ?? 'verify.png');
const eachDir = path.resolve(after('each-out') ?? 'slides');
const width = Number(after('width') ?? 1440);
const height = Number(after('height') ?? 900);
const settle = Number(after('settle') ?? 600);
const scale = Number(after('scale') ?? 2);
const eachSelector = after('each');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.gif': 'image/gif',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
  '.otf': 'font/otf',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.wasm': 'application/wasm',
};

function startServer(dir) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
      let file = path.join(dir, urlPath);
      if (!file.startsWith(dir)) return res.writeHead(403).end('forbidden');
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      fs.readFile(file, (err, buf) => {
        if (err) return res.writeHead(404).end('not found');
        res.writeHead(200, {
          'content-type': MIME[path.extname(file).toLowerCase()] ?? 'application/octet-stream',
          'cache-control': 'no-store',
        });
        res.end(buf);
      });
    });
    server.listen(0, '127.0.0.1', () => resolve({ server, port: server.address().port }));
  });
}

const { server, port } = await startServer(root);
const url = `http://127.0.0.1:${port}${entry}`;

const errors = [];
const warnings = [];
const failedRequests = [];
let browser;

try {
  browser = await chromium.launch({ headless: !has('headed') });
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: scale,
    reducedMotion: 'no-preference',
  });
  const page = await context.newPage();

  page.on('console', (msg) => {
    const type = msg.type();
    if (type === 'error') errors.push(msg.text());
    else if (type === 'warning') warnings.push(msg.text());
  });
  page.on('pageerror', (err) => errors.push(`uncaught: ${err.message}`));
  page.on('requestfailed', (req) => {
    failedRequests.push(`${req.url()} — ${req.failure()?.errorText ?? 'failed'}`);
  });

  let navigationError = null;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  } catch (err) {
    navigationError = err.message;
  }

  await page.evaluate(() => document.fonts?.ready?.catch?.(() => {}));
  await page.waitForTimeout(settle);

  const metrics = await page.evaluate(() => {
    const de = document.documentElement;
    const hScroll = de.scrollWidth > window.innerWidth + 1;
    const overflowing = [];
    // Only worth listing when the document itself scrolls sideways; otherwise
    // fixed-size stages and scaled layouts produce noise, not findings.
    if (hScroll) {
      for (const el of document.querySelectorAll('body *')) {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) continue;
        const cs = getComputedStyle(el);
        if (cs.position === 'fixed' || cs.position === 'absolute') continue;
        if (rect.right > window.innerWidth + 1 || rect.left < -1) {
          overflowing.push({
            tag: el.tagName.toLowerCase(),
            cls: typeof el.className === 'string' ? el.className.slice(0, 48) : '',
            left: Math.round(rect.left),
            right: Math.round(rect.right),
          });
        }
      }
    }
    const images = [...document.images].map((img) => ({
      src: (img.currentSrc || img.src || '').split('/').pop(),
      loaded: img.naturalWidth > 0,
      alt: img.hasAttribute('alt'),
    }));
    const fontFamilies = [...new Set(
      [...document.querySelectorAll('body *')]
        .slice(0, 400)
        .map((el) => getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim())
        .filter(Boolean),
    )];
    return {
      title: document.title || null,
      viewportWidth: window.innerWidth,
      documentWidth: de.scrollWidth,
      documentHeight: de.scrollHeight,
      horizontalScroll: hScroll,
      bodyBackground: getComputedStyle(document.body).backgroundColor,
      fontFamilies,
      images,
      overflowing: overflowing.slice(0, 10),
      overflowCount: overflowing.length,
      nodeCount: document.querySelectorAll('*').length,
    };
  });

  // Token discipline: only meaningful once the project has a token file.
  const notes = [];
  const tokenFile = [
    path.join(root, 'tokens.css'),
    path.join(path.dirname(root), 'tokens.css'),
  ].find((candidate) => fs.existsSync(candidate));

  if (tokenFile && !/\.standalone\.html$/i.test(abs)) {
    const css = await page.evaluate(() => ({
      links: [...document.querySelectorAll('link[rel~="stylesheet"]')].map((l) => l.getAttribute('href') ?? ''),
      inline: [
        ...[...document.querySelectorAll('style')].map((s) => s.textContent ?? ''),
        ...[...document.querySelectorAll('[style]')].map((e) => e.getAttribute('style') ?? ''),
      ].join('\n'),
    }));
    if (!css.links.some((href) => /(^|\/)tokens\.css(\?|#|$)/.test(href))) {
      notes.push(`tokens.css exists but this page does not link it`);
    }

    // Colour values belong in tokens.css alone: look for them in all the other CSS the page uses.
    const sources = [['this page', css.inline]];
    for (const href of css.links) {
      const file = href.split(/[?#]/)[0];
      if (!file || /^([a-z]+:)?\/\//i.test(file) || file.startsWith('data:') || path.basename(file) === 'tokens.css') continue;
      let local;
      try {
        local = path.resolve(root, decodeURIComponent(file));
      } catch {
        continue;
      }
      if (fs.existsSync(local)) sources.push([path.basename(local), fs.readFileSync(local, 'utf8')]);
    }
    const literal = /#[0-9a-f]{3,8}\b|\b(?:oklch|oklab|lab|lch|rgba?|hsla?|hwb|color)\([^)]*\)/gi;
    const found = sources.flatMap(([where, text]) =>
      [...new Set(text.replace(/\/\*[\s\S]*?\*\//g, '').match(literal) ?? [])].map((value) => `${value} in ${where}`),
    );
    if (found.length) {
      notes.push(`${found.length} colour literal(s) outside tokens.css: ${found.slice(0, 5).join(', ')}`);
    }
  }

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  await page.screenshot({ path: outPath, fullPage: has('full') });

  const eachShots = [];
  if (eachSelector) {
    fs.mkdirSync(eachDir, { recursive: true });
    const count = await page.locator(eachSelector).count();

    if (has('step')) {
      // Step through frames by keypress: captures what the presenter sees,
      // and works when slides are clipped or transformed out of view.
      const key = after('key') ?? 'ArrowRight';
      const stepWait = Number(after('step-wait') ?? 500);
      await page.mouse.click(1, 1);
      for (let i = 0; i < count; i += 1) {
        const shot = path.join(eachDir, `${String(i + 1).padStart(2, '0')}.png`);
        await page.screenshot({ path: shot });
        eachShots.push(shot);
        if (i < count - 1) {
          await page.keyboard.press(key);
          await page.waitForTimeout(stepWait);
        }
      }
    } else {
      for (let i = 0; i < count; i += 1) {
        const locator = page.locator(eachSelector).nth(i);
        const name = `${String(i + 1).padStart(2, '0')}.png`;
        const shot = path.join(eachDir, name);
        try {
          await locator.scrollIntoViewIfNeeded({ timeout: 2000 });
          await locator.screenshot({ path: shot, timeout: 5000 });
          eachShots.push(shot);
        } catch {
          eachShots.push(`(skipped ${i + 1}: not renderable — try --step)`);
        }
      }
    }
  }

  const report = {
    ok: errors.length === 0 && failedRequests.length === 0 && !metrics.horizontalScroll,
    url,
    screenshot: outPath,
    ...(eachShots.length ? { frames: eachShots } : {}),
    ...(navigationError ? { navigationError } : {}),
    errors,
    warnings: warnings.slice(0, 10),
    failedRequests,
    ...(notes.length ? { notes } : {}),
    metrics,
  };

  console.log(JSON.stringify(report, null, 2));

  if (!has('quiet')) {
    const lines = [];
    lines.push(`page      ${metrics.title ?? '(untitled)'}  ${metrics.viewportWidth}×${metrics.documentHeight}`);
    lines.push(`screenshot ${outPath}${eachShots.length ? `  +${eachShots.length} frames in ${eachDir}` : ''}`);
    lines.push(`nodes     ${metrics.nodeCount}`);
    lines.push(errors.length ? `errors    ${errors.length}` : 'errors    none');
    if (errors.length) for (const e of errors.slice(0, 8)) lines.push(`  - ${e}`);
    if (failedRequests.length) {
      lines.push(`requests  ${failedRequests.length} failed`);
      for (const r of failedRequests.slice(0, 8)) lines.push(`  - ${r}`);
    }
    if (metrics.horizontalScroll) {
      lines.push(`overflow  page is ${metrics.documentWidth}px wide in a ${metrics.viewportWidth}px viewport`);
      for (const o of metrics.overflowing.slice(0, 6)) {
        lines.push(`  - <${o.tag}${o.cls ? ` class="${o.cls}"` : ''}> ${o.left}→${o.right}`);
      }
    }
    if (metrics.images.some((i) => !i.loaded)) {
      lines.push('images    broken');
      for (const i of metrics.images.filter((x) => !x.loaded).slice(0, 8)) lines.push(`  - ${i.src}`);
    }
    if (notes.length) {
      lines.push('tokens    check');
      for (const n of notes) lines.push(`  - ${n}`);
    }
    console.error(lines.join('\n'));
  }

  if (has('hold') && has('headed')) {
    // Leave the window usable; the run ends when the person closes it.
    await new Promise((resolve) => {
      browser.once('disconnected', resolve);
    });
  } else {
    await context.close();
  }

  process.exitCode = report.ok ? 0 : 1;
} catch (err) {
  console.log(JSON.stringify({ ok: false, error: err.message }, null, 2));
  console.error(`verify failed: ${err.message}`);
  process.exitCode = 2;
} finally {
  await browser?.close().catch(() => {});
  server.close();
}
