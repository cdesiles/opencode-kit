#!/usr/bin/env node
// Inline an artifact's local stylesheets and classic scripts so it can be
// shipped as a single file.
//
//   node inline.mjs "design/Q3 Review.html"
//   node inline.mjs "design/Q3 Review.html" -o "dist/review.html"
//
// Remote URLs are left alone. Local @import chains are followed. Local
// scripts are inlined only when they are classic scripts; module scripts are
// left as references because inlining changes their resolution semantics.

import fs from 'node:fs';
import path from 'node:path';

const argv = process.argv.slice(2);
const outIndex = argv.indexOf('-o');
const outFlag = outIndex !== -1 ? argv[outIndex + 1] : null;
const positional = argv.filter(
  (a, i) => !a.startsWith('-') && !(outIndex !== -1 && i === outIndex + 1),
);
const input = positional[0];

if (!input) {
  console.error('usage: node inline.mjs <file.html> [-o <out.html>]');
  process.exit(2);
}

const inPath = path.resolve(input);
if (!fs.existsSync(inPath)) {
  console.error(`not found: ${inPath}`);
  process.exit(2);
}

const root = path.dirname(inPath);
const base = path.basename(inPath, path.extname(inPath));
const outPath = path.resolve(
  outFlag ?? path.join(root, `${base}.standalone.html`),
);

const inlined = [];
const missing = [];
const skipped = [];
const seenCss = new Set();

const isRemote = (href) => /^(?:[a-z]+:)?\/\//i.test(href) || href.startsWith('data:');

function inlineCssFile(file, depth = 0) {
  if (depth > 8) return '';
  if (seenCss.has(file)) return '';
  seenCss.add(file);

  let css = fs.readFileSync(file, 'utf8');

  css = css.replace(
    /@import\s+(?:url\(\s*)?["']([^"']+)["']\s*\)?\s*;?/gi,
    (statement, href) => {
      if (isRemote(href)) return statement;
      const nested = path.resolve(path.dirname(file), href);
      if (!fs.existsSync(nested)) {
        missing.push(href);
        return statement;
      }
      return inlineCssFile(nested, depth + 1);
    },
  );

  // Make url() references absolute-relative to the stylesheet, since the CSS
  // is moving out of its own directory.
  const dir = path.dirname(file);
  css = css.replace(/url\(\s*["']?([^"')]+)["']?\s*\)/gi, (match, ref) => {
    if (isRemote(ref) || ref.startsWith('/') || ref.startsWith('#')) return match;
    const abs = path.resolve(dir, ref);
    if (!fs.existsSync(abs)) return match;
    const rel = path.relative(root, abs).split(path.sep).join('/');
    return `url("${rel}")`;
  });

  inlined.push(path.relative(process.cwd(), file));
  return css;
}

let html = fs.readFileSync(inPath, 'utf8');

html = html.replace(/<link\b[^>]*>/gi, (tag) => {
  if (!/\brel\s*=\s*["']?[^"'>]*\bstylesheet\b/i.test(tag)) return tag;
  const href = tag.match(/\bhref\s*=\s*["']([^"']+)["']/i)?.[1];
  if (!href || isRemote(href)) return tag;

  const file = path.resolve(root, href);
  if (!fs.existsSync(file)) {
    missing.push(href);
    return tag;
  }

  const css = inlineCssFile(file);
  return css ? `<style>\n${css.trim()}\n</style>` : '';
});

html = html.replace(/<script\b([^>]*)\bsrc\s*=\s*["']([^"']+)["']([^>]*)><\/script>/gi, (tag, before, src, after) => {
  const attrs = `${before} ${after}`;
  if (isRemote(src)) return tag;
  if (/\btype\s*=\s*["']?module/i.test(attrs)) {
    skipped.push(`${src} (module script)`);
    return tag;
  }

  const file = path.resolve(root, src);
  if (!fs.existsSync(file)) {
    missing.push(src);
    return tag;
  }

  const js = fs.readFileSync(file, 'utf8');
  inlined.push(path.relative(process.cwd(), file));
  return `<script${before}>\n${js.trim()}\n</script>`;
});

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, html);

const bytes = (n) => `${(n / 1024).toFixed(1)} kB`;
const before = fs.statSync(inPath).size;
const after = fs.statSync(outPath).size;

console.log(
  JSON.stringify(
    {
      output: outPath,
      inlined,
      skipped,
      missing,
      size: { source: bytes(before), standalone: bytes(after) },
    },
    null,
    2,
  ),
);

if (missing.length) {
  console.error(`\n${missing.length} local reference(s) could not be resolved — the standalone copy is incomplete:`);
  for (const m of missing) console.error(`  - ${m}`);
  process.exitCode = 1;
}
