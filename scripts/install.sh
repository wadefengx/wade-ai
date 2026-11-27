#!/usr/bin/env bash
# Link wade-ai/AGENTS.md into user-level instruction entries.
# Usage: install.sh                 known entries of installed tools
#        install.sh <path>...       any other harness: link AGENTS.md at the given paths
# Idempotent. Existing files that are not our link are left untouched and reported.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
src="$root/AGENTS.md"

if [ $# -gt 0 ]; then
  for t in "$@"; do
    if [ -L "$t" ] && [ "$(readlink "$t")" = "$src" ]; then echo "ok    $t"
    elif [ -e "$t" ] || [ -L "$t" ]; then echo "WARN  $t exists; left untouched"
    else mkdir -p "$(dirname "$t")" && ln -s "$src" "$t" && echo "link  $t -> $src"; fi
  done
  exit 0
fi

link() { # link <tool home> <target>
  local home="$1" target="$2"
  [ -d "$home" ] || { echo "skip  $target (tool not installed)"; return; }
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$src" ]; then
    echo "ok    $target"
  elif [ -e "$target" ] || [ -L "$target" ]; then
    echo "WARN  $target exists; merge it into wade-ai or remove it, then rerun"
  else
    mkdir -p "$(dirname "$target")" && ln -s "$src" "$target" && echo "link  $target -> $src"
  fi
}

# Claude Code: import instead of symlink (symlinked CLAUDE.md is skipped in some sessions).
claude="$HOME/.claude/CLAUDE.md"
if [ -d "$HOME/.claude" ]; then
  if [ ! -e "$claude" ]; then
    printf '@%s\n' "$src" > "$claude" && echo "write $claude"
  elif grep -qxF "@$src" "$claude"; then
    echo "ok    $claude"
  else
    echo "WARN  $claude exists; add this line yourself: @$src"
  fi
else
  echo "skip  $claude (tool not installed)"
fi

codex="${CODEX_HOME:-$HOME/.codex}"
copilot="${COPILOT_HOME:-$HOME/.copilot}"
dsh="${DSH_HOME:-$HOME/.dsh}"

link "$codex"                "$codex/AGENTS.md"
link "$copilot"              "$copilot/instructions/wade-ai.instructions.md"
link "$HOME/.config/opencode" "$HOME/.config/opencode/AGENTS.md"
link "$dsh"                  "$dsh/AGENTS.md"
