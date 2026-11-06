---
name: design-prototype
description: Build a clickable prototype — app screen, feature flow, onboarding — as one self-contained HTML file with real interactions. Read before prototyping any interface.
---
# Prototype

A prototype exists to be clicked, not admired. Every control does something, every state is reachable, and nothing leads to a dead end.

## Scope

Pick the smallest flow that demonstrates the idea. Three connected screens beat eight disconnected ones. If the ask covers a whole app, ask which flow matters most and build that properly.

State the flow before building: entry point, the two or three decisions the user makes, the outcome. That's the spine.

## Structure

```html
<div id="app"></div>
<script>
  const state = { screen: 'inbox', items: [/* … */] };
  const render = () => { /* paint from state */ };
  const set = (patch) => { Object.assign(state, patch); render(); };
  render();
</script>
```

- One `state` object. Rendering is a pure function of it. No scattered DOM mutation.
- `localStorage` for anything that should survive a reload — never invent a persistence key you didn't write, and never clear keys you didn't set this session.
- Transitions: short, 120–200ms, and disabled under `prefers-reduced-motion`.

## Interaction rules

- **Every clickable thing is clickable.** No `<div>` styled as a button. Use `button` and `a`, keep keyboard focus visible.
- **Hit targets at least 44px.** Icons too.
- **Hover states everywhere**, and a visible focus ring — style `:focus-visible`, not `:focus`.
- **No dead ends.** If a button implies a screen you didn't build, make it do something honest: a toast saying it's not part of this prototype.
- **Loading, empty, error and success states** for anything that pretends to fetch. A prototype that only shows the happy path can't be reviewed.
- **Form validation is visible**: error text next to the field, not an alert.

## Look

Build from the project's design system if there is one. If not, `design-aesthetic` first — a prototype with default browser styling is not reviewable, because the reviewer can't separate the missing design from the missing behaviour.

Don't wrap the screen in a MacBook or iPhone frame unless the person asked for device context. The frame steals attention from the interface and breaks inside a narrow panel.

## Finishing

```
node ~/.config/opencode/lib/design/verify.mjs "design/Prototype.html" --full --out design/.verify/prototype.png
```

Then click through it yourself in a browser if you can, or read the screenshot and trace the state machine by hand. Check that each control has an obvious next state and that no path ends in a blank screen.
