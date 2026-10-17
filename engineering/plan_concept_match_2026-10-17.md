# Plan: match the concept renders (06, 07, 05)

Date: 2026-10-17
Owner: Munene. Lead: the local session. Second opinion: GPT-6.1 Sol (read-only, concept-plan run).
Goal: Cycles stills of the Blender model that look as close as possible to lead renders 06 and 07 (research/concepts/2026-10-17/). Then the same look in the three.js twin through the baked export.

## Where we are

Concept 06 above our C06, side by side: our render is close-up, flat grey light, cone-shaped trees, no real sky, and the landscape is out of frame. The concepts carry most of their realism in four things: far and high framing, golden light with a real sky and haze, dense broadleaf canopy and suburbs, and a designed forecourt.

## Gaps, ranked (lead study, corrected by Sol)

1. Camera framing. The stadium must fill about 36 to 38% of the frame width, near the vertical centre, with a 14 to 18% sky band.
2. Light: golden hour, a real sky, depth haze and long shadows.
3. Tree canopy: irregular broadleaf crowns. The current crowns are smooth procedural shapes.
4. Suburbs and horizon: integrate blender/context/suburbs.py; layered hills with haze; the racecourse visible.
5. Forecourt composition: the paths, palms, masts, beds and track exist in build_scene.py and build_site_detail.py. Their layout and look need refining against the design model frames and 06.
6. Surfaces: real paving, asphalt, earth, grass and roof tile textures. Louvres stay as geometry.
7. Traffic on Ngong Road in the Blender scene.
8. The lit inner bowl visible through the roof opening.

## Decisions for Munene

| Decision | Options | Lead recommendation |
|---|---|---|
| Shield size | Concept (about 70 to 80% of wall height by Sol's estimate) or historian frames (85 to 90%) | Frames. The concept is an AI image; the frames are the real building |
| Light | One morning bake (07:35, matches 06) or two (morning for 06, evening for 07) | One morning bake for the web. Render the 07 still with its own evening sun in Cycles |
| Film | A short film now, or stills first | Stills first. 90 s of film at check resolution is about 60 hours of CPU |

## Who does what

- Local (light work only): download CC0 assets and commit them with their licence records. The cloud network blocks downloads. Write code where it is local-owned (app/).
- Cloud: every Blender change, render, bake and export.
- Sol: a read-only review at the end of each pass, only if the Codex budget allows (weekly limit resets on 22 Oct).

## Local step 0: CC0 assets (before pass 2)

Download and commit to blender/assets/ with a CREDITS.md and one licence line per asset:
- 2 golden-hour HDRI skies (Poly Haven, CC0), 4K, with one morning and one evening sun.
- PBR texture sets at 2K (ambientCG or Poly Haven, CC0): paving stones, concrete, asphalt, red earth (murram), grass, clay roof tiles, corrugated iron sheet, painted metal.
- Broadleaf tree and palm models if a CC0 source exists. If none, the cloud builds irregular crowns in geometry nodes.
Keep the total under about 120 MB. Never derive a texture from a reference frame or a concept image.

## Passes (each pass gives a visible jump)

| Pass | Work | Size | Forecast score |
|---|---|---|---|
| 1 | Framing and light: C19 and C20 poses from Sol (C19 position [485, 165, -445], target [10, 30, 11], 35 mm; C20 position [-180, 165, 650], target [20, 30, 5], 38 mm), refined to the bounding boxes and sky band. HDRI sky, golden sun, depth haze in lookdev.py | S | 72 to 76 |
| 2 | Canopy, suburbs, horizon: irregular broadleaf crowns, CC0 palms, suburbs.py integrated after the site build, roof variety and apartment windows, layered hills and the racecourse | L | 78 to 82 |
| 3 | Forecourt, surfaces, traffic: the forecourt layout against the design model frames and 06, CC0 textures in build_scene.py, instanced vehicles on the Ngong Road splines | M | 82 to 85 |
| 4 | Roof and bowl: softer seam contrast, roof sheen, daylight bounce into the bowl, the lit tiers visible through the opening | M | 85 to 88 |

Forecasts are planning targets, not measured results.

## How closeness is measured (every pass)

- Fixed 960x540, fixed seed, exposure and camera.
- Frozen crops: roof, facade, bowl, forecourt, road, canopy, suburbs, horizon.
- Numbers per pass: stadium bounding-box error against the concept, horizon height, road angle, mean and spread of LAB colour per crop, edge density per crop, shadow direction, highlight clipping.
- The eight-category score (engineering/review_astra_hyperreal_2026-10-17.md). Mark "people" as not observed.
- Stop when two passes in a row reach 85/100 with every scored category at 4/5 or more. Escalate after three passes that gain less than 2 points, or after 8 passes.
- Commit each pass with blender/renders/concept_pass_NN/: the C19 and C20 renders, the side by side with 06 and 07, and metrics.csv.

## Web parity (after pass 2)

- blender/web_hero/common.py must use the same light and lookdev settings as the stills.
- Add the suburb collections to export_web.py; replace the 8-triangle tree fallback where it is visible.
- Test lightmap_uv.py, then re-bake with bake_lightmaps.py.
- render_panorama.py: separate near and far scenery, so close objects are not duplicated in the panorama.

## Honesty rules

- Measured geometry and the frames outrank the concepts. Shield size, the bowl and the roof stay as the ledger says.
- Label finished planting and the forecourt "estimated, design intent". Label artistic light and grade "Visualization".
- The concept images and frames are internal reference only. Never use them as textures.
