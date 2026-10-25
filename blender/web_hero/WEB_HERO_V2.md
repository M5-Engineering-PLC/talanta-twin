# web_hero_v2 bundle (work order engineering/cloud_web_hero_v2_2026-10-24.md)

Environment pass for the web twin on the pass K scene, after Munene approved the 4K stills in
blender/renders/hero_artistic_04/ (2026-10-24). Binaries never go on `wo/web-hero-v2`: the bake maps go to the orphan
branch `assets/web_hero_v2_bake`, the bundle to the orphan branch `assets/web_hero_v2`. The files of `web_hero_v1` are
not changed. The AI image research/reference/dusk_aerial_finished_2026-10-17.jpg is not used anywhere in this pass.

## W1. Scene and export set

Scene: `blender/out/frozen_FK.blend`, a frozen copy of step_FK (pass K, the scene of hero_artistic_04), passed to every
step as `TALANTA_SITE_BLEND`. `common.setup_morning()` now always sets the finished state (`scene_state.set_state`) and
the look layer (`lookdev.apply_lookdev(s, "day")`: material wraps for dirt, colour variation and edge wear; sun angle
0.53 deg, the same as before). The look layer's grade is a camera effect, so the compositor stays off and the view
settings stay as render_cycles.py sets them: bakes, panoramas and ground tiles keep the approved morning tone, and the
app tone-maps. The bake log records the scene (`scene`: state, look layer, blend) and the stage key carries the state
and the look layer, so no map from another scene state can be reused by mistake.

Changes (blender/web_hero/):

| Item | Change |
|---|---|
| W1.1 bake groups | `layout_pass_i` (1024 px: east approach paving, lens island, kerb), `plaza_south` (1024 px: collection `plaza_south_k`), `landmarks` (2048 px: collection `landmarks_pass_j`, walls to 47 m; AO as for the suburbs), all with the `_own_meshes()` filter of `site_layout`. Also `trace_sw` (1024 px: collections `trace_sw_finished`, `trace_structures`: the south-west grass loop, its road and the small stand), which the "grass loop" check needs and which no earlier export carried. One new batch `layout_pass_i+plaza_south+trace_sw+landmarks`. |
| W1.1 export | `SITE_COLS` gains `layout_pass_i`, `landmarks_pass_j`, `plaza_south_k`, `layout_cars_visualization`, `trace_sw_finished`, `trace_structures`. |
| W1.2 cars | `layout_cars_visualization` joins the `traffic` group (lightmap and AO, like `traffic_Visualization`, which is hidden in step_FK) and exports under its own name, "Visualization" kept. |
| W1.3 layout_final | export_web.py stops if the baked scene or a collection to export holds an object of `layout_final` or `layout_final_cars_visualization` (by collection or name prefix). step_FK has none. The `<name>_final` objects in step_FK (roads_final, road_markings_final, trace_tree_0012_final, trace_tree_0055_final) are the finished-state cut copies of passes I and K, not pass F. |
| W1.4 state | The export stops unless the baked scene is the finished state with the look layer. Only objects that render in that state are baked or exported (hide_render after the state switch; `internal_only` stays out). The roads group now bakes `roads_final` (the finished-state cut copy), not the hidden as-built `roads`. |
| W1.5 grass | `trace_sw` ships its albedo map like `sport` (export ALBEDO_GROUPS), so the K4 `training_grass` patches on the south-west lawn survive. Check on the test bake: the patches are in `trace_sw_albedo.png` (green texels: luminance spread 3.5 levels of 255 at quarter size; the 8-20 m patches are visible). The two training pitches carry the same material in the `sport` group, which already ships its albedo map. |
| W1.6 security | No exits, camera positions or control rooms are in these collections. `internal_only` objects (the station brand marks) stay out of bake and export. |
| test | `lightmap_uv.pack` raises `NoFit` when the charts cannot fit; in test mode the atlas doubles until they do (forecourt 46,168 charts, suburbs 104,152 and traffic 17,304 do not fit a quarter-size atlas at the 2 px chart minimum). |

Not exported (finished state renders them, but no order covers them; listed as gaps): `trace_trees` (88 traced trees,
linked copies of the canopy prototypes), `context_l07_visualization` (generic masses and trees placed for the L07
camera only), `people_figures_visualization` (the pass H figures; v1 had no people either), `horizon_context` and
`night_lights` (as in v1: far land in the panorama, night fixtures not in the morning bundle).

### Atlas cover (`bake_lightmaps.py uvonly`, full size)

| Group | Atlas px | Objects | Faces | Charts | Texels per m | Cover |
|---|---|---|---|---|---|---|
| stadium_shell | 2048 | 8 | 8,256 | 964 | 5.78 | 0.53 |
| stadium_fins | 2048 | 1 | 17,040 | 4,089 | 7.55 | 0.60 |
| stadium_ornament | 2048 | 3 | 46,048 | 1,220 | 11.99 | 0.55 |
| roof | 2048 | 3 | 21,060 | 3,492 | 7.33 | 0.52 |
| sport | 1024 | 6 | 7,711 | 511 | 3.22 | 0.41 |
| roads | 2048 | 2 | 15,900 | 3,872 | 4.08 | 0.55 |
| site_built | 1024 | 2 | 168 | 168 | 20.0 | 0.71 |
| suburbs | 4096 | 1 | 104,152 | 104,152 | 2.37 | 0.41 |
| traffic | 2048 | 1 | 17,304 | 17,304 | 7.14 | 0.73 |
| forecourt | 2048 | 131 | 47,038 | 46,168 | 2.90 | 0.27 |
| site_layout | 2048 | 168 | 2,898 | 2,404 | 6.84 | 0.63 |
| station | 1024 | 16 | 91 | 91 | 16.14 | 0.51 |
| layout_pass_i (new) | 1024 | 3 | 1,930 | 108 | 6.68 | 0.43 |
| landmarks (new) | 2048 | 12 | 294 | 213 | 6.20 | 0.70 |
| plaza_south (new) | 1024 | 9 | 2,014 | 150 | 6.57 | 0.47 |
| trace_sw (new) | 1024 | 5 | 124 | 87 | 5.61 | 0.49 |
| ground_00 to ground_23 | 1024 | 1 each | 1,225 (inner) to 11,200 | planar | | 0.99 |

The roads row is from the uvonly run before the `roads_final` fix (ngong_road and ngong_barrier only); the bake log of
the real bake gives the final figures.

### Test bake (`bake_lightmaps.py test`: quarter-size atlases, 4 samples)

57 min on 4 CPU cores: albedo 1,628 s, AO 135 s, light 1,611 s. At quarter size the time is mostly fixed cost per
batch, not texels: the forecourt (131 objects) and site_layout+station (184 objects) batches take 540 to 760 s per
pass however few samples they get, the other batches 20 to 120 s.

### Test export (`export_web.py test`, `node/post_glb.mjs test`)

Passes after three fixes found by the test run:
- the layout_final check first also caught the `<name>_final` cut copies of passes I and K; it now goes by collection
  and the `layout_final` name prefix only;
- the roads group baked the hidden as-built `roads`; it now takes `roads_final` (the finished-state copy) when the
  named object is hidden and its `_final` copy renders;
- post_glb.mjs needs a ground albedo map for the ground meshes (the app keeps them under the ground tiles), but the
  2026-10-20 change had stopped baking it: `ALBEDO_USED` is every group again (about 10 min at 4 samples);
- crown_detail.py made the tree prototypes detailed, so the fixed decimation ratio left 1,000+ triangles per suburbs
  tree (2.6M triangles for 2,424 trees, against 60,600 in v1). Decimated tree LOD0s are now capped at 120 triangles
  (`TREE_PROTO_TRIS`): 93 to 119.

Exported (test): every object of passes I, J and K (pi_ 3, lm_ 12, pk_ 9), the loop and stand (sw_ 5),
`layout_cars_visualization`, `roads_final`, `road_markings_final`; no layout_final object, no station brand mark, no
traffic_Visualization, no people. Triangles (test GLBs): hero LOD0 0.72M; site LOD0 8.89M, LOD1 (300 m) 0.67M, LOD2
(1 km) 0.51M. Of the site LOD0, 7.88M is the canopy: 70,324 instanced trees within +-1,500 m (v1: 31,944) at 112
triangles each (their web_lod mesh); no duplicate positions; 59,408 stand beyond 1 km. They switch to crossed-quad
impostors at 300 m, as in v1. Test GLBs: 38.5 MB (quarter-size maps).

## W2. Reuse and cost

### What can be reused: nothing

- The v1 maps on `assets/web_hero_v1_bake` are lossy (decoded from the KTX2 textures of the v1 GLBs) and cover only
  the maps the v1 GLBs carried.
- Geometry: comparing the v1 baked blend (on that branch) with step_FK object by object (vertex positions and
  transforms rounded to 1 cm): the stadium shell (3 of 8 objects unchanged), fins, ornament, roof, suburbs and all 24
  ground tiles changed (facade fix, replica passes A, B and G, seat count pass 01, pass B background, as-built ground).
  130 of 131 forecourt objects, the two site_built objects, 6 of 8 sport objects and 2 of 3 roads objects are unchanged.
- But a lightmap records the light arriving from the whole scene, and the scene round every unchanged object changed
  (the bowl, the new plaza, apron, layout, landmarks and cars cast and bounce light on them). The look layer also
  changes every material, so the bounce colours and every albedo map change.
- `migrate_stages_v2.py` (the 2026-10-20 reuse path) only matches stage tags, not geometry; it is not used.

So the bake runs from zero.

### Cost estimate (written before the first long run)

From the v1 times per batch (blender/out/web_hero/maps/stages.json of v1, same 4-core CPU class, 128 light samples,
64 AO samples), with AO and albedo only where the export uses them (bake_lightmaps.py `AO_USED`, `ALBEDO_USED`), plus
the new groups from the test bake's fixed cost:

| Stage | v1 groups (s) | new or changed (s) | estimate |
|---|---|---|---|
| albedo (4 samples, all groups) | 1,600 | +800 (site_layout, station, new batch) | 0.7 h |
| AO (64 samples: stadium, roof, suburbs, traffic, landmarks) | 1,550 | +200 | 0.5 h |
| light (128 samples) | 25,030 | +1,900 | 7.5 h |
| total | | | 8.7 h; 10 h with a 15 % margin for the look-layer AO node in every material |

### Parts (each under 4 h; `only=` groups per part, every batch whole inside one part)

| Part | Groups | Estimate |
|---|---|---|
| 1 | stadium_shell, stadium_fins, stadium_ornament, roof, sport, roads, site_built, forecourt | 2.1 h |
| 2 | site_layout, station, layout_pass_i, plaza_south, trace_sw, landmarks, suburbs, traffic | 2.3 h |
| 3 | ground_00 to ground_11 | 2.8 h |
| 4 | ground_12 to ground_23 | 3.0 h |
| final | a run without `only=`: every batch is on disk, so it only writes bake_log.json and the baked blend | 5 min |

After each part the maps and maps/stages.json go to `assets/web_hero_v2_bake` (layout as `assets/web_hero_v1_bake`:
`maps/`, and the baked blend after the final run). A new container restores them first:
`git fetch origin assets/web_hero_v2_bake && git archive FETCH_HEAD maps | tar -x -C blender/out/web_hero/`.

Command for a part (repo root):
```
TALANTA_SITE_BLEND=$PWD/blender/out/frozen_FK.blend blender -b --factory-startup --python-exit-code 1 \
  --python blender/web_hero/bake_lightmaps.py -- only=<groups> 128
```

### Parts run

The tool that runs long commands here stops a command after 2 h, so each part runs as one or two sub-runs of whole
batches (`only=`), each under 2 h; a lost sub-run costs at most its open batch (stages are saved per batch). Times are
wall clock on 4 CPU cores (Cycles uses all four). Branch `assets/web_hero_v2_bake` is pushed after each sub-run.

| Part | Sub-run: groups | Batches (s) | Wall | Result |
|---|---|---|---|---|
| 1 | 1a: stadium_shell, stadium_fins, stadium_ornament, roof | albedo 81 + 53; AO 456 + 397; light 1,822 + 1,418 | 4,304 s | done; light scales 5.17, 3.58, 5.06, 3.63; pushed ce3c942 |
| 1 | 1b: sport, roads (roads_final), site_built, forecourt | albedo 72 + 588; light 849 + 988 | 2,562 s | done; pushed ac10079 |
| 1 | total | | 6,866 s (1.91 h; estimate 2.1 h) | about 20 % slower per batch than v1 (look-layer material wraps), within the margin |
| 2 | 2a: site_layout, station, layout_pass_i, plaza_south, trace_sw, landmarks | albedo 807 + 124; AO 292 (landmarks); light 1,746 + 1,198 | 4,226 s | done; light scales 4.82, 3.90, 2.09, 1.58, 4.32, 5.15; pushed 4f54586 |
| 2 | 2b: suburbs, traffic | albedo 79; AO 913; light 2,624 | 3,684 s | done; pushed 3f37d5b |
| 2 | total | | 7,910 s (2.20 h; estimate 2.3 h) | the new batch (I, J, K, loop) took 1,198 s of light, more than estimated (600 s) |
| 3 | 3a: ground_05, ground_06, ground_09, ground_10 (under the bowl and plazas) | albedo 80; light 2,625 | 2,751 s | done; pushed f4f1619 |
| 3 | 3b: ground_00 to ground_04, ground_07, ground_08, ground_11 | albedo 176; light 5,802 | 6,026 s | done (run detached: one batch near the 2 h tool limit); pushed fda692e |
| 3 | total | | 8,777 s (2.44 h; estimate 2.8 h) | |
| 4 | 4a: ground_12 to ground_15 | albedo 80; light 2,567 | 2,692 s | done; pushed bd1d310 |
| 4 | 4b: ground_16 to ground_23 (outer tiles to +-1,500 m) | albedo 167; light 5,804 | 6,018 s | done (detached); pushed with the final run, 8e3534d |
| 4 | total | | 8,710 s (2.42 h; estimate 3.0 h) | |
| final | no `only=`: all 26 batches on disk, skipped; writes bake_log.json and talanta_web_baked.blend | | 44 s | pushed 8e3534d with the blend (49 MB) and bake_log.json |

Bake total: 32,307 s wall (8.97 h) in four parts of 1.9 to 2.4 h. Stage sums from maps/stages.json: albedo 2,305 s
(0.64 h), AO 2,058 s (0.57 h), light 27,444 s (7.62 h); 8.84 h of baking, the rest is scene load and UV packing per
sub-run (about 45 s each). Estimate was 8.7 h (10 h with margin). `bake_log.json` `bake_seconds` shows 0 because the
final run baked nothing; the per-batch times are in `stages`. 195 MB of maps (54 PNG plus stages.json); the bake
branch holds 91 files, 253 MB, at 8e3534d.

## W3. Panoramas, ground tiles and export

All from `blender/out/frozen_FK.blend` (`TALANTA_SITE_BLEND`), finished state, look layer on (common.py), under the
`blender` binary with `--python-exit-code 1`.

| Step | Command (after `blender -b --factory-startup --python-exit-code 1 --python`) | Wall | Result |
|---|---|---|---|
| panorama 07:30 | `render_panorama.py -- 128 8192 preset=morning_golden near=800 out=blender/out/web_hero/web_hero_v2/env` | 1,131 s | 8192 x 4096 EXR (DWAB) and 2048 HDR; 1,574 objects hidden and 16 cut inside 800 m |
| panorama 17:30 | the same with `preset=evening_golden` | 1,163 s | as above |
| ground tiles | `ground_tiles.py -- blender/out/web_hero/ground_png 16` (run detached) | 5,490 s | 61 tiles (25 at 0.25 m/px within 640 m, 36 at 0.5 m/px to 1,536 m), PNG, about 90 s each, and `tiles.json` |
| export | `export_web.py` | 359 s | 123 hero and 817 site objects staged; LOD0 mesh triangles 0.46M hero, 0.72M site (instances apart) |
| post-process | `node blender/web_hero/node/post_glb.mjs bundle=web_hero_v2` | 2,778 s | 70 files, 164,571,833 bytes (budget 250,000,000): hero GLB 34.2 MB, site GLB 89.2 MB, 61 ground KTX2 8.1 MB, panoramas 32 MB; manifest with sha256 per file |

Fixes found on the way:
- `render_panorama.py` and `ground_tiles.py` read every argument after the program name, so under the `blender`
  binary the `1` of `--python-exit-code 1` became the sample count and `128` the width: the first panorama run took
  13 s and wrote a 128 px image. Both now read only the arguments after `--` (the v1 runs used the bpy module, which
  has no Blender arguments). The two bad panoramas were deleted and rendered again.
- `ground_tiles.py` treated as ground only the v1 list (terrain, pitch, sport, roads and markings, forecourt.py flat
  meshes). The flat meshes of `site_layout_ge`, `finish_plaza`, `layout_pass_i`, `plaza_south_k` and
  `trace_sw_finished` are now ground too (linked copies of flower and shrub prototypes stay shadow-only), and the
  `_final` cut copies match by their base name (`road_markings_final`). 156 ground objects, 5,432 shadow-only. The
  south plaza with its round and axial beds, the lens island and the south-west lawn and loop road are in the tiles.
- The first `post_glb.mjs` run was stopped by the tool's 10 min limit for background commands while it encoded
  the site lightmaps, before it wrote anything; it was run again detached (the 2,778 s above).
- `post_glb.mjs` names the real source scene in the manifest (`bake_log.json` `scene`).

## W4. Bundle, staging and check shots

### Where the files are

| Item | Where |
|---|---|
| Bundle (models/, ground/, env/, manifest.json, README.md) | orphan branch `assets/web_hero_v2` at 3c936e7, 72 files |
| Manifest copy | blender/web_hero/web_hero_v2_manifest.json (sha256 per file) |
| Bake maps, baked blend, bake log | orphan branch `assets/web_hero_v2_bake` at 8e3534d |
| Check shots and sheet | blender/renders/web_hero_v2_check/ (JPG, each under 1 MB) |

No release was made and no pull request was opened; the laptop does both.

### Size against the 250 MB limit

| Part | Bytes |
|---|---|
| models/talanta_hero.glb | 34,215,928 |
| models/talanta_site.glb | 89,237,732 |
| ground/ (61 KTX2 tiles and tiles.json) | 8,282,082 |
| env/ (two 8K EXR, two 2048 HDR, two logs) | 32,836,091 |
| **Bundle total (manifest `total_bytes`)** | **164,571,833 of 250,000,000 (66 %)** |
| What the app downloads in hero mode (two GLBs, the 07:30 2048 HDR, ground tiles) | 136,095,948 (`stage_app_preview.py`) |

web_hero_v1 was 148.95 MB; v2 adds 15.6 MB (the pass I, J and K groups, the landmark towers with AO, and the
parked cars). Hero mode is tier 1 in engineering/scope_decision_2026-10-25.md (loaded after the first view), so the
136 MB does not count against the 30 MB first-view budget, but it is far above what a phone should fetch.

### Load time in software GL

Headless Chromium 1243 (Playwright), ANGLE on SwiftShader, 1920 x 1080, the app served by `npx vite` on the same
machine (no network time). `?hero&mode=full`:

| Shot | Hero mode on (GLBs parsed, panorama loaded) | Ground tiles | Screenshot done |
|---|---|---|---|
| L06 (key 2) | 46 s (42 s in the first run) | 61 of 61 | 256 s in all |
| L07 (key 3) | 38 s (32 s in the first run) | 61 of 61 | 246 s in all |

The app reports 1,580 meshes, 10.43 M triangles (instances included) and 942 LOD groups. A software frame takes tens
of seconds, so these times measure CPU decode and SwiftShader, not a real GPU. They are not a section 8 measurement.

Fixes found on the way:
- `stage_app_preview.py` staged only the GLBs and the HDR, so the app never loaded the ground tiles (it needs
  `ground.index` in the staged manifest). It now copies ground/ to app/public/ground/ and writes `ground.index`;
  app/public/ground/ is in .git/info/exclude.
- `shot_hero.mjs` had a fixed Chromium build path (1194) that this container does not have; it now uses
  Playwright's installed browser (`PW_CHROME` overrides).
- The app now opens on the landing page (stills and claim "Rendered from the twin model"), which covers the scene,
  so the first pair of shots showed the landing still. The shots use `?hero&mode=full`.

### Checks

| Check | Result |
|---|---|
| South plaza shows | pass: L07, the paving with the round bed and the axial beds in front of the south face |
| Lens island shows | not verified: the east island (K3) is in neither L06 nor L07 (hero_artistic_04 README; D03 shows it). The tiles and the site GLB include `plaza_south_k`, but no app shot from the east was taken. (A first reading took a bed in L06 for the island; that was wrong.) |
| Landmark towers show | pass: L07, the tower cluster on the skyline at the right, as in the Cycles still |
| Grass loop shows | pass, weak: L07, the south-west lawn with its loop path shows; at this distance the loop path reads faintly in the ground tiles |
| No west road, railway, station, footbridge or west car park | pass: L07 shows the west lawns empty apart from the training-pitch stand that is also in the Cycles still. The car park in L06 (right of the stadium, by Ngong Road) is the north car park of the site layout, not on the west lawns. |
| People carry "Visualization" | pass: the layer rows "People for scale · Visualization · not a crowd model" and "Match-day crowd · Visualization · phase 1"; the seated crowd shows its own "Visualization" label when it loads |
| Cars carry "Visualization" | **fail on screen**: traffic (app/src/hero/traffic.js) and the baked `layout_cars_visualization` carry the claim only in `userData` and in the GLB node names. No layer row or label shows "Visualization" for cars. Not fixed here (app code, outside this order); lead to decide (scope decision "Labels"). |

### Gaps

1. Car label on screen missing (above).
2. Trees: the tree LOD0 crowns (decimated to 120 triangles, W3) render near black and faceted in the app, and the
   planting reads much thinner than in the Cycles stills (L07 west lawns, L06 foreground). The 70,324-tree canopy is
   also 7.88 M of the 8.89 M site LOD0 triangles. Needs a look at the crown material and normals and at an impostor
   distance before a public build.
3. Not exported: `trace_trees`, `context_l07_visualization` and the people (the Cycles stills show a crowd on the
   plaza; the web build has none outside match day).
4. Far terrain: pink-grey blotches in the ground tiles at the far edge (known from v1).
5. Light: one bake, 07:30 sun. The app's time of day does not change the baked light; L06 shows the morning bake
   under a 07:30 sky, not the approved sunset look. The 17:30 panorama is in the bundle but not used by the app.
6. Framing: the app's L06 and L07 view chips sit lower and wider than the Cycles cameras, so the sheet is a
   like-for-like check of content, not of composition.
7. The facade reads grey-white in the app against the warm sunset still; the shields and the roof ring match.
8. Size for phones: 136 MB in hero mode. A phone version (scope decision, tier 1) needs a smaller site GLB.
