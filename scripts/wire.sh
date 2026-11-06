#!/usr/bin/env bash
# Wire this repo into an OpenCode config directory.
#
#   wire.sh install   <opencode-dir> <repo> [link|copy]
#   wire.sh uninstall <opencode-dir> <repo>
#
# every agents/*.md and commands/*.md file becomes a symlink (default) or a copy
# inside <opencode-dir>; every lib/* directory is always symlinked, so scripts
# keep resolving their node_modules inside the repo. Anything replaced is moved
# aside to <name>.bak.<timestamp> and restored by uninstall.

set -euo pipefail

action=${1:?usage: wire.sh <install|uninstall> <opencode-dir> <repo> [link|copy]}
opencode_dir=${2:?missing opencode directory}
repo=${3:?missing repo path}
mode=${4:-link}

agents_dir="$opencode_dir/agents"
commands_dir="$opencode_dir/commands"
lib_dir="$opencode_dir/lib"

# Newest backup of a path, if any.
latest_backup() {
	local target=$1 backup
	backup=$(ls -d "$target".bak.* 2>/dev/null | tail -1) || true
	printf '%s' "$backup"
}

place_file() {
	local src=$1 dest=$2
	if [ -e "$dest" ] && [ ! -L "$dest" ]; then
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
	local target=$1 backup
	if [ -L "$target" ]; then
		rm -f "$target"
		echo "removed  $target"
	fi
	backup=$(latest_backup "$target")
	if [ -n "$backup" ]; then
		mv "$backup" "$target"
		echo "restored $target from $backup"
	fi
}

case "$action" in
install)
	mkdir -p "$agents_dir" "$commands_dir" "$lib_dir"
	for f in "$repo"/agents/*.md; do
		[ -e "$f" ] || continue
		place_file "$f" "$agents_dir/$(basename "$f")"
	done
	for f in "$repo"/commands/*.md; do
		[ -e "$f" ] || continue
		place_file "$f" "$commands_dir/$(basename "$f")"
	done
	for d in "$repo"/lib/*/; do
		[ -d "$d" ] || continue
		place_dir "${d%/}" "$lib_dir/$(basename "$d")"
	done
	;;
uninstall)
	for f in "$repo"/agents/*.md; do
		[ -e "$f" ] || continue
		remove_path "$agents_dir/$(basename "$f")"
	done
	for f in "$repo"/commands/*.md; do
		[ -e "$f" ] || continue
		remove_path "$commands_dir/$(basename "$f")"
	done
	for d in "$repo"/lib/*/; do
		[ -d "$d" ] || continue
		remove_path "$lib_dir/$(basename "$d")"
	done
	;;
*)
	echo "unknown action: $action" >&2
	exit 2
	;;
esac
