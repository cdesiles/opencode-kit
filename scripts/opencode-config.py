#!/usr/bin/env python3
"""Register this repo's skills and MCP servers in an OpenCode config file.

    opencode-config.py sync          <opencode-dir> <repo> <selection-file>
    opencode-config.py remove        <opencode-dir> <repo>
    opencode-config.py skills-add    <opencode-dir> <repo>
    opencode-config.py skills-remove <opencode-dir> <repo>

sync applies a selection file written by kit.py. Skills go in the 'skills'
array: the whole skills/ directory when every skill is chosen, so skills added
later show up on their own, and one entry per skill otherwise. Each chosen
mcp/<name>.json puts its server under mcp.servers and, when it sets
other_agents, appends a global "<name>_*" rule with that effect, so agents
that do not allow the server themselves are asked or denied. remove takes all
of it back out; skills-add and skills-remove touch only the skills.

Only the kit's own entries change: a server you configured differently under
the same name keeps your entry, and only its permission rule follows the
selection. Edits opencode.json when present,
otherwise opencode.jsonc, and creates opencode.json when neither exists. JSONC
files with comments are left alone: the script prints what to set by hand and
exits 2.
"""

import json
import os
import sys
from pathlib import Path


def config_path(opencode_dir: Path) -> Path:
    for name in ("opencode.json", "opencode.jsonc"):
        if (opencode_dir / name).exists():
            return opencode_dir / name
    return opencode_dir / "opencode.json"


def portable(path: Path) -> str:
    """Prefer a ~/ path so the entry survives copying config to another machine."""
    home = Path(os.path.expanduser("~"))
    try:
        return "~/" + str(path.resolve().relative_to(home.resolve()))
    except ValueError:
        return str(path.resolve())


def load(path: Path, quiet: bool = False):
    if not path.exists():
        return {"$schema": "https://opencode.ai/config.json"}
    text = path.read_text()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        if not quiet:
            print(f"{path} is not plain JSON ({err.msg} at line {err.lineno}).", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        if not quiet:
            print(f"{path} does not contain a JSON object.", file=sys.stderr)
        return None
    return data


def save(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


class Refusal(Exception):
    pass


# Skills


def skill_ids(skills_dir: Path) -> list:
    """Every subdirectory holding a SKILL.md, by name, which is also the skill ID."""
    if not skills_dir.is_dir():
        return []
    return sorted(p.name for p in skills_dir.iterdir() if not p.name.startswith(".") and (p / "SKILL.md").is_file())


def target(entry, skills_dir: Path):
    """The path an entry names when it is <skills_dir> itself or a skill inside it, else None."""
    if not isinstance(entry, str) or not (entry.startswith("~") or os.path.isabs(entry)):
        return None
    path = Path(os.path.expanduser(entry)).resolve()
    root = skills_dir.resolve()
    return path if path == root or path.parent == root else None


def registered(opencode_dir: Path, skills_dir: Path):
    """The skill IDs the config takes from <skills_dir>, and its entries for missing skills.

    The IDs are None when the config cannot be read as plain JSON.
    """
    data = load(config_path(opencode_dir), quiet=True)
    if data is None:
        return None, []
    sources = data.get("skills", [])
    ids, stale = set(), []
    for entry in sources if isinstance(sources, list) else []:
        path = target(entry, skills_dir)
        if path is None:
            continue
        if path == skills_dir.resolve():
            ids.update(skill_ids(skills_dir))
        elif (path / "SKILL.md").is_file():
            ids.add(path.name)
        else:
            stale.append(entry)
    return ids, stale


def wanted_skills(skills_dir: Path, chosen) -> list:
    available = skill_ids(skills_dir)
    picked = [s for s in available if s in set(chosen)]
    if picked and len(picked) == len(available):
        return [portable(skills_dir)]
    return [portable(skills_dir / s) for s in picked]


def sync_skills(data: dict, skills_dir: Path, want: list, where: Path) -> list:
    sources = data.get("skills", [])
    if not isinstance(sources, list):
        raise Refusal(f"{where}: 'skills' is not an array, refusing to edit.")

    # Keep the kit's entries where the first one was, in case the order was chosen on purpose.
    kept, at = [], None
    for entry in sources:
        if target(entry, skills_dir) is None:
            kept.append(entry)
        elif at is None:
            at = len(kept)
    at = len(kept) if at is None else at
    updated = kept[:at] + want + kept[at:]
    if updated == sources:
        return []

    notes = [f"skills entry removed from {where}: {e}" for e in sources if target(e, skills_dir) is not None and e not in want]
    notes += [f"skills entry added to {where}: {e}" for e in want if e not in sources]
    if updated:
        data["skills"] = updated
    else:
        data.pop("skills", None)
    return notes


# MCP servers


def servers(repo: Path) -> dict:
    """The kit's server definitions, mcp/<name>.json, by name."""
    found = {}
    directory = repo / "mcp"
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        if path.name.startswith("."):
            continue
        spec = json.loads(path.read_text())
        if not isinstance(spec, dict) or not isinstance(spec.get("server"), dict):
            raise Refusal(f"{path}: expected an object with a 'server' object.")
        found[path.stem] = spec
    return found


def rule(name: str, effect: str) -> dict:
    return {"action": f"{name}_*", "resource": "*", "effect": effect}


def legacy(data: dict) -> list:
    """Servers listed directly under 'mcp', the V1 layout."""
    mcp = data.get("mcp")
    if not isinstance(mcp, dict):
        return []
    return [k for k, v in mcp.items() if k not in ("servers", "timeout") and isinstance(v, dict)]


def configured(data: dict, name: str):
    """The server the config defines under <name>: mcp.servers.<name>, or the V1 mcp.<name>.

    A V1 entry is returned as a marker that never equals a kit definition, so it always counts as yours.
    """
    mcp = data.get("mcp")
    if not isinstance(mcp, dict):
        return None
    current = mcp.get("servers")
    if isinstance(current, dict) and name in current:
        return current[name]
    if name in legacy(data):
        return {"V1 layout": mcp[name]}
    return None


def differences(entry, server: dict) -> list:
    if not isinstance(entry, dict):
        return ["not an object"]
    if "V1 layout" in entry:
        return ["V1 layout"]
    return sorted(k for k in set(entry) | set(server) if entry.get(k) != server.get(k))


def server_state(opencode_dir: Path, repo: Path):
    """Which kit servers the config holds as defined ('ours'), or differently ('foreign', with the keys
    that differ), and which have the kit's other_agents rule in place ('ruled'). All None when unreadable.
    """
    data = load(config_path(opencode_dir), quiet=True)
    if data is None:
        return None, None, None
    rules = data.get("permissions") if isinstance(data.get("permissions"), list) else []
    ours, foreign, ruled = set(), {}, set()
    for name, spec in servers(repo).items():
        if spec.get("other_agents") and rule(name, spec["other_agents"]) in rules:
            ruled.add(name)
        entry = configured(data, name)
        if entry is None:
            continue
        if entry == spec["server"]:
            ours.add(name)
        else:
            foreign[name] = differences(entry, spec["server"])
    return ours, foreign, ruled


def sync_servers(data: dict, repo: Path, chosen: set, where: Path) -> list:
    notes = []
    for name, spec in servers(repo).items():
        server, entry = spec["server"], configured(data, name)
        own = rule(name, spec["other_agents"]) if spec.get("other_agents") else None
        if name in chosen and entry is None:
            mcp = data.setdefault("mcp", {})
            if not isinstance(mcp, dict) or not isinstance(mcp.setdefault("servers", {}), dict):
                raise Refusal(f"{where}: 'mcp' or 'mcp.servers' is not an object, refusing to edit.")
            mcp["servers"][name] = server
            entry = server
            notes.append(f"MCP server added to {where}: {name}")
            if server.get("type") == "remote" and server.get("oauth") is not False:
                notes.append(f"  sign in once: /mcps in OpenCode, or opencode mcp auth {name}")
        elif name not in chosen and entry == server:
            mcp = data["mcp"]
            del mcp["servers"][name]
            if not mcp["servers"]:
                del mcp["servers"]
            if not mcp:
                del data["mcp"]
            entry = None
            notes.append(f"MCP server removed from {where}: {name}")

        if own is None:
            continue
        rules = data.get("permissions", [])
        if not isinstance(rules, list):
            raise Refusal(f"{where}: 'permissions' is not an array, refusing to edit.")
        keep = name in chosen
        if keep and own not in rules:
            data["permissions"] = rules + [own]
            notes.append(f"permission added to {where}: {own['action']} {own['effect']} for agents that don't allow it")
        elif not keep and own in rules:
            rules = [r for r in rules if r != own]
            if rules:
                data["permissions"] = rules
            else:
                data.pop("permissions", None)
            notes.append(f"permission removed from {where}: {own['action']} {own['effect']}")
    return notes


def by_hand(want_skills: list, chosen: set, repo: Path) -> None:
    print("Set these by hand, keeping your own entries:", file=sys.stderr)
    print(f'  "skills": {json.dumps(want_skills)},', file=sys.stderr)
    specs = {n: s for n, s in servers(repo).items() if n in chosen}
    if specs:
        print(f'  "mcp": {json.dumps({"servers": {n: s["server"] for n, s in specs.items()}})},', file=sys.stderr)
        rules = [rule(n, s["other_agents"]) for n, s in specs.items() if s.get("other_agents")]
        if rules:
            print(f'  "permissions": [..., {", ".join(json.dumps(r) for r in rules)}],', file=sys.stderr)


def main() -> int:
    args = sys.argv[1:]
    commands = {"sync": 4, "remove": 3, "skills-add": 3, "skills-remove": 3}
    if not args or commands.get(args[0]) != len(args):
        print(__doc__.strip(), file=sys.stderr)
        return 2

    command, opencode_dir, repo = args[0], Path(args[1]), Path(args[2])
    skills_dir = repo / "skills"
    chosen_skills, chosen_servers = [], None
    if command == "sync":
        lines = Path(args[3]).read_text().splitlines()
        if not lines:
            print(f"empty selection file: {args[3]}", file=sys.stderr)
            return 2
        chosen_skills = [line.split(" ", 1)[1] for line in lines if line.startswith("skill ")]
        chosen_servers = {line.split(" ", 1)[1] for line in lines if line.startswith("mcp ")}
    elif command == "remove":
        chosen_servers = set()
    elif command == "skills-add":
        chosen_skills = skill_ids(skills_dir)
    want = wanted_skills(skills_dir, chosen_skills)

    path = config_path(opencode_dir)
    data = load(path)
    try:
        if data is None:
            by_hand(want, chosen_servers or set(), repo)
            return 2
        before = json.dumps(data, sort_keys=True)
        notes = sync_skills(data, skills_dir, want, path)
        if chosen_servers is not None:
            notes += sync_servers(data, repo, chosen_servers, path)
    except Refusal as err:
        print(err, file=sys.stderr)
        return 2

    if notes:
        print("\n".join(notes))
    if json.dumps(data, sort_keys=True) == before:
        print(f"skills and MCP entries already up to date in {path}")
    else:
        save(path, data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
