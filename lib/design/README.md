# design/verify.mjs

Browser verification for design artifacts, used by the `designer` agent and the
`design-*` skills.

```sh
node ~/.config/opencode/lib/design/verify.mjs "design/Foo.html" --full --out design/.verify/foo.png
```

Serves the target over a throwaway `127.0.0.1` port, loads it in headless
Chromium, and reports console errors, failed requests, horizontal overflow,
broken images, the fonts that actually rendered, and a screenshot. Exits 1 on
problems.

## Reinstalling

`package.json` and `node_modules` are gitignored in this repo, so a fresh
checkout needs:

```sh
cd ~/.config/opencode/lib/design
npm install                       # playwright package
npx playwright install chromium   # ~190MB, one time
```

## Flags

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
| `--quiet` | JSON only |

Each run is its own process with its own browser, so several agents can verify
at the same time without conflicts or windows appearing.
