# opencode-kit

Agents for OpenCode, each with the skills, commands and scripts it needs. Nothing here is a plugin: an agent is a
Markdown file, a skill is a directory with a `SKILL.md`, and the kit wires both into your config.

Requires OpenCode v2 and Node 20+.

## Install

```sh
git clone <this-repo-url> ~/workspace/perso/opencode-kit
cd opencode-kit
make deps      # node dependencies per lib/*, plus headless chromium (~190 MB, one time)
make install
make check
```

Open a new session and run the agent's command, or select the agent directly.

`make install` backs up anything it replaces to `*.bak.<timestamp>` and reports each step.

| Item | Installed as | Destination |
| --- | --- | --- |
| `agents/*.md` | symlink | `~/.config/opencode/agents/` |
| `commands/*.md` | symlink | `~/.config/opencode/commands/` |
| `lib/*/` | symlink | `~/.config/opencode/lib/` |
| `skills/` | config entry | `skills` array in `opencode.json` |

`lib/` is always symlinked so helper scripts keep resolving their `node_modules` inside this checkout. Skills use the
documented `skills` array rather than a link, because it needs no second symlink layer:

```jsonc
{
  "skills": ["~/workspace/perso/opencode-kit/skills"],
}
```

Config entries have the highest skill precedence, so this overrides a same-named skill in `~/.config/opencode/skills`.

## Manual install

Without the Makefile, four steps:

1. Symlink or copy `agents/*.md` into `~/.config/opencode/agents/`.
2. Symlink or copy `commands/*.md` into `~/.config/opencode/commands/`.
3. Symlink each `lib/*` to `~/.config/opencode/lib/`.
4. Add the `skills` entry above to your OpenCode config, then `npm install` in each `lib/` that has a
   `package.json` (and `npx playwright install chromium` for `lib/design`).

## Agents

| Agent | Command | Skills it owns | What it does |
| --- | --- | --- | --- |
| `designer` | `/design` | `design-*` | Design systems, decks, documents, prototypes and wireframes as self-contained HTML; verifies them in headless Chromium |

`pptx` and `pdf` are used for export when present; they are separate skills, not part of this kit.

## Adding an agent

The kit has no registry to edit. Drop four things in and it is picked up by `make install`:

```
agents/<name>.md          # the agent; frontmatter + system prompt
commands/<name>.md        # optional: /<name>
skills/<subject>-*/       # skills the agent owns
lib/<name>/               # optional: scripts those skills call
```

Keep the skill prefix aligned with the agent's permission rules. `designer` denies every skill and allows only
`design-*`, so its skills carry that prefix; a second agent owning `writing-*` stays out of its way. This is the same
isolation pattern as key prefixes in a shared cache.

Agent frontmatter should use V2 fields — `mode`, `permissions` as a list of `{action, resource, effect}`. Avoid the
legacy `permission` map, `temperature`, `tools` and `maxSteps`: V2 reads them as deprecated, and request overlays are
preserved but not yet sent with model requests.

## Update

```sh
git pull
```

Links and the config entry keep pointing at this checkout. Re-run `make deps` only when a `lib/*/package.json` changed.

## Uninstall

```sh
make uninstall
```

Removes the links and the `skills` entry, and restores any `*.bak.*` backups.

## Verify script

The design skills call:

```sh
node ~/.config/opencode/lib/design/verify.mjs "design/Foo.html" --full --out design/.verify/foo.png
```

Serves the file on a throwaway localhost port, loads it in headless Chromium, and reports console errors, failed
requests, horizontal overflow, broken images, the fonts that actually rendered, and a screenshot path. Exits 1 on
problems. Flags are documented in `lib/design/README.md`; `make test` is a smoke test of the whole chain.

The path is hardcoded in the agent prompt and five skills, which is why `make install` puts a link at
`~/.config/opencode/lib/design` rather than relying on a nicer layout.

## Notes

- To keep design skills out of the default agents too, add to your config:

  ```jsonc
  {
    "agents": {
      "build": {
        "permissions": [{ "action": "skill", "resource": "design-*", "effect": "deny" }],
      },
    },
  }
  ```

- Use `make install MODE=copy` if symlinked files are not picked up by your setup.
- The `SKILL.md` files also work in Claude Code: copy `skills/*` into `~/.claude/skills`.
- An agent with the same ID already present merges instead of replacing: permission rules append. Remove the old file
  if you want only the kit's rules.

## License

Apache-2.0. See [LICENSE](LICENSE).
