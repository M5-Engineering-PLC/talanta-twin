# Commit ownership

The person who runs the session owns every commit, pull request, and comment. This rule applies in local sessions and in cloud sessions. An AI tool is never an author, a co-author, or a committer.

- Commit with the git identity of the person who runs the session.
- Do not add a `Co-Authored-By` trailer for Claude, Codex, or any other AI tool.
- Do not add a "Generated with Claude Code" line or a claude.ai session link to a commit message or a PR body.
- Do not use `--author`, `git -c user.name`, `git -c user.email`, or `GIT_AUTHOR_*` / `GIT_COMMITTER_*` variables in a command.
- Do not change `git config user.name` or `git config user.email`.
- If git has no identity, or the identity is an AI identity, stop. Tell the person to set their own identity:
  - On a local PC, they set their own `git config`.
  - In a cloud session, they set `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` on their cloud environment.

The hook `.claude/hooks/commit-ownership-guard.sh` and the git hook `commit-msg` enforce this rule. The GitHub check `commit-ownership` also checks each pull request and each push to `main`. Do not turn off or work around these checks.
