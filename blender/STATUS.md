# Status and handoff: blender/ and web hero (branch claude/hopeful-archimedes-lo15is)

Written 2026-10-19 for the next coding agent. Last code commit before this file: 760db75. Read AGENTS.md first.

## Rules carried from the lead (Munene)

- Work on `claude/hopeful-archimedes-lo15is`. Push after each step, with a time estimate and a report. Merge, never
  rebase, when the remote is ahead.
- Commit with plain `git commit` as the repo identity munene <nenemwaniki@gmail.com>. If git shows no identity or
  shows Claude, stop and tell the lead. Do not touch /root/.gitconfig. No Claude attribution trailers.
- Ownership: blender/ and app/public/models|env are ours. Do not edit app/src, app/index.html or main.js. After a
  blockout rebuild, restore app/public/data/blockout.glb with `git checkout`.
- Never commit binaries (GLB, KTX2, EXR, HDR, blend, bake maps) or raw video. Frames are internal reference only:
  never in a build, texture, pitch or public page.
- Interior: no control rooms, CCTV, access control, gate hardware, gates, exits or signs (IF62, IF69 stay out). No
  sign or door text. People and crowds are labelled Visualization. No architect or guide names in public output.
- oL3wsPsx4Jw is not used for geometry. PWj9s_v3G6U and "Nyayo" frames are show and lighting references only.
- Do not let the session idle while renders or bakes run. Keep each poll under 10 minutes. Start background jobs
  with `setsid`. Do not use `pkill -f`/`pgrep -f` with a pattern in the same command line (it matches its own shell);
  kill by pid.

## Where things stand

| pass | state | record |
|---|---|---|
| Interior pass 2 (sheet 06, Priority 1 build, C30-C35) | done | blender/renders/interior_pass_02/README.md |
| Geometry pass 2 (opening ring, landmarks, LOO) | done; pf foot_inset, wall_bulge, shield centre derived | blender/renders/geometry_pass_02/ |
| Geometry pass 3 (crest prior, last height fit) | rule failed; build values kept | blender/renders/geometry_pass_03/README.md |
| Tier section 01 (row counts) | rows 15 / 12 / 32 derived; tread/riser fit rejected | blender/renders/tier_section_01/README.md |
| Bake (all groups, maps/stages.json) | done | blender/out/web_hero/bake_log.json (local) |
| Environment pass web_hero_v1 | built, 148.95 MB of 250 MB; release upload blocked | blender/web_hero/WEB_HERO_V1.md, web_hero_v1_manifest.json |
| Landing-page preview with the bundle | screenshot taken (Hillside, 07:30) | this file, "App preview" |

Open task lists: Group 3 (PL rows on the matchday camera only) not started. Web hero task: the release step is open.

## Blocked: GitHub prerelease web_hero_v1

Instruction: upload the bundle as prerelease "web_hero_v1"; if releases cannot be created, stop and tell the lead.
This session had no release-create or asset-upload tool and the gh CLI was disallowed, so it stopped there. The
bundle is `blender/out/web_hero/web_hero_v1/` (models/, ground/, env/, manifest.json with size and sha256 per file;
committed copy: blender/web_hero/web_hero_v1_manifest.json).

**The bundle, the baked blend and the bake maps exist only in the container that built them** (blender/out/web_hero/
is git-ignored). If that container is gone, rebuild them:

1. `~/.venvs/bpy/bin/python blender/web_hero/bake_lightmaps.py ...` (about 11 h CPU: albedo 0.44 h, AO 3.60 h,
   light 6.95 h; per-batch times in WEB_HERO_V1.md). Stages are saved to maps/stages.json and reused on restart.
2. `render_panorama.py` for 07:30 (`preset=morning_golden`) and 17:30, 8K, `near=800` (about 22 min each).
3. `ground_tiles.py` (61 tiles, about 2 min each).
4. `export_web.py`, then `node blender/web_hero/node/post_glb.mjs bundle=web_hero_v1` (add `skip_models` to redo only
   tiles, panoramas and manifest).
Check the sha256 values against web_hero_v1_manifest.json only for the deterministic parts; renders will differ.

## App preview (landing page hero)

- `python3 blender/web_hero/stage_app_preview.py` copies the two GLBs and the 2048 HDR into app/public/models and
  app/public/env and writes an app-format manifest. Those folders are listed in .git/info/exclude (local); never
  commit them.
- Serve `app/` with `npx vite --port 5199 --host 127.0.0.1` and open `/?hero`. The hero loads in about 40 s in
  software GL (5.75M triangles, 526 meshes, 304 LOD groups, panorama on).
- `node blender/web_hero/node/shot_hero.mjs "http://127.0.0.1:5199/?hero" out.png 20000` takes the screenshot.

Findings from the preview, for whoever owns them:
- The near ground in the landing view is pale and blotchy (pink-grey patches). The same blotches show in the ground
  tiles. Suspect the terrain material's colour noise or the ground light bake; ours to fix (blender/).
- The landing caption reads "56,972 seats modelled"; the build now has 63,949 places (62,524 bowl, 583 media, 218
  VIP, 624 sky-box estimate). The caption lives in app/src (not ours): tell the app owner.
- The app loads panoramas with HDRLoader only, so the 8K EXR is not used; the 2048 HDR is staged for both sizes. An
  8K HDR or EXR support in the app (app/src, not ours) is needed for the full panorama.

## Open issues to report to the lead

- Capacity: 63,949 places against the narrated 60,000 (+6.6 %). Likely cause: the upper tier is deeper than modelled
  and overhangs the middle tier; vomitories and camera positions are not cut. Seat pitch stays 0.5 m.
- Tier section: implied treads/risers are implausible (lower 1.32/0.75 m, middle 0.91/0.75 m, upper 0.49/0.34 m).
  Needs a measured section or side-on frames with a scale object.
- Heights: the frame fits cannot fix them (geometry pass 3). A measured section is the way forward.
- Media offices and the tunnel side are placeholders.

## Key scripts

- blender/build_blockout.py, build_bowl_detail.py, build_site_detail.py, build_scene.py: the model.
- blender/scripts/make_interior_cameras.py: C30-C35.
- gis/scripts/profile_fit/fit2.py (acceptance rule: max(basin, LOO spread) < 2 m, no value at a bound),
  gis/scripts/tier_section/: row counts and the rejected fit. gis/scripts/build_parameter_ledger.py: the ledger.
- blender/web_hero/: common.py (presets), bake_lightmaps.py, render_panorama.py (camera clip_end 100 km; the
  default 1 km clip had hidden everything beyond it), ground_tiles.py, export_web.py, node/post_glb.mjs,
  stage_app_preview.py, node/shot_hero.mjs.
- Environment: Blender bpy 5.2 in ~/.venvs/bpy; PIL and scipy in ~/.venvs/gis; Node 22 with gltf-transform,
  ktx2-encoder (12.58 Mpix per image limit) and meshoptimizer in blender/web_hero/node.
