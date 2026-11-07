# design/

Two tools used by the `designer` agent and the `design-*` skills.

## verify.mjs

Browser verification. Serves the target over a throwaway `127.0.0.1` port, loads
it in headless Chromium, and reports console errors, failed requests, horizontal
overflow, broken images, the fonts that actually rendered, and a screenshot.
Exits 1 on problems.

```sh
node ~/.config/opencode/lib/design/verify.mjs "design/Foo.html" --full --out design/.verify/foo.png
```

When a `tokens.css` sits next to the artifact (or one level up), it also checks
that the page links it, and lists colour literals (hex, `oklch()`, `rgb()` and
the like) in the page's own CSS and in its other local stylesheets, such as
`components.css`. Named colours are not flagged. Those are notes, not failures.

| Flag | Effect |
|---|---|
| `--out <path.png>` | screenshot destination (default `./verify.png`) |
| `--full` | full-page screenshot |
| `--width` / `--height` | viewport, default 1440×900 |
| `--scale <n>` | device scale factor, default 2 |
| `--settle <ms>` | extra wait after load, default 600 |
| `--each <selector>` | also screenshot every match |
| `--step` | with `--each`: step through frames by keypress (for decks) |
| `--key <key>` | key used by `--step`, default `ArrowRight` |
| `--each-out <dir>` | destination for per-frame shots |
| `--headed` | show the window instead of running headless |
| `--hold` | with `--headed`: keep it open until closed |
| `--quiet` | JSON only |

Each run is its own process with its own browser, so several agents can verify
at the same time without conflicts or windows appearing.

## inline.mjs

Makes a standalone copy: local stylesheets and classic scripts are copied into
the HTML, `@import` chains are followed, `url()` references are rewritten.

```sh
node ~/.config/opencode/lib/design/inline.mjs "design/Foo.html"
# → design/Foo.standalone.html
```

Remote URLs are left alone. Module scripts are left as references. Exit code 1
means a local reference could not be resolved and the copy is incomplete — always
run the verifier on the standalone file afterwards.

## Reinstalling

`package.json` and `node_modules` are gitignored in this repo, so a fresh
checkout needs:

```sh
cd ~/.config/opencode/lib/design
npm install                       # playwright package
npx playwright install chromium   # ~190MB, one time
```
