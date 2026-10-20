# Work order: Sol review fixes, quick wins, roadmap

Date: 2026-10-17
Status: done in commits 565e38b to 7be3c7e. Kept for the record.
Branch: claude/hopeful-archimedes-lo15is, reviewed at 1d82282
From: the local lead session, for the cloud Talanta build chat

## Context

GPT-6.1 Sol ran a read-only review of this branch and a progress evaluation. The verdict is: merge after the listed fixes. `node --check` passed on all 12 JavaScript files. Nothing was tested in a browser or on a GPU.

Do the steps in the order below. Commit after each step.

## Step 1: P1 and P2 fixes

- P1 `app/src/main.js:586`. `pipeline.render()` runs outside the guard at line 546. A shader or render-target failure during render throws and does not fall back to a plain render. This contradicts handoff line 26. Catch the failure, switch to the plain renderer once, and log a warning.
- P2 `gis/scripts/export_web.py:193`. The export keeps exterior rings and drops polygon holes. The track exterior is 13,657.72 m2, but its recorded area is 3,638 m2. `pitch.js:78` fills it at grass height, so it covers the training pitch. Keep the holes. Acceptance: the mesh area matches the source polygon, and the enclosed pitch is visible.
- P2 `main.js:303`. The bowl toggle leaves the plinth, concourse and luminous rings visible. Include them in the toggle.
- P2 `site.js:45-47`. The fountain water is at `pad - 0.2`, under the solid step boxes and the terrain. Make the pool visible: cut the opening or raise the water.
- P2 Seat count. 56,972 is 5.05% short of 60,000. The handoff says "within 5%", and `gis/validation_plan.md:14` sets a 2% limit. Do not change the seat spacing to force a match. Correct the claim in the handoff, and mark the capacity gate as failed until the dimensions and row structure are resolved.
- P2 `main.js:308`. The building layer says "Open Buildings 2023", but 6,687 heights are area defaults and 7 come from floor counts. Keep the height source for each building, and label estimated heights as estimated.
- P2 `site.js:5` cites JWNowpO44rw 07:14. `gis/heldout_frames.csv:4` reserves that frame for validation. Replace the validation frame with an unused one, or record that it was used.
- P2 `fetch_open_buildings_temporal.py:52` prints "no tiles" and returns success. `derive_near_ring.py:35` then uses defaults. Exit with a nonzero code when no tiles are found.
- P2 `main.js:207`. The tour highlight clears its group without disposing the geometries. Dispose them.

## Step 2: Five quick wins

Each quick win takes less than one hour. Compare each one at fixed views.

1. `main.js`: make a fixed golden-hour opening shot with fewer focus chips. The stadium must fill the first frame, and the controls must not cover the roof.
2. `bowl.js`: tune the shield brightness, and put the spears behind the shields. Red, black and white must stay distinct without strong emissive glow.
3. `bowl.js`: compare an opaque membrane with the current transparent roof. Keep the opaque membrane if it has no sorting artifacts and gives better shading.
4. `site.js`: make the fountain water easy to see by day and by night. This links to the P2 fountain fix.
5. `context.js`: give a capped sample of trees a trunk and a second, smaller crown. The silhouettes must improve with no significant increase in frame time.

## Step 3: Roadmap to a hero v1

This is Sol's order, with the highest visual payoff first. Plan these packages. Do not build them all now.

| Package | Size | Owner | Outcome |
|---|---|---|---|
| P0 | S | Munene | Real-device baseline: six fixed views; frame rates, backend and console errors in the default, ?lite and ?nopost modes; and forced WebGL2. Save the results in docs/screens/ |
| P1 | M | Build | Bowl silhouette and materials in bowl.js: white shell, membrane, louvres, readable shields, varied ribs |
| P2 | M | Build | Crisp stylised ground near the stadium, in place of the blurry 10 m Sentinel-2 texture: paving, murram, grass edges |
| P3 | S | Build | Tree variety in context.js |
| P4 | M | Build | Forecourt in site.js: water, steps, ground contact, figures that stay on surfaces they could stand on |
| P5 | M | Munene | Google Earth Pro measurements for the open W1b fields. Google Earth Pro is now installed on his PC |
| P6 | M | Build | Derived geometry and provenance fixes, and write gis/site_scale.md. Do this after P2, because both touch export_web.py |
| P7 | L | Build | Renderer stability and device quality levels |
| P8 | M | Build | Daylight, dusk and night lighting, with city lights at night |
| P9 | L | Build | Seated crowd with reactions and phone lights, labelled Visualization |
| P10 | L | Build | Rain and wet materials, labelled Simulation |
| P11 | L | Build | One scripted football sequence that ends in a goal |
| P12 | M | Build | A directed 90-second tour, camera events, and touch controls that work on a phone |
| P13 | M | Munene and lead | Release evidence and a hero video |

These file areas are safe to edit in parallel: bowl.js, the ground assets, context.js, site.js, the measurements, and the renderer. Never edit main.js or export_web.py in two places at the same time.

## Scorecard

- Modules: 55 in total. 10 are partial, 6 are stubs, and 39 are not started.
- W1: not verified, because gis/raw is not present.
- W1b: partial.
- W2: done, but the footprints are in GeoPackage format, not GeoJSON.
- W3: no evidence. There is no COLMAP report.
- W4: partial. gis/site_scale.md does not exist.
- W5: partial. There is no performance overlay and no build evidence.
- W6: uses procedural geometry instead of Blender. Munene must approve this change.

The weakest areas are close-range visual quality, the missing event story (crowd, rain, match), and performance that has not been measured on a real device. On phones, `style.css:166` hides the side panel, charts and events, and nothing replaces them.

## Concept renders

Sol made four concept renders: a golden-hour aerial, a Mashujaa night with a drone shield, the matchday bowl, and the forecourt at dusk. They exist only on Munene's PC. They are concept images, not product assets. Use them as a look target only. Do not use them as textures.

## Rules

- Follow AGENTS.md.
- Do not use frames as textures.
- Do not put gates, exits or security detail in the public build.
- Label crowd views "Visualization".
- Commit as Munene, with no Claude attribution.

## Report back

When steps 1 and 2 are done, reply with the list of commits and before-and-after notes for each fixed view.
