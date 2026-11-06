---
name: design-system
description: Build a design system — tokens, type scale, spacing and a component set — as a single self-contained specimen page. Read before designing anything that will have more than one screen, and whenever the project has no existing system.
---
# Design system

The system is the artifact. Everything else is built from it. A deliverable that invents its own colours and spacing is a one-off; a deliverable built on tokens can be extended, rebranded and kept consistent.

## Output

One file: `design/Design System.html`. Sections in this order:

1. **Intent** — three sentences: who this is for, what it should feel like, what it explicitly is not.
2. **Colour** — every swatch with its token name, hex, oklch, and the pairings that pass contrast.
3. **Type** — families, weights, the scale with a named role per step, and a paragraph sample at body size.
4. **Space and shape** — the spacing scale, radii, shadows, borders.
5. **Components** — each one rendered in its real states.
6. **Rules** — the five or six decisions someone would otherwise get wrong.

## Tokens

Two layers. Primitives hold raw values; semantic tokens name a job and point at a primitive. Components only ever reference semantic tokens — that's what makes a rebrand a one-line change.

```css
:root {
  /* primitives */
  --ink-900: oklch(0.22 0.02 260);
  --ink-600: oklch(0.48 0.02 260);
  --paper-50: oklch(0.99 0.005 90);
  --paper-100: oklch(0.96 0.008 90);
  --line-200: oklch(0.90 0.006 90);
  --accent-500: oklch(0.55 0.14 35);
  --accent-600: oklch(0.45 0.15 35);
  --accent-100: oklch(0.94 0.03 35);

  /* semantic */
  --text: var(--ink-900);
  --text-muted: var(--ink-600);
  --bg: var(--paper-50);
  --surface: var(--paper-100);
  --border: var(--line-200);
  --accent: var(--accent-500);
  --accent-hover: var(--accent-600);
  --accent-wash: var(--accent-100);

  /* type */
  --font-display: "Fraunces", Georgia, serif;
  --font-text: "Public Sans", system-ui, sans-serif;
  --step--1: 0.875rem;
  --step-0: 1rem;
  --step-1: 1.25rem;
  --step-2: 1.5625rem;
  --step-3: 1.953rem;
  --step-4: 2.441rem;
  --step-5: 3.052rem;

  /* space, on a 4px base */
  --s-1: 4px;  --s-2: 8px;   --s-3: 12px;  --s-4: 16px;
  --s-5: 24px; --s-6: 32px;  --s-7: 48px;  --s-8: 64px;  --s-9: 96px;

  /* shape and motion */
  --radius-sm: 4px; --radius: 8px; --radius-lg: 16px;
  --shadow-1: 0 1px 2px oklch(0.2 0.02 260 / 0.06);
  --shadow-2: 0 4px 16px oklch(0.2 0.02 260 / 0.08);
  --ease: cubic-bezier(0.2, 0.7, 0.3, 1);
  --dur: 160ms;
}
```

That block is a starting point, not a template to copy blindly. Change the accent hue, the type pairing and the ink warmth to match the brief — but keep the structure.

## Rules for the tokens

- **Contrast is measured, not eyeballed.** Body text 4.5:1 against its actual background; large text and UI borders 3:1. Every swatch page states its pairings.
- **Okclh, not random hex.** Even lightness steps stop palettes looking muddy. Keep chroma roughly constant across a hue family.
- **No unused tokens.** If nothing references a token, delete it.
- **Two type families.** One display, one text. Fallback stacks must be real, not `sans-serif` alone.
- **Scale, don't ad-lib.** If a value isn't on the spacing or type scale, either add it deliberately or use the nearest one.
- **Dark mode only if asked** — but keep colours semantic so adding it later is a token swap, not a rewrite.

## Components

Ship these in the specimen, each in default, hover, focus, active and disabled where they apply:

- Button — primary, secondary, ghost. One size is usually enough.
- Text input and select, with label, help text and error state.
- Card, with a real content example, not "Lorem ipsum".
- Navigation, at both desktop and narrow width.
- Table or list row with a header.
- Badge and tag.
- Modal or dialog.
- Empty state.
- Toast or inline notice.

Each component uses semantic tokens only. If a component needs a value that has no token, that's a gap in the system — add the token, don't hard-code the value.

## Specimen page

The specimen is documentation for humans, not a component gallery to be admired. Show the token name next to the swatch. Show the CSS for the component. Note the states that are hard to see (focus rings, disabled).

Use the system's own type and spacing to lay out the specimen — it's the first proof that the system works.

## Finish

Run `design-verify` on the specimen. Check that every swatch label is legible, every component is aligned to the same baseline grid, and no sample text overflows its container at 1024px wide.
