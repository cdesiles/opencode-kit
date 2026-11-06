# opencode-designer

An OpenCode agent for design work: design systems, decks, documents, prototypes and wireframes, delivered as
single self-contained HTML files. Ships the agent, nine skills, a `/design` command, and the headless verification
script the agent depends on.

Requires OpenCode v2 and Node 20+.

## Install

```sh
git clone <this-repo-url> ~/workspace/perso/opencode-designer
cd opencode-designer
make deps      # playwright + headless chromium, ~190 MB, one time
make install
make check
```

Open a new session and run `/design` — or switch to the `designer` agent.

`make install` backs up anything it replaces to `*.bak.<timestamp>` and reports each step.

| Item | Installed as | Destination |
| --- | --- | --- |
| `agents/designer.md` | symlink | `~/.config/opencode/agents/designer.md` |
| `commands/design.md` | symlink | `~/.config/opencode/commands/design.md` |
| `lib/design/` | symlink | `~/.config/opencode/lib/design/` |
| `skills/` | config entry | `skills` array in `opencode.json` |

The `lib/design` symlink matters: the agent prompt and five skills hardcode
`node ~/.config/opencode/lib/design/verify.mjs`, so the script must be reachable at that exact path.

The skills use the documented `skills` array instead of a link because it needs no second symlink layer:

```jsonc
{
  "skills": ["~/workspace/perso/opencode-designer/skills"],
}
```

Config entries have the highest skill precedence, so this overrides a same-named skill in `~/.config/opencode/skills`.

## Manual install

Without the Makefile, four steps:

1. Symlink or copy `agents/designer.md` into `~/.config/opencode/agents/`.
2. Symlink or copy `commands/design.md` into `~/.config/opencode/commands/`.
3. Symlink `lib/design` to `~/.config/opencode/lib/design`.
4. Add the `skills` entry above to your OpenCode config, then `npm install && npx playwright install chromium`
   inside `lib/design`.

## Update

```sh
git pull
```

Links and the config entry keep pointing at this checkout. Re-run `make deps` only when `lib/design/package.json`
changed.

## Uninstall

```sh
make uninstall
```

Removes the links and the `skills` entry, and restores any `*.bak.*` backups.

## Skills

| Skill | Use |
| --- | --- |
| `design-brief` | Nail down audience, format and constraints |
| `design-aesthetic` | No brand, direction open |
| `design-system` | Tokens, type, spacing, components as a specimen page |
| `design-deck` | 1920×1080 keyboard-driven presentation |
| `design-doc` | Report, memo, proposal, printable page |
| `design-prototype` | Clickable app or feature mockup |
| `design-options` | A few distinct directions to choose between |
| `design-wireframe` | Many rough ideas, early exploration |
| `design-verify` | Render, screenshot and inspect before handing over |

`pptx` and `pdf` are used for export when present; they are separate skills, not part of this kit.

## Verify script

```sh
node ~/.config/opencode/lib/design/verify.mjs "design/Foo.html" --full --out design/.verify/foo.png
```

Serves the file on a throwaway localhost port, loads it in headless Chromium, and reports console errors, failed
requests, horizontal overflow, broken images, the fonts that actually rendered, and a screenshot path. Exits 1 on
problems. Flags are documented in `lib/design/README.md`; `make test` is a smoke test of the whole chain.

## Notes

- The agent denies every skill except `design-*`, `pptx` and `pdf`. To keep design skills out of the default
  agents too, add to your config:

  ```jsonc
  {
    "agents": {
      "build": {
        "permissions": [{ "action": "skill", "resource": "design-*", "effect": "deny" }],
      },
    },
  }
  ```

- Use `make install MODE=copy` if symlinked files are not picked up.
- The `SKILL.md` files also work in Claude Code: copy `skills/*` into `~/.claude/skills`.
- The agent's frontmatter uses V2 fields only (`permissions`, no `temperature`), which V2 accepts and older
  versions read as deprecated.
