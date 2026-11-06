---
name: design-options
description: Present two or three distinct design directions for one ask, as separate rendered candidates the person can pick between. Read when asked for options, variations, or "show me a few ways".
---
# Options

Options are decisions, not decoration. Two candidates that differ only in accent colour are one option with a bug.

## How many

Two or three. One is not a choice; four is a survey nobody answers. If the ask has several independent axes (layout *and* density *and* tone), pick the axis that matters most and vary only that — otherwise the person can't tell which difference they're reacting to.

## Make them genuinely different

Name the difference in one line each before building:

> **1a — Editorial.** Big serif headline, asymmetric two-column, generous margins. Reads as a report.
> **1b — Product.** Tighter grotesque, card-dense, screenshot-led. Reads as a landing page.

Same content in both. Different argument about what the thing is.

## Presentation

One page, one file, candidates side by side or stacked in a wrapping row:

```html
<div style="display:flex; flex-wrap:wrap; gap:48px">
  <section id="1a" style="flex:1 1 520px">
    <h2>1a — Editorial</h2>
    <!-- candidate -->
  </section>
  <section id="1b" style="flex:1 1 520px">
    <h2>1b — Product</h2>
    <!-- candidate -->
  </section>
</div>
```

- Stable ids (`1a`, `1b`, `2a`), visible as labels, so the person can say "1b".
- **Ids like `1a` are anchors, not CSS selectors.** `#1a` is invalid CSS — an identifier can't start with a digit — and the browser silently drops the entire rule. Style candidates with a class (`.opt-a`) and keep `id="1a"` for linking. Same trap in `querySelector('#1a')`.
- Content is identical across candidates. Scale is identical. Only the design decision varies.
- No "recommended" badge unless they asked you to recommend one — then put the reason in a sentence, not a badge.

## Ask, then converge

Present them, then ask which direction to take with the `question` tool. Don't merge the two into a compromise nobody chose, and don't continue building all of them.

When a second round is wanted, add it as new candidates rather than editing the first round — the person may still refer back.

## Finishing

```
node ~/.config/opencode/lib/design/verify.mjs "design/Options.html" --full --out design/.verify/options.png
```

Check that each candidate holds up at its own width and that the page doesn't overwhelm the preview panel on a laptop screen.
