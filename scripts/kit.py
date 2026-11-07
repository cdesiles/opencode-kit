#!/usr/bin/env python3
"""Choose what to install from this kit, or check what is installed.

    kit.py select <opencode-dir> <repo> <selection-file> [agents] [skills] [mcp]
    kit.py check  <opencode-dir> <repo>

select writes a "<kind> <name>" line for every agent, command, lib, skill and
MCP server to install, for wire.sh and opencode-config.py to apply. Given no
list, it opens a checklist when run in a terminal, starting from what is
installed (or from everything on a first install), and picks everything
otherwise. A list is "all", "none", or names separated by spaces or commas;
an empty skills or mcp list means what the chosen agents use. Cancelling
leaves the file empty.

Nothing is registered by hand: an agent owns the skills its permissions allow
by name or pattern and the MCP servers it allows as "<server>_*", a command
goes with the agent in its frontmatter, and a lib is installed when a chosen
item mentions ~/.config/opencode/lib/<name>/. A server you configured
differently under the same name keeps your entry; the kit only sets its rule.

check reports each item and exits 1 when an installed one is incomplete.
"""

from __future__ import annotations

import filecmp
import importlib.util
import locale
import os
import re
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

try:
    import curses
except ImportError:  # some minimal Python builds ship without it
    curses = None

HEADER = "# opencode-kit selection"
KINDS = ("agent", "command", "lib", "skill", "mcp")


def _load_opencode_config():
    path = Path(__file__).resolve().with_name("opencode-config.py")
    spec = importlib.util.spec_from_file_location("opencode_config", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


opencode_config = _load_opencode_config()


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value.split(" #", 1)[0].rstrip()


def frontmatter(path: Path) -> dict:
    """Read the frontmatter subset the kit uses: scalars, and lists of flat maps."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict = {}
    items = item = block = None
    for raw in lines[1:]:
        text = raw.strip()
        if text == "---":
            break
        if block is not None:
            if not text or raw[0].isspace():
                data[block] = (data[block] + " " + text).strip()
                continue
            block = None
        if not text or text.startswith("#"):
            continue
        if not raw[0].isspace() and not text.startswith("-"):
            key, _, value = text.partition(":")
            key, value = key.strip(), value.strip()
            items = item = None
            if value in ("|", ">", "|-", ">-", "|+", ">+"):
                data[key], block = "", key
            elif value:
                data[key] = unquote(value)
            else:
                items = data[key] = []
            continue
        if items is None:
            continue
        if text.startswith("-"):
            text = text[1:].strip()
            if text.startswith("{") and text.endswith("}"):
                pairs = (part.partition(":") for part in text[1:-1].split(","))
                items.append({k.strip(): unquote(v) for k, _, v in pairs if k.strip()})
                item = None
                continue
            item = {}
            items.append(item)
        if item is not None and ":" in text:
            key, _, value = text.partition(":")
            item[key.strip()] = unquote(value)
    return data


def owns(rules: list, skill: str) -> bool:
    """True when the last rule matching <skill> allows it by name or pattern, not by '*'."""
    last = None
    for rule in rules:
        if fnmatchcase("skill", rule.get("action", "")) and fnmatchcase(skill, rule.get("resource", "*")):
            last = rule
    return last is not None and last.get("effect") == "allow" and last.get("resource", "*").strip("*") != ""


def uses(rules: list, server: str) -> bool:
    """True when the agent's last rule for '<server>_*' allows the whole server."""
    last = None
    for rule in rules:
        if rule.get("action") == f"{server}_*":
            last = rule
    return last is not None and last.get("effect") == "allow"


def is_ours(src: Path, dest: Path) -> bool:
    """True when <dest> is what wire.sh put there for <src>: a link to it, or an unmodified copy."""
    if dest.is_symlink():
        try:
            return os.path.samefile(dest, src)
        except OSError:
            return False
    return dest.is_file() and src.is_file() and filecmp.cmp(src, dest, shallow=False)


def children(directory: Path) -> list:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if not p.name.startswith("."))


def skill_files(directory: Path) -> list:
    found = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        found.extend(Path(root, f) for f in files if not f.startswith("."))
    return found


@dataclass
class Item:
    kind: str
    name: str
    path: Path
    meta: dict
    agent: str | None = None  # command: the kit agent it starts
    commands: list = field(default_factory=list)  # agent: its commands
    skills: list = field(default_factory=list)  # agent: the skills it owns
    servers: list = field(default_factory=list)  # agent: the MCP servers it uses
    libs: set = field(default_factory=set)

    @property
    def key(self) -> tuple:
        return (self.kind, self.name)

    @property
    def description(self) -> str:
        return " ".join(str(self.meta.get("description", "")).split())


class Kit:
    def __init__(self, repo: Path):
        self.repo = repo
        self.libs = [p.name for p in children(repo / "lib") if p.is_dir()]
        self._lib_refs = {
            lib: re.compile(r"opencode/lib/" + re.escape(lib) + r"(?![\w.-])") for lib in self.libs
        }
        self.agents = {
            p.stem: self._item("agent", p.stem, p, [p])
            for p in children(repo / "agents")
            if p.suffix == ".md" and p.is_file()
        }
        self.commands = {
            p.stem: self._item("command", p.stem, p, [p])
            for p in children(repo / "commands")
            if p.suffix == ".md" and p.is_file()
        }
        self.skills = {
            p.name: self._item("skill", p.name, p / "SKILL.md", skill_files(p))
            for p in children(repo / "skills")
            if (p / "SKILL.md").is_file()
        }
        self.servers = {
            name: Item("mcp", name, repo / "mcp" / f"{name}.json", spec)
            for name, spec in opencode_config.servers(repo).items()
        }
        for agent in self.agents.values():
            rules = [r for r in agent.meta.get("permissions", []) if isinstance(r, dict)]
            agent.skills = [name for name in self.skills if owns(rules, name)]
            agent.servers = [name for name in self.servers if uses(rules, name)]
        for command in self.commands.values():
            owner = self.agents.get(str(command.meta.get("agent", "")))
            if owner:
                command.agent = owner.name
                owner.commands.append(command.name)

    def _item(self, kind: str, name: str, path: Path, files: list) -> Item:
        item = Item(kind, name, path, frontmatter(path))
        for file in files:
            try:
                if file.stat().st_size > 1_000_000:
                    continue
                text = file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            item.libs.update(lib for lib, ref in self._lib_refs.items() if ref.search(text))
        return item

    def standalone(self) -> list:
        """Commands that start no agent from this kit, chosen on their own."""
        return [c for c in self.commands.values() if c.agent is None]

    def everything(self) -> set:
        items = list(self.agents.values()) + self.standalone() + list(self.skills.values())
        return {item.key for item in items + list(self.servers.values())}

    def state(self, opencode_dir: Path):
        """What is installed, as keys, and the servers configured differently under the kit's names.

        A server of yours counts as installed when the kit's permission rule for it is in place.
        """
        keys = {a.key for a in self.agents.values() if is_ours(a.path, opencode_dir / "agents" / a.path.name)}
        keys |= {c.key for c in self.standalone() if is_ours(c.path, opencode_dir / "commands" / c.path.name)}
        registered, _ = opencode_config.registered(opencode_dir, self.repo / "skills")
        ours, foreign, ruled = opencode_config.server_state(opencode_dir, self.repo)
        if registered is None:  # the config is not plain JSON: assume every skill and server
            registered, ours, foreign, ruled = set(self.skills), set(self.servers), {}, set()
        keys |= {("skill", name) for name in registered if name in self.skills}
        keys |= {("mcp", name) for name in ours | (set(foreign) & ruled)}
        return keys, foreign

    def locked(self, foreign: dict) -> set:
        """Servers of yours with no permission rule to set, so nothing for the kit to do."""
        return {("mcp", name) for name in foreign if not self.servers[name].meta.get("other_agents")}

    def resolve(self, agents: str, skills: str, servers: str) -> set:
        """Turn AGENTS, SKILLS and MCP values into a selection. Raises ValueError on unknown names."""
        tops = {a.name: a.key for a in self.agents.values()}
        tops.update({"/" + c.name: c.key for c in self.standalone()})
        chosen = set(names(agents, tops, "agent"))
        picked = [a for a in self.agents.values() if a.key in chosen]
        if skills.replace(",", " ").split():
            chosen |= set(names(skills, {name: ("skill", name) for name in self.skills}, "skill"))
        else:
            chosen |= {("skill", s) for a in picked for s in a.skills}
        if servers.replace(",", " ").split():
            chosen |= set(names(servers, {name: ("mcp", name) for name in self.servers}, "MCP server"))
        else:
            chosen |= {("mcp", s) for a in picked for s in a.servers}
        return chosen

    def plan(self, chosen: set) -> dict:
        agents = [a for a in self.agents.values() if a.key in chosen]
        started = {a.name for a in agents}
        commands = [c for c in self.commands.values() if c.agent in started or c.key in chosen]
        skills = [s for s in self.skills.values() if s.key in chosen]
        libs = set().union(*(item.libs for item in agents + commands + skills))
        return {
            "agent": [a.name for a in agents],
            "command": [c.name for c in commands],
            "lib": [lib for lib in self.libs if lib in libs],
            "skill": [s.name for s in skills],
            "mcp": [s.name for s in self.servers.values() if s.key in chosen],
        }

    def rows(self) -> list:
        def leaf(item: Item) -> Row:
            detail = "MCP · " + item.description if item.kind == "mcp" else item.description
            return Row(item.key, item.name, detail, 1, [])

        rows, owned = [], set()
        for agent in self.agents.values():
            parts = [self.skills[s] for s in agent.skills] + [self.servers[s] for s in agent.servers]
            detail = " · ".join(filter(None, [" ".join("/" + c for c in agent.commands), agent.description]))
            rows.append(Row(agent.key, agent.name, detail, 0, [p.key for p in parts]))
            rows.extend(leaf(p) for p in parts)
            owned.update(p.key for p in parts)
        rows.extend(Row(c.key, "/" + c.name, c.description, 0, []) for c in self.standalone())
        for label, group in (("skills", self.skills), ("MCP servers", self.servers)):
            loose = [item for item in group.values() if item.key not in owned]
            if loose:
                rows.append(Row(None, f"other {label}" if self.agents else label, "", 0, [i.key for i in loose]))
                rows.extend(leaf(i) for i in loose)
        return rows


def names(value: str, valid: dict, kind: str) -> list:
    words = value.replace(",", " ").split()
    if words == ["all"]:
        return list(valid.values())
    if words in ([], ["none"]):
        return []
    unknown = [w for w in words if w not in valid]
    if unknown:
        raise ValueError(f"unknown {kind}: {', '.join(unknown)} (available: {', '.join(valid) or 'none'})")
    return [valid[w] for w in words]


@dataclass
class Row:
    key: tuple | None  # the item this row stands for; None for a heading
    label: str
    detail: str
    depth: int
    members: list  # items toggled along with this row


class PickerError(Exception):
    pass


class Picker:
    """Full-screen checklist. Returns the chosen keys, or None when cancelled."""

    def __init__(self, kit: Kit, chosen: set, installed: set, foreign: dict, target: str):
        self.kit = kit
        self.rows = kit.rows()
        self.foreign = foreign
        self.locked = kit.locked(foreign)
        self.chosen = set(chosen) - self.locked
        self.installed = installed
        self.target = target
        self.cursor = self.top = 0
        self.view = 1

    def __call__(self, screen):
        self.screen = screen
        self.utf8 = "utf" in str(getattr(screen, "encoding", "")).lower()
        self.colors = {}
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        if curses.has_colors():
            try:
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_GREEN, -1)
                curses.init_pair(2, curses.COLOR_RED, -1)
                self.colors = {"+": curses.color_pair(1), "-": curses.color_pair(2)}
            except curses.error:
                pass
        while True:
            self.draw()
            key = screen.getch()
            if key in (curses.KEY_UP, ord("k")):
                self.move(-1)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.move(1)
            elif key == curses.KEY_PPAGE:
                self.move(-self.view)
            elif key == curses.KEY_NPAGE:
                self.move(self.view)
            elif key in (curses.KEY_HOME, ord("g")):
                self.cursor = 0
            elif key in (curses.KEY_END, ord("G")):
                self.cursor = len(self.rows) - 1
            elif key in (ord(" "), ord("x")):
                self.toggle(self.rows[self.cursor])
            elif key == ord("a"):
                self.chosen = self.kit.everything() - self.locked
            elif key == ord("n"):
                self.chosen = set()
            elif key in (curses.KEY_ENTER, 10, 13):
                return self.chosen
            elif key in (27, ord("q")):
                return None

    def move(self, step: int):
        self.cursor = max(0, min(len(self.rows) - 1, self.cursor + step))

    def toggle(self, row: Row):
        keys = [k for k in ([row.key] if row.key else []) + row.members if k not in self.locked]
        if row.key:
            on = row.key not in self.chosen
        else:
            on = not all(k in self.chosen for k in keys)
        if on:
            self.chosen.update(keys)
        else:
            self.chosen.difference_update(keys)

    def glyph(self, fancy: str, plain: str) -> str:
        return fancy if self.utf8 else plain

    def put(self, y: int, x: int, text: str, attr: int = 0) -> int:
        room = self.screen.getmaxyx()[1] - 1 - x
        if room <= 0 or not text:
            return x
        if len(text) > room:
            text = text[: room - 1] + self.glyph("…", "~")
        if not self.utf8:
            text = text.encode("ascii", "replace").decode()
        try:
            self.screen.addstr(y, x, text, attr)
        except (curses.error, UnicodeEncodeError):
            pass
        return x + len(text)

    def mark(self, row: Row) -> str:
        if row.key is None or row.key in self.locked:
            return ""
        was, now = row.key in self.installed, row.key in self.chosen
        return "+" if now and not was else "-" if was and not now else ""

    def box(self, row: Row) -> str:
        if row.key in self.locked:
            return "[=]"
        if row.key is not None:
            return "[x]" if row.key in self.chosen else "[ ]"
        members = [k for k in row.members if k not in self.locked]
        picked = sum(k in self.chosen for k in members)
        return "[x]" if picked == len(members) else "[ ]" if picked == 0 else "[-]"

    def detail(self, row: Row) -> str:
        if row.key is None or row.key[0] != "mcp" or row.key[1] not in self.foreign:
            return row.detail
        differs = ", ".join(self.foreign[row.key[1]])
        if row.key in self.locked:
            return f"MCP · yours: your entry differs ({differs}) and there is no rule to set"
        return f"MCP · yours: your entry differs ({differs}) and stays; the kit sets who may use it"

    def summary(self) -> str:
        plan = self.kit.plan(self.chosen)
        parts = [
            f"{len(plan['agent'])} of {len(self.kit.agents)} agents",
            f"{len(plan['skill'])} of {len(self.kit.skills)} skills",
        ]
        standalone = self.kit.standalone()
        if standalone:
            parts.append(f"{sum(c.key in self.chosen for c in standalone)} of {len(standalone)} commands")
        if self.kit.servers:
            parts.append(f"{len(plan['mcp'])} of {len(self.kit.servers)} MCP servers")
        added, removed = len(self.chosen - self.installed), len(self.installed - self.chosen)
        change = f"{added} to add, {removed} to remove" if added or removed else "no changes"
        return ", ".join(parts) + self.glyph(" · ", " - ") + change

    def draw(self):
        screen = self.screen
        screen.erase()
        height, width = screen.getmaxyx()
        if height < 8 or width < 40:
            self.put(0, 0, "Window too small (q cancels)")
            screen.refresh()
            return
        self.view = height - 5
        self.top = max(min(self.top, self.cursor), self.cursor - self.view + 1)
        self.put(0, 1, f"Choose what to install in {self.target}", curses.A_BOLD)
        if self.top > 0:
            self.put(1, 1, self.glyph("↑ more", "^ more"), curses.A_DIM)
        if self.top + self.view < len(self.rows):
            self.put(height - 3, 1, self.glyph("↓ more", "v more"), curses.A_DIM)
        label_width = min(28, max(len(r.label) + 4 * r.depth for r in self.rows))
        for line, index in enumerate(range(self.top, min(len(self.rows), self.top + self.view))):
            self.draw_row(2 + line, self.rows[index], index == self.cursor, label_width)
        self.put(height - 2, 1, self.summary())
        keys = self.glyph("↑↓", "j/k") + " move   space toggle   a all   n none   enter install   q cancel"
        self.put(height - 1, 1, keys, curses.A_DIM)
        screen.refresh()

    def draw_row(self, y: int, row: Row, current: bool, label_width: int):
        base = curses.A_REVERSE if current else 0
        if current:
            self.put(y, 0, " " * (self.screen.getmaxyx()[1] - 1), base)
        mark = self.mark(row)
        self.put(y, 1, mark, base | self.colors.get(mark, 0))
        weight = curses.A_BOLD if row.depth == 0 else 0
        x = self.put(y, 3 + 4 * row.depth, f"{self.box(row)} {row.label}", base | weight)
        self.put(y, max(x + 2, 9 + label_width), self.detail(row), base if current else curses.A_DIM)


def pick(kit: Kit, chosen: set, installed: set, foreign: dict, target: str):
    if curses is None:
        raise PickerError("this Python has no curses module")
    os.environ.setdefault("ESCDELAY", "50")
    locale.setlocale(locale.LC_ALL, "")
    try:
        return curses.wrapper(Picker(kit, chosen, installed, foreign, target))
    except curses.error as err:
        raise PickerError(f"the terminal cannot show the checklist ({err})") from err


def select(opencode_dir: Path, repo: Path, out: Path, agents: str, skills: str, servers: str) -> int:
    kit = Kit(repo)
    if not kit.everything():
        print(f"Nothing to install: {repo} has no agents, commands, skills or MCP servers.")
        return 0
    installed, foreign = kit.state(opencode_dir)
    if agents.strip() or skills.strip() or servers.strip():
        try:
            chosen = kit.resolve(agents, skills, servers)
        except ValueError as err:
            print(err, file=sys.stderr)
            return 2
    elif sys.stdin.isatty() and sys.stdout.isatty():
        target = opencode_config.portable(opencode_dir)
        try:
            chosen = pick(kit, installed or kit.everything(), installed, foreign, target)
        except PickerError as err:
            print(f"{str(err).capitalize()}. Set AGENTS, SKILLS or MCP to choose without it.", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            chosen = None
        if chosen is None:
            print("Cancelled, nothing changed.")
            return 0
    else:
        print("No terminal for the checklist: installing everything (set AGENTS, SKILLS or MCP to choose).")
        chosen = kit.everything()

    plan = kit.plan(chosen - kit.locked(foreign))
    lines = [HEADER] + [f"{kind} {name}" for kind in KINDS for name in plan[kind]]
    out.write_text("\n".join(lines) + "\n")

    tops = plan["agent"] + ["/" + c.name for c in kit.standalone() if c.name in plan["command"]]
    print("agents: " + (", ".join(tops) or "none"))
    picked, total = plan["skill"], len(kit.skills)
    if picked and len(picked) == total:
        print(f"skills: all {total}")
    else:
        print("skills: " + (f"{', '.join(picked)} ({len(picked)} of {total})" if picked else "none"))
    if kit.servers:
        print("mcp: " + (", ".join(plan["mcp"]) or "none"))
    for name, keys in foreign.items():
        managed = name in plan["mcp"] and kit.servers[name].meta.get("other_agents")
        tail = "; the kit sets only its permission rule" if managed else ""
        print(f"mcp: {name} keeps your own entry, which differs from mcp/{name}.json ({', '.join(keys)}){tail}")
    return 0


def check(opencode_dir: Path, repo: Path) -> int:
    kit = Kit(repo)
    problems = 0

    def report(status: str, message) -> None:
        nonlocal problems
        problems += status in ("MISS", "STALE")
        print(f"{status:<5} {message}")

    live = set()
    for item in list(kit.agents.values()) + list(kit.commands.values()):
        dest = opencode_dir / f"{item.kind}s" / item.path.name
        if is_ours(item.path, dest):
            report("ok", dest)
            live.add(item.key)
        elif item.kind == "command" and ("agent", item.agent) in live:
            report("MISS", f"{dest} (run make install)")
        else:
            report("--", f"{dest} (not installed)")

    config = opencode_config.config_path(opencode_dir)
    registered, stale = opencode_config.registered(opencode_dir, repo / "skills")
    live |= {("skill", name) for name in registered or ()}

    items = list(kit.agents.values()) + list(kit.commands.values()) + list(kit.skills.values())
    needed = set().union(*(item.libs for item in items if item.key in live))
    for lib in kit.libs:
        src, dest = repo / "lib" / lib, opencode_dir / "lib" / lib
        if is_ours(src, dest):
            report("ok", dest)
            if (src / "package.json").is_file() and not (src / "node_modules").is_dir():
                report("MISS", f"{lib} dependencies (run make deps)")
        elif lib in needed:
            report("MISS", f"{dest} (run make install)")
        else:
            report("--", f"{dest} (not installed)")

    if registered is None:
        report("MISS", f"skills entries: {config} is not plain JSON, check them by hand")
    else:
        for entry in stale:
            report("STALE", f"skills entry {entry} in {config} (run make install)")
        if registered:
            report("ok", f"{len(registered)} of {len(kit.skills)} skills registered in {config}")
        for name in kit.skills:
            if name in registered:
                continue
            leftover = opencode_dir / "skills" / name
            note = f"; {leftover} still provides it" if (leftover / "SKILL.md").is_file() else ""
            report("--", f"skill {name} (not registered{note})")

    ours, foreign, ruled = opencode_config.server_state(opencode_dir, repo)
    for name, item in kit.servers.items() if ours is not None else ():
        policy = item.meta.get("other_agents")
        rule = f"{name}_* {policy} for other agents"
        if name in ours:
            live.add(item.key)
            report("ok", f"MCP server {name} in {config}")
            if policy and name not in ruled:
                report("MISS", f"permission {rule} in {config} (run make install)")
        elif name in foreign:
            own = f"MCP server {name}: your own entry in {config}, which differs in {', '.join(foreign[name])}"
            if name in ruled:
                live.add(item.key)
                report("ok", f"{own}, with {rule}")
            else:
                report("--", own)
        elif name in ruled:
            report("STALE", f"permission {rule} in {config}, but no {name} server (run make install)")
        else:
            report("--", f"MCP server {name} (not installed)")

    if not live:
        report("MISS", "nothing from this kit is installed (run make install)")
    return 1 if problems else 0


def main() -> int:
    args = sys.argv[1:]
    if 4 <= len(args) <= 7 and args[0] == "select":
        padded = args[1:] + [""] * (7 - len(args))
        return select(Path(padded[0]), Path(padded[1]), Path(padded[2]), *padded[3:6])
    if len(args) == 3 and args[0] == "check":
        return check(Path(args[1]), Path(args[2]))
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
