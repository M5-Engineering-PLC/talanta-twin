# Handoff: where the Talanta twin is parked

Updated: 2026-10-19. Read this file first on a new device or with a new coding agent. Then read AGENTS.md, then blender/STATUS.md.

## Where the work is

| what | where |
|---|---|
| Main work branch (model, bakes, app) | `claude/hopeful-archimedes-lo15is` on origin |
| Baked web hero bundle (148.95 MB, 70 files) | GitHub prerelease `web_hero_v1`, asset `web_hero_v1.tar` |
| Bundle manifest (size and sha256 per file) | blender/web_hero/web_hero_v1_manifest.json, and the release asset `web_hero_v1_manifest.json` |
| Bundle as a git branch (backup copy) | `assets/web_hero_v1` (orphan branch, no shared history) |
| Baked blend and bake maps (backup copy) | `assets/web_hero_v1_bake` (orphan branch) |
| Fetch script for the bundle | app/tools/fetch_assets.mjs (`npm run fetch-assets`), tests in app/tools/fetch_assets.test.mjs |
| Landing concept images (internal only, frame-derived) | `munene/CAM-01-landing-option` |
| Cloud handoff for blender/ and gis/ | blender/STATUS.md |

Raw videos and the dense frame sets exist only on the lead machine. They are not needed to continue the build.

## Start on a new device

1. Clone the repository and check out the work branch:
   `git clone https://github.com/M5-Engineering-PLC/talanta-twin.git && cd talanta-twin && git switch claude/hopeful-archimedes-lo15is`
2. Set your git identity to your own name and email. Do not commit as an AI identity.
3. Install the app: `cd app && npm install`.
4. Get the bundle: `gh release download web_hero_v1 -R M5-Engineering-PLC/talanta-twin -D /tmp/web_hero_v1`.
5. Check the archive: `cd /tmp/web_hero_v1 && sha256sum -c web_hero_v1.tar.sha256`.
6. Extract the archive outside the repository. Or skip steps 4 to 6: run `npm run fetch-assets` in app/. It downloads the release with gh, checks each file against the manifest and installs it into app/public.
7. Run `npm run dev` in app/. Use Chrome or another browser with WebGPU or WebGL. Open `/?hero` for the baked scene.

Do not commit anything from app/public/models, app/public/env or app/public/ground. They are binaries.

## Next tasks, in order

The path to the landing mockups 06 and 07 (work items L1 to L8 and three open decisions) is in PLAN.md section 12. Tasks 2, 3 and 5 below are L4 and L3 there.

1. App: run `npm run fetch-assets` once against the real web_hero_v1 release on a laptop with gh logged in, then open `/?hero`. The script is finished and passes `npm test` (fake bundle and fake gh, 7 cases), but it has not yet downloaded the real release. Until the app reads EXR (task 3), it points both panorama sizes at the 2048 HDR and lists the 8K EXR as `file_exr`.
2. App: load the 61 ground tiles near the camera first. Fall back to the current ground_site.jpg when the tiles are missing.
3. App: load the 8K EXR panorama when the device can take it. Else load the 2048 HDR.
4. Done (2026-10-19): the landing caption reads "60,000 design capacity"; the procedural seat count is gone from it.
5. Blender (cloud): fix the pale pink-grey blotches on the near ground and the ground tiles. Re-export the ground tiles only.
6. Blender (cloud): the build has 63,949 places against the narrated 60,000. Check the upper tier depth and overhang, and cut the vomitories. Keep the 0.5 m seat pitch.
7. Blender (cloud): group 3 PL rows on the matchday camera only (see blender/STATUS.md).
8. Test the landing at 375 px phone width on a real phone. A headless check at 375 x 812 (?hero, Hillside, morning) showed no horizontal scroll and no overlap.

App tasks run on a laptop. Bakes, renders and exports run in the cloud chat. A new bundle gets a new release tag (web_hero_v2). Do not replace the files in web_hero_v1.

## Status by area

| area | done | what is left |
|---|---|---|
| Exterior shape and roof | about 85 % | Heights are kept, not measured. A measured section would settle them. |
| Landing interface | about 85 % | Real phone test |
| Bake and environment bundle | about 80 % | Ground blotches |
| Interior, bowl camera features | about 65 % | Media offices and tunnel side are placeholders; group 3 |
| Seat count and tier rows | about 50 % | 6.6 % over; the implied treads and risers are not plausible |
| Live twin with the baked scene | about 30 % | Tasks 1 to 3 above |
| Public-ready output | about 15 % | Nothing is cleared for public use |

## Rules for every agent

- Frames, Google Earth captures and concept images are internal reference only. Never use them as textures or in public output.
- No security detail in public output: no gates, turnstiles, exits, exit signs, CCTV, control rooms or access routes.
- People and crowds are labelled Visualization. Do not name the architect or the guides. Do not copy sign or door text.
- Video oL3wsPsx4Jw is never used for geometry. PWj9s_v3G6U and "Nyayo" frames are show and lighting references only.
- No sacco names or logos on vehicles. Credit the CC-BY nganya model.
- Work on branches. Never rewrite main. Commit as the person who runs the session, with no AI attribution.
- Keep the repository private.

## Open decisions for Munene

- Delete the old remote branches codex/lookdev, codex/shield-fix, codex/suburbs and web/hero-match.
- Remove the old web-crowd and web-tour worktrees. The web-crowd worktree holds an uncommitted app/src/hero/crowd.js.
- Delete the `assets/` branches after a second device has fetched the release once.
- Reinstall the Codex CLI: `npm install -g @openai/codex@latest`.
