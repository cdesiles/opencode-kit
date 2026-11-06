---
name: design-verify
description: Check a design artifact in a real browser before handing it over — console errors, broken assets, overflow, then a visual review of the screenshot. Read before delivering anything.
---
# Verify

The script catches mechanical failures. The screenshot is where you catch design failures. Do both, every time.

## Run it

```
node ~/.config/opencode/lib/design/verify.mjs "design/Foo.html" --full --out design/.verify/foo.png
```

Common variants:

| Case | Flags |
|---|---|
| Deck, one shot per slide | `--each "section" --step --each-out design/.verify/deck` |
| Document, print width | `--width 900 --height 1200 --full` |
| Poster or fixed canvas | `--width 1080 --height 1350 --full` |
| Narrow panel check | `--width 900` |
| Slow animation to settle | `--settle 2000` |

It serves the file on a throwaway localhost port, loads it headless, and prints JSON plus a summary on stderr. Exit code 1 means something is wrong.

## Read the output

- **`errors`** — console errors and uncaught exceptions. Usually a script referencing a missing element. Fix the cause, don't silence it.
- **`failedRequests`** — missing fonts, images, sibling files. A missing font silently falls back and the whole type decision is lost, so this one matters more than it looks.
- **`horizontalScroll`** — the page is wider than the viewport. On screen that's a scrollbar nobody wants; in print it means content is cut off the right edge. Find the element from the `overflowing` list.
- **`metrics.fontFamilies`** — what actually rendered. If the display face isn't there, the font didn't load and you're reviewing the fallback.
- **`images[].loaded: false`** — broken asset or a wrong relative path.
- **`metrics.nodeCount`** — a sanity check, not a target.

## Then look at the screenshot

Open the file. Judge, in this order:

1. **Hierarchy** — does the eye land on the headline first, the supporting detail second? Squint: if everything has equal weight, there is no hierarchy.
2. **Spacing** — consistent rhythm, and enough of it. Uneven gaps between groups are the most common tell of an unconsidered layout.
3. **Alignment** — anything that should share a left edge and doesn't.
4. **Clipping and overlap** — text touching or crossing a boundary, an element escaping its container.
5. **Contrast** — muted grey on light grey is the default failure. Check the actual values, don't trust the screenshot rendering.
6. **Content** — no filler, no placeholder text left behind, no numbers you invented.

## Fix and re-run

Fix from the error text directly; don't re-read the whole file to find the line. Re-run after each substantive change. Three rounds is the limit — after that, hand it over with an honest note about what's still wrong.

Never say a design is done because the script exited 0. The script doesn't know whether it looks good.
