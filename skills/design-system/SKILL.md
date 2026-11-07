---
name: design-system
description: Build a design system as two CSS files other apps can copy — tokens.css (custom properties) and components.css (classes built on them) — documented by a specimen page. Read before designing anything that will have more than one screen, and whenever the project has no existing system.
---
# Design system

The system is the artifact. Everything else is built from it. A deliverable that invents its own colours and spacing is a one-off; a deliverable built on tokens can be extended, rebranded and kept consistent.

## Output

Three files, and the split is the point:

- `design/tokens.css` — the tokens, and nothing else. Plain CSS custom properties.
- `design/components.css` — the components, as classes built only from the semantic tokens.
- `design/Design System.html` — the specimen. It `<link>`s both files and documents them. Documentation only: it declares no values of its own.

The two CSS files are the system: they are what other apps copy. The specimen stays in the project as their documentation.

Sections in the specimen, in this order:

1. **Intent** — three sentences: who this is for, what it should feel like, what it explicitly is not.
2. **Colour** — every swatch with its token name, the value it resolves to, and the pairings that pass contrast.
3. **Type** — families, weights, the scale with a named role per step, and a paragraph sample at body size.
4. **Space and shape** — the spacing scale, radii, shadows, borders.
5. **Components** — each one rendered in its real states, next to the markup an app copies.
6. **Rules** — the five or six decisions someone would otherwise get wrong.
7. **Use it in an app** — the version, the two files to copy, the order to load them, the font `<link>`, the root class, and what changed since the last version.

## Tokens

Two layers. Primitives hold raw values; semantic tokens name a job and point at a primitive. Components only ever reference semantic tokens — that's what makes a rebrand a one-line change.

Write this to `design/tokens.css`. It is the only file in the project where a raw value may appear. `acme` stands for the system's prefix (see Sharing):

```css
/* Acme design system 1.0.0 — tokens. Copy this file as is; change it in its source project. */
:root {
  /* primitives */
  --acme-ink-900: oklch(0.22 0.02 260);
  --acme-ink-600: oklch(0.48 0.02 260);
  --acme-paper-50: oklch(0.99 0.005 90);
  --acme-paper-100: oklch(0.96 0.008 90);
  --acme-line-200: oklch(0.90 0.006 90);
  --acme-accent-500: oklch(0.55 0.14 35);
  --acme-accent-600: oklch(0.45 0.15 35);
  --acme-accent-100: oklch(0.94 0.03 35);

  /* semantic */
  --acme-text: var(--acme-ink-900);
  --acme-text-muted: var(--acme-ink-600);
  --acme-bg: var(--acme-paper-50);
  --acme-surface: var(--acme-paper-100);
  --acme-border: var(--acme-line-200);
  --acme-accent: var(--acme-accent-500);
  --acme-accent-hover: var(--acme-accent-600);
  --acme-accent-wash: var(--acme-accent-100);

  /* type */
  --acme-font-display: "Fraunces", Georgia, serif;
  --acme-font-text: "Public Sans", system-ui, sans-serif;
  --acme-step--1: 0.875rem;
  --acme-step-0: 1rem;
  --acme-step-1: 1.25rem;
  --acme-step-2: 1.5625rem;
  --acme-step-3: 1.953rem;
  --acme-step-4: 2.441rem;
  --acme-step-5: 3.052rem;

  /* space, on a 4px base */
  --acme-s-1: 4px;  --acme-s-2: 8px;   --acme-s-3: 12px;  --acme-s-4: 16px;
  --acme-s-5: 24px; --acme-s-6: 32px;  --acme-s-7: 48px;  --acme-s-8: 64px;  --acme-s-9: 96px;

  /* shape and motion */
  --acme-radius-sm: 4px; --acme-radius: 8px; --acme-radius-lg: 16px;
  --acme-border-width: 1px; --acme-ring-width: 2px;
  --acme-shadow-1: 0 1px 2px oklch(0.2 0.02 260 / 0.06);
  --acme-shadow-2: 0 4px 16px oklch(0.2 0.02 260 / 0.08);
  --acme-ease: cubic-bezier(0.2, 0.7, 0.3, 1);
  --acme-dur: 160ms;
}
```

That block is a starting point, not a template to copy blindly. Change the accent hue, the type pairing and the ink warmth to match the brief — but keep the structure.

## Rules for the tokens

- **Contrast is measured, not eyeballed.** Body text 4.5:1 against its actual background; large text and UI borders 3:1. Every swatch page states its pairings.
- **Oklch, not random hex.** Even lightness steps stop palettes looking muddy. Keep chroma roughly constant across a hue family.
- **No unused tokens.** If nothing references a token, delete it.
- **No values outside this file.** A hex, `oklch()` literal, px size or shadow anywhere else is a token that hasn't been named yet.
- **Two type families.** One display, one text. Fallback stacks must be real, not `sans-serif` alone.
- **Scale, don't ad-lib.** If a value isn't on the spacing or type scale, either add it deliberately or use the nearest one.
- **Dark mode only if asked** — but keep colours semantic so adding it later is a token swap, not a rewrite.

## Components

Write them to `design/components.css`, and render each in the specimen in default, hover, focus, active and disabled where they apply:

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

```css
/* Acme design system 1.0.0 — components. Needs tokens.css from the same version, loaded first. */

.acme {
  font-family: var(--acme-font-text);
  font-size: var(--acme-step-0);
  color: var(--acme-text);
  background: var(--acme-bg);
}

.acme-button {
  font: inherit;
  padding: var(--acme-s-2) var(--acme-s-4);
  border: var(--acme-border-width) solid transparent;
  border-radius: var(--acme-radius);
  background: var(--acme-accent);
  color: var(--acme-bg);
  transition: background var(--acme-dur) var(--acme-ease);
}
.acme-button:hover { background: var(--acme-accent-hover); }
.acme-button:focus-visible { outline: var(--acme-ring-width) solid var(--acme-accent); outline-offset: var(--acme-ring-width); }
.acme-button--ghost { background: transparent; color: var(--acme-accent); border-color: var(--acme-border); }
```

## Sharing

Other apps take the system by copying `tokens.css` and `components.css`. The rules below are what lets a copy work anywhere.

- **Prefix everything.** Pick one short name for the system before the first token and put it on every custom property and every class: `--acme-accent`, `.acme-button`. Copies then sit next to an app's own CSS without collisions. The prefix is part of the API; never change it.
- **Plain CSS in both files.** No Tailwind directives, no preprocessor syntax, no nesting, no `@layer` requirement, no `@import` between them. A React app, a static page or another design tool must get identical results from a straight copy.
- **Everything resolves at runtime.** No build-time colour maths, no compiled output.
- **Nothing global in `components.css`.** No resets, no element selectors, nothing on `html` or `body`: dropping the file into an app must not restyle it. Base text styles live on the root class, `.acme`, which an app adds where it wants them.
- **States come from the markup.** Style `:hover`, `:focus-visible`, `:disabled`, `[aria-invalid="true"]`, `[aria-current]` and `[aria-expanded]` rather than state classes an app would have to toggle, so the components work with any framework's HTML.
- **Easy to override.** One class per rule where possible, no IDs, no `!important`.
- **One version for both files.** The first line of each names the system and its version; bump it on every change, in both. Patch for a changed value, minor for a new token or component, major for a removal. Rename by adding the new token and keeping the old one as an alias, `--acme-old: var(--acme-new);`, until the apps have moved; removing the alias is the major bump.
- **Project things stay in the specimen.** Font `<link>` tags, container widths and asset paths are not tokens. The specimen shows the font `<link>` so an app can copy it with the files.

If the target project already has a token file, match its naming before inventing your own. A shared vocabulary is worth more than a better name.

## Specimen page

The specimen is documentation for humans, not a component gallery to be admired. Show the token name next to the swatch. Show each component with the markup an app copies. Note the states that are hard to see (focus rings, disabled).

Link both files, tokens first, and put the root class on `<body>`. Use the system's own type and spacing to lay out the specimen — it's the first proof that the system works.

Read the values from the file instead of typing them, so the documentation can't drift:

```html
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="components.css">
…
<body class="acme">
<figure class="swatch" data-token="--acme-accent-500"></figure>
…
<script>
  for (const el of document.querySelectorAll('[data-token]')) {
    const name = el.dataset.token;
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    el.dataset.value = value;                // printed by CSS
    el.style.setProperty('--swatch', value); // painted by CSS
  }
</script>
```

The swatch paints itself from the token and prints the value the browser resolved. A hand-typed hex is a future lie.

## Finish

Run `design-verify` on the specimen. It lists any colour literal in the specimen or in `components.css`; there should be none. Check that every swatch label is legible, every component is aligned to the same baseline grid, and no sample text overflows its container at 1024px wide.

When the system goes to another app, it copies `tokens.css` and `components.css` unchanged, plus the font `<link>` from the specimen — not the specimen itself. Export a standalone copy of the specimen only if it needs to be read somewhere without the folder.
