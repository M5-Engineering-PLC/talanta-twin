# Branch rules

These rules apply to every repository in M5-Engineering-PLC. Adopted on 2026-10-20.

## Rules

- `main` is the only long-lived branch.
- Make one short-lived branch for each piece of work.
- Name the branch `type/short-topic`. Use one of these types: `feat/`, `fix/`, `docs/`, `hw/`, `wo/`.
- Put every change into `main` through a pull request. Only nenemwaniki approves changes to `main`.
- GitHub deletes the branch automatically after the merge.
- Keep backups and archives as tags named `archive/<topic>`, not as branches.
- Keep large binary files in GitHub Releases, not in branches.
- If a branch has no commits for 14 days, open a pull request or delete the branch.

## Before you delete a branch

Make sure that `main`, a tag, or a release contains all the commits of the branch. Then delete it.
