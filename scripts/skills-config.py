#!/usr/bin/env python3
"""Add, remove or check the skills source in an OpenCode config file.

    skills-config.py add    <opencode-dir> <skills-path>
    skills-config.py remove <opencode-dir> <skills-path>
    skills-config.py check  <opencode-dir> <skills-path>

Edits opencode.json when present, otherwise opencode.jsonc, and creates
opencode.json when neither exists. JSONC files with comments are left alone:
the script prints the snippet to add by hand and exits 2.
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


def load(path: Path):
    if not path.exists():
        return {"$schema": "https://opencode.ai/config.json"}
    text = path.read_text()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        print(f"{path} is not plain JSON ({err.msg} at line {err.lineno}).", file=sys.stderr)
        print("Add this entry by hand, inside the top-level object:", file=sys.stderr)
        print('  "skills": ["<repo>/skills"],', file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"{path} does not contain a JSON object.", file=sys.stderr)
        return None
    return data


def save(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    command, opencode_dir, skills_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    path = config_path(opencode_dir)
    entry = portable(skills_dir)

    if command == "check":
        data = load(path)
        if data is None:
            return 1
        return 0 if entry in data.get("skills", []) else 1

    data = load(path)
    if data is None:
        return 2

    sources = data.get("skills", [])
    if not isinstance(sources, list):
        print(f"{path}: 'skills' is not an array, refusing to edit.", file=sys.stderr)
        return 2

    if command == "add":
        if entry in sources:
            print(f"skills entry already present in {path}")
            return 0
        sources.append(entry)
    elif command == "remove":
        if entry not in sources:
            print(f"skills entry not present in {path}")
            return 0
        sources = [s for s in sources if s != entry]
    else:
        print(f"unknown command: {command}", file=sys.stderr)
        return 2

    if sources:
        data["skills"] = sources
    else:
        data.pop("skills", None)

    save(path, data)
    verb = "added to" if command == "add" else "removed from"
    print(f"skills entry {verb} {path}: {entry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
