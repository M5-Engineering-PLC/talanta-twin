#!/usr/bin/env bash
# PreToolUse hook. The person who runs the session owns every commit, PR, and
# comment. AI tools are never an author, co-author, or committer.
#
# Blocks:
#   - AI co-author trailers, "Generated with <AI>" lines, AI noreply emails,
#     in any Bash command and in any MCP tool input (for example GitHub tools)
#   - git author or committer overrides (--author, -c user.*, GIT_AUTHOR_*,
#     GIT_COMMITTER_*, git config user.*)
#   - git commit when the configured identity is empty or is an AI identity
#
# The session owner sets their identity outside the session: with their own
# git config on a local PC, or with GIT_AUTHOR_* / GIT_COMMITTER_* variables on
# their cloud environment. Exit 2 = block. stderr goes back to the model.

input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')
if [ "$tool" = "Bash" ]; then
    text=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
else
    text=$(printf '%s' "$input" | jq -c '.tool_input // empty')
fi
[ -z "$text" ] && exit 0

block() {
    echo "BLOCKED by commit-ownership-guard: $1" >&2
    echo "Commits, PRs, and comments belong to the person who runs this session. Use their own git identity. Add no AI attribution and no author override." >&2
    [ -n "$2" ] && echo "$2" >&2
    exit 2
}

ai='(claude|anthropic|codex|openai|chatgpt|gpt-[0-9]|copilot|gemini|cursor ?agent|devin)'
re_coauthor="co-authored-by:[^\"'\\n]*${ai}"
re_generated="generated (with|by) \\[?${ai}"
re_ai_mail='(noreply@anthropic\.com|noreply@openai\.com|copilot@users\.noreply\.github\.com)'

# Check attribution text only where it can reach a commit, a PR, or a comment:
# git and gh commands, and MCP tools for GitHub or GitLab. Other commands can
# mention these strings (docs, searches). The git commit-msg hook catches a
# message that arrives some other way, for example from a file.
if [ "$tool" = "Bash" ]; then
    printf '%s' "$text" | grep -qE '(^|[^[:alnum:]_.-])(git|gh)([[:space:]]|$)' || exit 0
else
    printf '%s' "$tool" | grep -qiE 'github|gitlab' || exit 0
fi

printf '%s' "$text" | grep -qiE "$re_coauthor" && block "AI Co-Authored-By trailer"
printf '%s' "$text" | grep -qiE "$re_generated" && block "\"Generated with <AI>\" line"
printf '%s' "$text" | grep -qiE "$re_ai_mail" && block "AI email address in a commit, PR, or comment"

[ "$tool" = "Bash" ] || exit 0
printf '%s' "$text" | grep -qE '\bgit\b' || exit 0

printf '%s' "$text" | grep -qE -- '--author[= ]' && block "git --author override"
printf '%s' "$text" | grep -qE -- '-c +user\.(name|email)=' && block "git -c user.name/user.email override"
printf '%s' "$text" | grep -qE 'GIT_(AUTHOR|COMMITTER)_(NAME|EMAIL)=' && block "GIT_AUTHOR/GIT_COMMITTER override in the command"
printf '%s' "$text" | grep -qE 'git +(-C +[^ ]+ +)?config( +--[a-z-]+)* +user\.(name|email) +[^;&|[:space:]]' \
    && block "changing git user.name/user.email" "The person who runs the session must set their identity outside the session."

# Before a commit, check the identity that git will use. Use the -C folder of
# the command if it has one, otherwise the session folder.
if printf '%s' "$text" | grep -qE '\bgit\b([^;&|]*)\bcommit\b'; then
    dir=$(printf '%s' "$text" | sed -nE 's/.*git +-C +("([^"]+)"|([^ ]+)).*/\2\3/p' | head -n1)
    dir=${dir:-$(printf '%s' "$input" | jq -r '.cwd // empty')}
    dir=${dir:-.}
    for v in GIT_AUTHOR_IDENT GIT_COMMITTER_IDENT; do
        ident=$(git -C "$dir" var "$v" 2>/dev/null) || block "git has no $v identity set" \
            "Set the session owner's identity: git config on a local PC, or GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME and GIT_COMMITTER_EMAIL on the cloud environment."
        id=${ident% * *}
        printf '%s' "$id" | grep -qiE "$re_ai_mail|<[^>]*${ai}[^>]*>|^${ai}\b|\[bot\]" \
            && block "git $v is an AI identity: $id" \
                "Set the session owner's identity: git config on a local PC, or GIT_AUTHOR_* and GIT_COMMITTER_* variables on the cloud environment."
    done
fi
exit 0
