# M1 backup comparison and checkpoint — 2026-11-10

Status: IN PROGRESS. Software evidence only; this is not a frozen candidate or device acceptance.

Compared backup `77c375f` with origin work branch `13bb219` (common comparison base `f8289db`). Integration merge `c9a88e0` also carries perimeter release `ee07ff3` and its benchmark parent `affc306`. Backup history remains on `origin/munene/talanta-local-backup-2026-11-09`.

## Menu

Both group registry entries and display claims, disable planned modules and exclude security modules. Origin uses a native modal dialog, case-insensitive security filter, explicit action parser and tested 375px layout changes. Retain it. Backup offers direct menu actions for ENV-01, ENV-02, ENV-03, AMB-02, AMB-03 and CAM-07; ported these mappings to the origin dialog and tested the parser and registry. Mode actions open the existing venue or weather mode; they do not themselves assert a particular time, rain setting or individual tree. Tour reuses the existing tour control. Browser interaction and focus checks remain open.

## First load

Both restrict phones to their own manifest and defer later light sets. Origin explicitly identifies the missing phone manifest in its failure and supports a requested seek during preparation. Backup waits for the first selected set to be applied and delays later preloads until after painted frames, with additional mocked tests, byte estimator and phone cache handling. Origin preloads the requested set rather than applying it in preparation, and schedules idle work without the backup's double-animation-frame guard. These are real behavior differences: compare seek during loading, first painted frame, phone cache and interruption in browser before selecting or adapting the safer parts. No loading code was ported yet; do not mark M1 complete.

## Pass K

Both record Munene's 2026-10-24 approval of L06/L07. Origin states it prominently and cites both sources; retain origin. Neither is a current demo acceptance.

## Verification and next actions

- At `c9a88e0`, `npx vite build` passed (107 modules); the perimeter exporter succeeded, producing 8,558,496-byte hero and 8,575,588-byte site files. Rebuild after the menu changes.
- Windows `npm test` at `c9a88e0` before the menu port: 192 tests, 181 pass, 11 fail; detailed output `m1_test_windows_2026-11-10.log`. Failures include Windows `/C:` URL pathname assumptions, archive/test command issues, and linker checks. One prior run also exposed CRLF byte equality in the generated seat palette. These are not evidence of a clean candidate.
- `node app/tools/link_bundle.mjs --help` actually ran the linker and failed at `ground/tiles.json` size mismatch. Checkout CRLF conversion is a likely cause and must be verified against raw Git blob hashes. The linker may require symlink privileges. Do not claim bundle integrity.
- Menu-specific software tests after port: 7 passed, 0 failed. Run complete suite on a byte-preserving checkout in a portable Linux environment or fix Windows path/line-ending assumptions, then rerun the bundle integrity check and build on the final commit.
- M3 independent software check reported by the lead: all five raw Git blobs at `c14cc71` root (README, checksum manifest, tar.000, tar.001, tar.002) had matching SHA-256 values against `origin/main` `88e04ce` under `assets/render_pack`. Branch deletion still requires Munene's approval.
- No push or main merge performed. M2 requires explicit approval of the exact candidate; device, layout, road, panorama, GPU and H0 gates remain open. Kaggle was not used.
