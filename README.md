# opencode-kit

Agents for OpenCode, each with the skills, commands and scripts it needs. Nothing here is a plugin: an agent is a
Markdown file, a skill is a directory with a `SKILL.md`, and the kit wires both into your config.

Requires OpenCode v2 and Node 20+.

## Install

```sh
git clone <this-repo-url> ~/workspace/perso/opencode-kit
cd opencode-kit
make install   # choose agents, skills and MCP servers, then wire them in
make deps      # node dependencies for the installed libs, plus headless chromium for designer (~190 MB, one time)
make check
```

Open a new session and run the agent's command, or select the agent directly.

`make install` opens a checklist of the agents, each with the skills it owns and the MCP servers it uses. Everything
is ticked on a first install, so Enter installs the whole kit. Space toggles a row, and toggling an agent toggles its
skills and servers with it. `a` and `n` select all or none, `q` cancels. Each agent brings its command and any `lib/`
its files use.

Re-run `make install` to change the selection. The checklist starts from what is installed and marks what will be
added (`+`) or removed (`-`). Anything you untick is removed the way `make uninstall` removes it.

To skip the checklist, name what you want. Each variable takes names, `all` or `none`; without `SKILLS` or `MCP`, the
chosen agents bring what they own:

```sh
make install AGENTS=designer                     # designer, every design-* skill, flux and playwright
make install AGENTS=designer MCP=playwright      # the same without FLUX
make install AGENTS="designer grill" SKILLS="design-brief design-deck design-verify"
make install AGENTS=all SKILLS=all MCP=all       # everything
```

Without a terminal, as under CI or Ansible, `make install` installs everything unless one of them is set.

`make install` backs up anything it replaces to `*.bak.<timestamp>` and reports each step.

| Item | Installed as | Destination |
| --- | --- | --- |
| `agents/*.md` | symlink | `~/.config/opencode/agents/` |
| `commands/*.md` | symlink | `~/.config/opencode/commands/` |
| `lib/*/` | symlink | `~/.config/opencode/lib/` |
| `skills/*/` | config entries | `skills` array in `opencode.json` |
| `mcp/*.json` | config entries | `mcp.servers`, plus a rule in `permissions` |

`lib/` is always symlinked so helper scripts keep resolving their `node_modules` inside this checkout. Skills use the
documented `skills` array rather than a link, because it needs no second symlink layer. With every skill selected,
one entry covers the whole directory, so skills added by a later `git pull` show up on their own:

```jsonc
{
  "skills": ["~/workspace/perso/opencode-kit/skills"],
}
```

With a subset, each chosen skill gets its own entry instead, such as `"~/workspace/perso/opencode-kit/skills/design-deck"`.
Other entries in the array are left alone.

Config entries have the highest skill precedence, so they override a same-named skill in `~/.config/opencode/skills`.
The reverse holds too: a skill you leave out still loads from there if a copy exists, and `make check` says so.

## MCP servers

| Server | What it gives | Agents that allow it | Every other agent |
| --- | --- | --- | --- |
| `flux` | FLUX image generation by Black Forest Labs at `https://mcp.bfl.ai`, billed to your BFL account | `designer` | denied |
| `playwright` | A headless, isolated browser through `@playwright/mcp`, for clicking through pages | `designer` | asks first |

Each `mcp/<name>.json` holds the entry written under `mcp.servers.<name>`, plus an `other_agents` effect. An agent opts
in by allowing `<name>_*` in its permissions, which is also how the checklist knows to list the server under it. Every
other agent gets a global `<name>_*` rule with that effect; agent rules come after global ones, so the opt-in wins.

In practice, `designer` always has both. In `build`, Playwright asks before it is used: approve once, or always for
that project. FLUX stays out of `build`'s tools, along with its long server instructions.

Sign in to FLUX once after installing: run `/mcps` in OpenCode and pick `flux`, or `opencode mcp auth flux`.

A server you already configured under the same name keeps your entry, so the kit only manages its rule. The checklist
says which fields differ. To use the kit's definition instead, delete your entry and run `make install` again. Do the
same after changing a file in `mcp/`, because the old entry then counts as yours.

`playwright` runs with `--allow-unrestricted-file-access` so it can open the `file://` pages the designer builds;
Playwright blocks those by default. Remove the flag in `mcp/playwright.json` to keep that guardrail.

## Manual install

Without the Makefile, five steps:

1. Symlink or copy `agents/*.md` into `~/.config/opencode/agents/`.
2. Symlink or copy `commands/*.md` into `~/.config/opencode/commands/`.
3. Symlink each `lib/*` to `~/.config/opencode/lib/`.
4. Add the `skills` entry above to your OpenCode config, or one entry per skill directory you want, then
   `npm install` in each `lib/` that has a `package.json` (and `npx playwright install chromium` for `lib/design`).
5. Copy the `server` object of each `mcp/<name>.json` you want to `mcp.servers.<name>`, and add a global permission
   rule `{ "action": "<name>_*", "resource": "*", "effect": <its other_agents> }`.

## Agents

| Agent | Command | Skills it owns | MCP servers | What it does |
| --- | --- | --- | --- | --- |
| `designer` | `/design` | `design-*` | `flux`, `playwright` | Design systems as `tokens.css` and `components.css` that other apps copy, and decks, documents, prototypes and wireframes as HTML built on them; generates imagery with FLUX, verifies in headless Chromium and clicks through prototypes |
| `grill` | `/grill` | — | — | Staff-engineer sparring partner: challenges scope, priority, evidence and architecture before work starts, one decision at a time |

`pptx` and `pdf` are used for export when present; they are separate skills, not part of this kit.

## Adding an agent

The kit has no registry to edit. Drop these in and `make install` picks them up:

```
agents/<name>.md          # the agent; frontmatter + system prompt
commands/<name>.md        # optional: /<name>
skills/<subject>-*/       # skills the agent owns
lib/<name>/               # optional: scripts those skills call
mcp/<server>.json         # optional: an MCP server, with its other_agents effect
```

The checklist reads what belongs together from the files themselves. A command goes with the agent in its `agent`
frontmatter. An agent owns the skills its `skill` permissions allow by name or pattern, not through `*`, and uses the
MCP servers it allows as `<server>_*`. A lib is installed whenever a chosen agent, command or skill mentions
`~/.config/opencode/lib/<name>/`. Commands, skills and servers that belong to no agent are listed on their own.

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

Links and the config entries keep pointing at this checkout. Re-run `make deps` only when a `lib/*/package.json`
changed, and `make install` to pick up a new agent or MCP server, or a new skill when you selected only some.

## Uninstall

```sh
make uninstall
```

Removes the links, the `skills` entries, and the kit's MCP servers and permission rules, and restores any `*.bak.*`
backups. Servers you configured yourself stay.

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

`lib/design/inline.mjs` makes the standalone copy the skills use when an artifact leaves the project:

```sh
node ~/.config/opencode/lib/design/inline.mjs "design/Foo.html"
# → design/Foo.standalone.html
```

It copies local stylesheets and classic scripts into the HTML and follows `@import`. Artifacts link
`design/tokens.css` while they are being built, so the single-file version is an export step, not the authoring
format.

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

- Use `make install MODE=copy` if symlinked files are not picked up by your setup. A copy you edit by hand counts as
  yours: install backs it up before replacing it, and uninstall leaves it in place.
- The `SKILL.md` files also work in Claude Code: copy `skills/*` into `~/.claude/skills`.
- An agent with the same ID already present merges instead of replacing: permission rules append. Remove the old file
  if you want only the kit's rules.

## License

Apache-2.0. See [LICENSE](LICENSE).
