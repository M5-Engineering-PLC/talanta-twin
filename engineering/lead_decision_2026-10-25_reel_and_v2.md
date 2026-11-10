# Lead decision: landing reel and the web_hero_v2 gaps (2026-10-25)

Date: 2026-10-25
Project: Talanta twin (M5)
From: the local lead session, for Munene and the cloud build chat
Status: decided by the lead. The full reel render needs Munene's approval of the render order (see R3).
Branch: `wo/web-hero-v2`

## State on 2026-10-25

- The cloud finished W0 to W4 of engineering/cloud_web_hero_v2_2026-10-24.md.
- The laptop verified the bundle: 70 files, 164,571,833 bytes, every size and sha256 matches the manifest.
- GitHub prerelease `web_hero_v2` exists (web_hero_v2.tar, its sha256, the manifest).
- app/tools/fetch_assets.mjs now installs web_hero_v2 by default. The fetch and the 38 app tests pass.
- The landing page uses the approved hero_artistic_04 stills, with 9:16 phone crops.

## Part 1: the landing reel

### R1. Decision

Approved as a concept. The landing gets a short Cycles video. The live twin stays the place where the visitor explores.

The landing loads in this sequence:

| Step | What the visitor sees | Budget |
|---|---|---|
| 1 | The poster still (L07) at once | Inside the 30 MB and 5 s first view |
| 2 | The reel. It streams behind the poster and starts muted when it is ready. | 8 to 15 MB at 1080p, a 720p portrait version for phones |
| 3 | The live twin loads in the background while the reel plays (tier 1) | Not in the first-view budget |

Rules:
- One mode only: muted autoplay on all devices. Do not use scroll-to-play. The scroll test (blender/scroll_test/) stays as a test. It does not go into the product.
- Show "Explore in 3D", pause and skip over the reel at all times.
- If the visitor turns on reduced motion, show the poster still and no reel.
- Show the claim on screen for the full reel: people, vehicles and lighting are illustrative.
- Phones get a portrait cut from their own camera moves. Do not crop the wide reel.
- No shot frames an exit, a control room or a camera position at close range (AGENTS.md rule 8).

### R2. Shots

1. The approach from Ngong Road.
2. Round to the south plaza.
3. The bowl from above.
4. The last shot ends exactly on camera L07 (day).

The reel ends on L07 because the live twin is baked with day light. A dusk shot can go in the middle of the reel, but the reel must not end on it. At dusk the live twin does not match the Cycles look yet (gap G5).

### R3. Cost: test first, then a render order for approval

The test frame took about 11 to 12 min at 1080p on the 4-core cloud machine. A 30 s reel at 24 fps is 720 frames, about 140 h. That is too much.

The full reel must cost 30 h of cloud CPU or less, in parts of less than 4 h. Do not start it before Munene approves the render order.

1. Finish the 24-frame test. Record the time for each frame, the file size and any flicker.
2. Then measure each of these, on 3 to 5 frames of the same shot. Record the time and the look for each:
   1. Persistent data (`render.use_persistent_data`): only the camera moves, so the scene does not need a rebuild for each frame.
   2. Volumetric haze off. Use the haze-free view layer and a compositor mist pass instead. The haze is the expensive part.
   3. 32 and 48 adaptive samples with OpenImageDenoise, against 128. Check the flicker over 24 frames.
   4. The portrait phone cut at 720 x 1280.
3. Find out if two or more cloud sessions can render frame ranges at the same time. The frames do not depend on each other.
4. Use 12 fps with interpolation only if the result has no visible artefacts. A shorter reel at 24 fps (20 s) is better than an interpolated one.
5. Write the render order: the shot list, the camera moves, the frame rate, the resolution, the samples, the cost and the file sizes. Put it in blender/landing_reel/RENDER_ORDER.md, then stop.
6. After each part of the full render, push the frames to an orphan branch `assets/landing_reel_frames`. Do not put frames on `wo/web-hero-v2`.

## Part 2: the web_hero_v2 gaps

The gaps are from blender/web_hero/WEB_HERO_V2.md, section W4 "Gaps".

| Gap | Fix | Who |
|---|---|---|
| G1 Car label on screen missing | Add a layer row and an on-screen label "Vehicles · Visualization" for traffic and the baked parked cars | Laptop (app) |
| G2 Trees near black and faceted, planting thin | Find the cause in the export: crown normals, the material, or the 120-triangle decimation. Fix the export. Then set the impostor distance in the app. | Cloud finds the cause and fixes the export. Laptop does the app part. |
| G3 No people outside match day | Later: the crowd modules (scope decision, phase C) | Not now |
| G4 Pink-grey blotches in the far ground tiles | Later. Known from v1. | Not now |
| G5 One bake (07:30); dusk does not change the baked light | Do not make a second bake now (about 9 h). At dusk, the app uses the 17:30 panorama, lowers and warms the lightmap intensity, and turns on the lamps. | Laptop (app) |
| G6 The app's L06 and L07 view chips do not match the Cycles cameras | Set the app's L06 and L07 views to the Cycles camera positions, targets and field of view. The reel (R2) and the stills need this match. | Laptop (app) |
| G7 Facade grey-white in the app against the warm still | Correct it in the app grade together with G5 | Laptop (app) |
| G9 The default page shows the old procedural model. The baked scene loads only with `?hero`. Munene saw this on 2026-10-25. | Make the baked scene the default live twin. It loads in tier 1, behind the landing still or the reel. Keep the procedural model only as a fallback when a device cannot load the bake. This is the first laptop fix. | Laptop (app) |
| G8 136 MB in hero mode, too much for phones | Export a phone variant of the site GLB: trees as impostors, no far LOD. Target 40 MB or less for the phone tier 1. | Cloud (export) |

## Order

1. Cloud: R3 steps 1 to 5 (the test and the render order), then G2 (cause and export fix), then G8 (phone variant). Stop for the render order approval.
2. Laptop: G9 first, then G1, G5, G6 and G7 in the app, with a Sol review.
3. At the end of phase A, the lead opens one pull request from `wo/web-hero-v2` into `main`.
