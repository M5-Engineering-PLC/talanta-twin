# Lead decision: bring the live twin close to the Cycles look (2026-10-25)

Date: 2026-10-25
Project: Talanta twin (M5)
From: the local lead session, for Munene, Sol and the cloud build chat
Status: approved by Munene on 2026-10-25 ("send out all four steps"). The Gaussian splat stays a later test.
Branch: `wo/web-hero-v2`
Related: engineering/lead_decision_2026-10-25_reel_and_v2.md (R1 to R3, gaps G1 to G9), engineering/scope_decision_2026-10-25.md (loading tiers).

## Why the live twin is not the Cycles image

- Cycles traces about 128 samples for each pixel. One 1080p frame takes about 11 min on the 4-core cloud machine. The browser has about 16 ms for each frame.
- The live twin uses a bake. The bake stores Cycles light in lightmaps at one time, 07:30. The app cannot change the baked light. It can only tint and dim it.
- The browser does not render the volumetric haze, the soft sun shadows, the glare and the compositor grade. It uses cheaper effects.
- Some differences are pipeline faults, not physics:
  - Trees are decimated to 120 triangles and render near black (G2).
  - The facade reads grey (G7).
  - The Cycles stills use AgX with the look "AgX - High Contrast" or "AgX - Medium High Contrast" (blender/lookdev.py) and a compositor grade. three.js AgXToneMapping has no looks. The app grade (app/src/hero/grade.js) is a separate estimate.
  - The L07 still is at 10:30 and the L06 still is at 18:05. The only bake is at 07:30. So no app view can match a still in light.

## Decision: four steps

| Step | Outcome | Who |
|---|---|---|
| P1 Pipeline fixes | The app colour pipeline copies the Cycles look. Trees and the facade are correct. | Cloud (export data, trees). Laptop (app grade). |
| P2 Time-of-day bakes | Lightmap sets at the still times and at night. The app blends between them as the time changes. | Cloud (bakes). Laptop (blend). |
| P3 Photo mode | On a desktop, when the visitor stops the camera, a browser path tracer refines the frame. | Laptop (app). |
| P4 Crossfade at the views | At L06 and L07, the live frame fades into the Cycles still. | Laptop (app). |

Later test, not now: a Gaussian splat trained from Cycles views. It needs a GPU machine, and we do not have one. It is 100 to 500 MB and has one lighting state. Do not start it.

## P1. Pipeline fixes

### P1 cloud

1. Write the full look into the export manifest, in a new `look` block:
   - the view transform, the look name and the exposure for each still (L06, L07);
   - every compositor node value that changes colour (from blender/lookdev.py `STRENGTHS`: contrast, saturation, warmth, grain, glare, vignette);
   - a curve of 33 samples that gives the effect of the AgX look on a grey ramp from -10 EV to +6.5 EV. Measure it in Blender. The app copies this curve.
2. Render two reference images for each of L06 and L07 at 1920 x 1080:
   - `ref_bake_<view>.png`: the web export state (the 07:30 bake, no haze, no people, no event lights), with the full look;
   - `ref_still_<view>.png`: the same camera with the hero_artistic_04 settings at the still time, but no haze.
   Push them to the orphan branch `assets/web_hero_v2_bake` under `parity/`. They are internal reference only.
3. G2 trees, as ordered before: find the cause (crown normals, the material, or the 120-triangle decimation) and fix the export.

### P1 laptop

1. Apply the manifest `look` block in the app grade instead of the estimated values in grade.js. Keep grade.js as the fallback when the block is missing.
2. Write a tool that captures the app canvas at L06 and L07 and gives the mean colour difference (CIEDE2000) against `ref_bake_<view>.png`, for the full frame and for the facade, the pitch and the sky. The lead runs it in Chromium.
3. Target: mean CIEDE2000 of 3 or less for the full frame against `ref_bake_<view>.png`. Report the value before and after.

## P2. Time-of-day bakes

Bake these lightmap sets on the same geometry and UVs as web_hero_v2. Bake each one in parts of less than 4 h.

| Priority | Time | Why |
|---|---|---|
| 1 | 10:30 | Matches the L07 still and the end of the reel |
| 2 | 18:05 | Matches the L06 still (golden hour, sun near the Ngong Hills) |
| 3 | 20:00 | Night: floodlights, facade lights, lamps and city light |
| existing | 07:30 | Morning |

Rules:
- Each set is about 9 h of cloud CPU. The three new sets total about 27 h.
- Each set has the same file names and layout as the 07:30 set, under `lightmaps/<HHMM>/`. Push the maps to an orphan branch `assets/web_hero_v2_bake_<HHMM>`. The laptop makes the release.
- Also render a panorama for each time, as for the 17:30 panorama.
- The night bake needs the event and street lights as real Cycles lights. If they do not exist as lights in the scene, stop and report. Do not invent fixture positions near exits or control rooms (AGENTS.md rule 8).

App rules (laptop, after the 10:30 set arrives):
- Tier 1 loads only the set nearest to the current time. Other sets load in tier 2, when the visitor moves the time slider.
- Between two sets, blend the lightmaps in the shader. The sun direction, the shadows and the sky change with the time as they do now.
- Phones load one set only, until the phone variant (G8) is measured.

## P3. Photo mode

Paused on 2026-10-25 by engineering/lead_decision_2026-10-25_walkthrough.md. The walkthrough film does this job now. Do not start P3.

- Use three-gpu-pathtracer (npm). It runs on WebGL2, so photo mode uses its own WebGLRenderer and canvas over the WebGPU canvas. It is a tier 2 module (dynamic import). It downloads only when the visitor opens photo mode.
- Desktop only. It is off on phones and on devices without WebGL2 or with less than 4 GB of device memory (`navigator.deviceMemory` when it is available).
- It starts when the camera has been still for 1 s. It stops at the first input. It shows a sample count and a "Photo mode, path traced in your browser" note.
- It uses the base colour and material textures, not the lightmaps, and the panorama for the current time as the sky light.
- Escalate if the GLB has the light baked into the base colour, or if the 7.88 M-triangle scene does not fit in GPU memory on the lead laptop. A lower LOD for photo mode is an acceptable fix.

## P4. Crossfade at the views

- When the visitor selects view L06 or L07 and the camera arrives, set the app time to the still time (18:05 or 10:30). Then fade in the Cycles still over 0.6 s.
- Fade the still out at the first input (drag, wheel, touch, key) over 0.3 s.
- The still must line up with the live frame. The app camera uses the Cycles vertical FOV. When the viewport is not 16:9, fit the still by cover and change the app FOV so that the two frames line up. On phones, use the 9:16 crops.
- Show the claim from the landing page over the still: the people, vehicles and lighting are illustrative.
- If reduced motion is on, show the still without the fade.

## Order

1. Cloud: R3 steps 1 to 5 (the reel test and the render order), then G2, then P1 cloud items 1 and 2, then G8, then the P2 bakes in priority order. Stop after each bake set and report the time used.
2. Laptop, Sol run 1: P1 laptop and P4.
3. Laptop, Sol run 2: P3 photo mode. Paused (see P3).
4. Laptop, Sol run 3: the P2 blend, after the 10:30 set arrives.
5. Each Sol change gets a lead review of the diff and a visual check in Chromium.

## Cloud budget

| Item | Estimate |
|---|---|
| P1 references (4 Cycles frames at 1080p, no haze) | under 1 h |
| P2 bakes 10:30, 18:05, 20:00 | about 27 h |
| Panoramas for the new times | under 2 h |

The full reel render (R3) needs a separate approval by Munene.
