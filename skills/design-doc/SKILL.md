---
name: design-doc
description: Build a printable document — report, memo, proposal, letter, one-pager — as one self-contained HTML file that prints cleanly to A4 or Letter. Read before making any document deliverable.
---
# Document

A document is read sequentially and printed on paper. Both facts constrain the layout: a single measure of text, real page breaks, and nothing that depends on hover.

## Decide pagination first

- **Flowing** (default) — one continuous text flow; the browser's print engine splits it across pages. Right for reports, memos, letters, essays, anything whose length you don't control.
- **Fixed pages** — explicit `<section class="page">` blocks, one per sheet. Right when the page count is the design: a one-page resume, a two-sided flyer, a certificate, a poster.

If the person asked for "two pages", they mean fixed. If they asked for "a report", they mean flowing. When it's genuinely unclear, ask — building the wrong one wastes the whole document.

## Geometry

```css
@page { size: A4; margin: 0; }        /* or: size: letter; */
body  { margin: 0; background: #fff; }
.page { width: 210mm; min-height: 297mm; padding: 24mm 22mm; box-sizing: border-box; }
.page + .page { break-before: page; }

@media screen {
  body { background: #e9e7e2; padding: 32px 0; }
  .page { margin: 0 auto 24px; box-shadow: 0 2px 24px rgb(0 0 0 / .12); }
}
```

For flowing documents, drop the fixed `.page` and set `@page { margin: 22mm }` with a `max-width: 66ch` column. Paper size: A4 unless the person is clearly American, Letter if so. If they gave a size, use theirs.

## Type

- Body 11–12pt, line-height 1.5–1.6. Never below 10.5pt for anything that must be read.
- Measure 60–75 characters. Wider than that and the eye loses the line.
- One text family for body, optionally a second for headings. Same pairing as the design system if there is one.
- Headings sized by a scale, with the top-level heading noticeably larger — 28–36pt — not 14pt bold.
- Emphasis via weight and space, not colour alone. A document that prints in greyscale must still read.

## Structure

- Real semantic elements: `h1`–`h3`, `p`, `ul`, `table`, `figure`, `blockquote`. Not styled divs.
- Page numbers via `@page` counters if the document runs past two pages:
  ```css
  @page { @bottom-center { content: counter(page); } }
  ```
  Support is partial — a footnote-style number on each fixed page is a reliable fallback.
- Tables: right-align numbers, left-align text, thin rules rather than full borders, header repeated across breaks with `thead { display: table-header-group }`.
- Avoid `break-inside: avoid` on anything taller than a third of a page.
- Figures get a caption. No caption, no figure.

## Content

Keep the person's words. You may cut and reorder when asked; you may not paraphrase. If a section is empty because they haven't written it, leave a clearly marked gap rather than inventing text.

No stock photography. Use a placeholder box with a monospace note saying what belongs there.

## Finishing

Run `design-verify` at print width and read the screenshot:

```
node ~/.config/opencode/lib/design/verify.mjs "design/Report.html" \
  --width 900 --height 1200 --full --out design/.verify/report.png
```

Check for: text clipped at page edges, a heading orphaned at the bottom of a page, tables splitting badly, and any horizontal overflow — which in print means content lost off the right edge.

Then print to PDF yourself once (Cmd-P, Save as PDF) to confirm the page count and that nothing shifts at real paper size.
