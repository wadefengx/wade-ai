#!/usr/bin/env bash
# Create .ai/CONTEXT.md from the wade-ai template in the current project, kept out of git.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
top="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
dest="$top/.ai/CONTEXT.md"
if [ -e "$dest" ]; then echo "exists $dest"; exit 0; fi
mkdir -p "$top/.ai"
tpl="$(cat "$root/templates/CONTEXT.md")"
printf '%s%s%s\n' "${tpl%%<需求名>*}" "${1:-<需求名>}" "${tpl#*<需求名>}" > "$dest"
if git rev-parse --git-dir >/dev/null 2>&1; then
  ex="$(git rev-parse --git-path info/exclude)"
  mkdir -p "$(dirname "$ex")"
  # Only the relay files; a project may commit other things under .ai/.
  for pat in /.ai/CONTEXT.md /.ai/notes/; do
    grep -qxF "$pat" "$ex" 2>/dev/null || echo "$pat" >> "$ex"
  done
fi
echo "wrote $dest"
