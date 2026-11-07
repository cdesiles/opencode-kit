#!/usr/bin/env bash
# Wire this repo into an OpenCode config directory.
#
#   wire.sh install   <opencode-dir> <repo> [link|copy] [selection-file]
#   wire.sh uninstall <opencode-dir> <repo>
#
# install puts the agents/*.md and commands/*.md files named in the selection
# file (written by kit.py) into <opencode-dir> as symlinks (default) or
# copies, and symlinks the lib/* directories it names, so scripts keep
# resolving their node_modules inside the repo. Without a selection file it
# wires everything. Anything replaced is moved aside to <name>.bak.<timestamp>.
# Whatever the selection leaves out is removed the way uninstall removes it:
# only links into the repo and unmodified copies go, and the newest backup
# comes back.

set -euo pipefail

action=${1:?usage: wire.sh <install|uninstall> <opencode-dir> <repo> [link|copy] [selection-file]}
opencode_dir=${2:?missing opencode directory}
repo=${3:?missing repo path}
mode=${4:-link}
selection=${5:-}

agents_dir="$opencode_dir/agents"
commands_dir="$opencode_dir/commands"
lib_dir="$opencode_dir/lib"

if [ -n "$selection" ] && [ ! -s "$selection" ]; then
	echo "empty or missing selection file: $selection" >&2
	exit 2
fi

# Newest backup of a path, if any.
latest_backup() {
	local target=$1 backup
	backup=$(ls -d "$target".bak.* 2>/dev/null | tail -1) || true
	printf '%s' "$backup"
}

# Whether <dest> is what install put there for <src>: a link to it, or an unmodified copy.
ours() {
	local src=$1 dest=$2
	if [ -L "$dest" ]; then
		[ "$dest" -ef "$src" ]
	else
		[ -f "$dest" ] && cmp -s "$src" "$dest"
	fi
}

# Whether the selection names "<kind> <name>". Everything counts when there is none.
selected() {
	[ -z "$selection" ] || grep -qxF "$1 $2" "$selection"
}

place_file() {
	local src=$1 dest=$2
	if [ -e "$dest" ] && [ ! -L "$dest" ] && ! ours "$src" "$dest"; then
		mv "$dest" "$dest.bak.$(date +%Y%m%d-%H%M%S)"
		echo "backed up $dest"
	fi
	rm -f "$dest"
	if [ "$mode" = "copy" ]; then
		cp "$src" "$dest"
		echo "copied  $dest"
	else
		ln -s "$src" "$dest"
		echo "linked  $dest -> $src"
	fi
}

place_dir() {
	local src=$1 dest=$2
	if [ -e "$dest" ] && [ ! -L "$dest" ]; then
		mv "$dest" "$dest.bak.$(date +%Y%m%d-%H%M%S)"
		echo "backed up $dest"
	fi
	rm -rf "$dest"
	ln -s "$src" "$dest"
	echo "linked  $dest -> $src"
}

remove_path() {
	local src=$1 dest=$2 backup
	if ours "$src" "$dest"; then
		rm -f "$dest"
		echo "removed  $dest"
	fi
	if [ -e "$dest" ] || [ -L "$dest" ]; then
		return 0
	fi
	backup=$(latest_backup "$dest")
	if [ -n "$backup" ]; then
		mv "$backup" "$dest"
		echo "restored $dest from $backup"
	fi
}

# Place <src> at <dest> when install selects it, otherwise take it back out.
wire() {
	local kind=$1 src=$2 dest=$3
	if [ "$action" = uninstall ] || ! selected "$kind" "$(basename "$dest" .md)"; then
		remove_path "$src" "$dest"
	elif [ -d "$src" ]; then
		place_dir "$src" "$dest"
	else
		place_file "$src" "$dest"
	fi
}

case "$action" in
install)
	mkdir -p "$agents_dir" "$commands_dir" "$lib_dir"
	;;
uninstall) ;;
*)
	echo "unknown action: $action" >&2
	exit 2
	;;
esac

for f in "$repo"/agents/*.md; do
	[ -e "$f" ] || continue
	wire agent "$f" "$agents_dir/$(basename "$f")"
done
for f in "$repo"/commands/*.md; do
	[ -e "$f" ] || continue
	wire command "$f" "$commands_dir/$(basename "$f")"
done
for d in "$repo"/lib/*/; do
	[ -d "$d" ] || continue
	wire lib "${d%/}" "$lib_dir/$(basename "$d")"
done
