---
name: design-wireframe
description: Explore quickly with rough wireframes and storyboards instead of polished mockups. Read when the ask is still fuzzy or many ideas need comparing.
---
# Wireframe

Wireframes answer structure questions cheaply. They are not ugly designs — they are deliberately plain, so the person reacts to the arrangement rather than the styling.

## Rules

- **Grayscale only.** Two ink values and a grey box fill. No brand colour, no gradients, no shadows. The moment it looks styled, feedback shifts from "this flow is wrong" to "I don't like the blue".
- **Real copy.** Labels, headings and button text should be the actual words, in monospace or a plain sans. Grey bars standing in for text hide exactly the problem you're testing: whether the words fit.
- **Boxes for images**, with a short note inside about what goes there.
- **Same fidelity everywhere.** One polished panel next to five rough ones makes the polished one look endorsed.
- **Fast and many.** Six to eight frames is a normal first pass. Each should take minutes, not an hour.

## What to show

Pick the axis under question and exhaust it:

- **Flow** — screens in sequence, arrows between them, decision branches labelled.
- **Layout** — one screen, three to five arrangements of the same content.
- **Density** — the same screen at three levels of information density.

Number every frame (`1`, `2`, …) and caption it in one line. Captions are where the thinking lives.

## Output

One page, frames in a wrapping grid, `align-items: start`. Fixed frame width around 380–520px so the whole set can be scanned at once.

```css
.frame { width: 420px; border: 1px solid #c8c8c8; background: #fff; }
.frame__chrome { height: 28px; border-bottom: 1px solid #e2e2e2; }
.frame__body { padding: 16px; font: 13px/1.45 ui-monospace, "SFMono-Regular", monospace; }
```

## Finishing

Verify once, then stop. Wireframes don't need a screenshot review loop — they need a decision from the person. End by asking which frame or combination to take forward.
