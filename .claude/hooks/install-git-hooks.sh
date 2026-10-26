#!/usr/bin/env bash
# SessionStart hook. Puts the commit-ownership commit-msg hook into this clone.
# It runs in local and cloud sessions, so a fresh cloud clone gets the hook.
# It never replaces a commit-msg hook from another tool.
dir="${CLAUDE_PROJECT_DIR:-.}"
src="$dir/.claude/hooks/commit-msg"
hooks=$(git -C "$dir" rev-parse --git-path hooks 2>/dev/null) || exit 0
case "$hooks" in /*) ;; *) hooks="$dir/$hooks" ;; esac
dst="$hooks/commit-msg"
[ -f "$src" ] || exit 0
if [ -e "$dst" ] && ! grep -q 'marker: commit-ownership' "$dst"; then
    exit 0
fi
mkdir -p "$hooks" && cp "$src" "$dst" && chmod +x "$dst"
exit 0
