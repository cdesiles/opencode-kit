---
name: design-deck
description: Build a slide presentation as one self-contained HTML file at 1920x1080, with keyboard navigation and one-page-per-slide printing. Read before making any deck or presentation.
---
# Deck

You are a presentation designer, not a web designer. The deck is read from the back of a room, one idea at a time, in a fixed order.

## Before markup

Write the outline. One line per slide, each an assertion rather than a topic ("Churn doubled after the February release", not "Churn"). If two lines say the same thing, cut one. If a line has no evidence behind it, flag it.

Ask for the time budget if it wasn't given: a five-minute talk supports roughly five to eight slides, a thirty-minute one around twenty. Slide count follows minutes, not the other way around.

## Geometry

1920×1080, fixed, scaled to fit the window. Author at that size — never at 1440 or "responsive-ish" — and let the scale transform handle the viewport.

Keep all slides in the DOM at once and move the track, so printing produces one page per slide and element screenshots work.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Deck title</title>
<style>
  * { box-sizing: border-box }
  html, body { margin: 0; background: #111 }
  .viewport { position: fixed; inset: 0; display: grid; place-items: center; overflow: hidden }
  .frame { position: relative; overflow: hidden }   /* sized to the scaled stage by JS */
  .stage { width: 1920px; height: 1080px; transform-origin: top left }
  .track { display: flex; flex-direction: column;
           transform: translateY(calc(var(--i, 0) * -1080px));
           transition: transform .35s cubic-bezier(.2, .7, .3, 1) }
  .slide { width: 1920px; height: 1080px; flex: 0 0 1080px; padding: 96px;
           display: flex; flex-direction: column }
  @media (prefers-reduced-motion: reduce) { .track { transition: none } }
  @media print {
    @page { size: 1920px 1080px; margin: 0 }
    html, body { background: #fff }
    .viewport { position: static; display: block; overflow: visible }
    .frame { overflow: visible; width: auto !important; height: auto !important }
    .stage { transform: none !important; width: auto; height: auto }
    .track { transform: none }
    .slide { break-after: page; page-break-after: always }
    .slide:last-child { break-after: auto; page-break-after: auto }
  }
</style>
</head>
<body>
  <div class="viewport">
    <div class="frame" id="frame">
      <div class="stage" id="stage">
        <div class="track" id="track">
          <section class="slide" data-screen-label="01 Title">…</section>
          <section class="slide" data-screen-label="02 Problem">…</section>
        </div>
      </div>
    </div>
  </div>
  <script>
    const frame = document.getElementById('frame');
    const stage = document.getElementById('stage');
    const track = document.getElementById('track');
    const slides = [...track.children];
    let i = 0;
    function fit() {
      const s = Math.min(innerWidth / 1920, innerHeight / 1080);
      frame.style.width = `${1920 * s}px`;
      frame.style.height = `${1080 * s}px`;
      stage.style.transform = `scale(${s})`;
    }
    function go(n) {
      i = Math.max(0, Math.min(slides.length - 1, n));
      track.style.setProperty('--i', i);
    }
    addEventListener('resize', fit); fit(); go(0);
    addEventListener('keydown', (e) => {
      if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(e.key)) { e.preventDefault(); go(i + 1); }
      if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); go(i - 1); }
      if (e.key === 'Home') go(0);
      if (e.key === 'End') go(slides.length - 1);
    });
  </script>
</body>
</html>
```

The two-container trick matters: the frame is sized to the *scaled* dimensions, so the stage never overflows the viewport, the deck stays centred, and the verifier's overflow check doesn't report phantom problems. Don't simplify it back to a single scaled element.

`data-screen-label` is what the verifier names each frame after. Number them.

## Slide craft

- **One idea per slide.** If the body needs a sentence of explanation plus a chart plus three bullets, it's two slides.
- **Headline does the work.** The headline states the claim; the body supports it. A deck where every headline is a noun is an agenda, not an argument.
- **Type floor: 24px.** Body 32–36px is normal; headlines 64–110px. If it feels too big on your 1440px monitor, it's still too small at the back of a room.
- **One or two background colours for the whole deck.** Vary section openers by layout, not by inventing a new gradient.
- **Vary the rhythm.** Not every slide is title-plus-three-cards. Give the key number its own full-bleed slide. Let one image or quote run edge to edge.
- **No bullets of bullets.** Three items maximum per group, one line each.
- **Charts get a title that states the finding**, axis labels at 24px, and one highlighted series. Never a rainbow palette.
- **Page number** in the same place on every slide, muted, small.

## Copy

Never rewrite the person's text. Tighten by cutting, not by paraphrasing. If a slide is thin because the source material is thin, say so rather than inventing content.

## Finishing

Run `design-verify` with per-slide frames:

```
node ~/.config/opencode/lib/design/verify.mjs "design/Deck.html" \
  --each "section" --step --each-out design/.verify/deck --out design/.verify/deck.png
```

`--step` walks the deck with the arrow keys and captures the viewport at each slide — exactly what the presenter sees, including the scaling.

Open every frame. Check: nothing clipped at the edges, headlines don't wrap awkwardly, no text under 24px, consistent margins, the highlight colour used the same way everywhere.
