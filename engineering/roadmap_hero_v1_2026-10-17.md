# Roadmap: twin v0.2 to hero v1

Date: 2026-10-17
Source: the GPT-6.1 Sol review of `claude/hopeful-archimedes-lo15is` at 1d82282 and the lead's work order. Packages are in Sol's order: highest visual payoff first. This is a plan only. Build one package at a time, and commit after each package.

## Ground rules for every package

- Follow AGENTS.md. Frames are a look reference only. They are never textures. No gates, exits, camera positions or control rooms.
- Crowd, rain and match views carry a "Visualization" or "Simulation" label on screen.
- Compare each package at the fixed views in `docs/screens/`, using the P0 baseline. Record frame time on the P0 device before and after.
- Never edit `app/src/main.js` or `gis/scripts/export_web.py` in two branches at the same time. These areas are safe to edit in parallel: `bowl.js`, the ground assets, `context.js`, `site.js`, the measurements, and the renderer.
- Commit as Munene. Name branches and commits by package (for example `p2-ground`).

## Packages

| Pkg | Size | Owner | Files | Depends on | Done when |
|---|---|---|---|---|---|
| P0 | S | Munene | docs/screens/ | none | Six fixed views (open, overview, forecourt, fountain day and night, shield, roof) in the default, `?lite`, `?nopost` and forced WebGL2 modes; frame rate, backend line and console errors in a README table |
| P1 | M | Build | bowl.js | P0 | White shell reads white at 500 m by day; membrane and louvres are distinct; shields readable in morning and evening light; ribs vary in depth. Side-by-side with the concept "golden-hour aerial" (look only) |
| P2 | M | Build | export_web.py (ground), new `ground_*.ktx2`/`jpg`, terrain.js | P0 | 1.5 m stylised ground inside the site and 300 m round it: paving, murram, grass edges, crisp road edges, contact shadows. No visible 10 m pixels at the forecourt view |
| P3 | S | Build | context.js | none | Three or more tree species shapes (acacia flat-top, eucalyptus, jacaranda) by NDVI and distance; frame time within 5% of v0.2 |
| P4 | M | Build | site.js | P2 | Forecourt water, steps and ground contact read correctly; figures stand only on walkable surfaces (plaza, forecourt, concourse) and avoid the pool and planters |
| P5 | M | Munene | gis/site_measurements.md | none | Google Earth Pro numbers for the open W1b fields: fountain pool, plaza outline, shield centres, roof inner edge (3 repeats each) |
| P6 | M | Build | export_web.py, gis/site_scale.md | P2, P5 | Derived geometry uses P5 numbers; every feature in the manifest carries a source and a claim level; `gis/site_scale.md` written. Re-run V3 and V4 |
| P7 | L | Build | main.js (renderer), new `quality.js` | P0 | Quality levels (low, medium, high) chosen from the P0 numbers; device test on one phone and one laptop; no frame over 33 ms on medium |
| P8 | M | Build | main.js (lighting), context.js | P7 | Day, dusk and night presets; window lights, street lights and a traffic flow on the main roads at night |
| P9 | L | Build | new `crowd.js` | P7 | Seated crowd from the seat instances, with reactions and phone lights. On-screen label "Visualization" |
| P10 | L | Build | new `weather.js` | P7, P8 | Rain particles, wet materials and puddles from the weather card. On-screen label "Simulation" |
| P11 | L | Build | new `match.js` | P9 | One scripted football sequence that ends in a goal, with the crowd reaction |
| P12 | M | Build | main.js (camera), style.css | P8, P9 | A directed 90-second tour with camera events; touch controls work on a phone; the side panel has a phone replacement (sheet) |
| P13 | M | Munene and lead | docs/release/ | all | Release evidence (V-checks, P0 numbers) and a hero video recorded from the build |

## Order of work

1. P0 first (Munene), because every later package compares against it.
2. P1, P3 and P5 can run in parallel (different files).
3. P2, then P4 and P6 (P2 and P6 both touch `export_web.py`).
4. P7 before any of P8 to P12.
5. P13 last.

## Known gaps carried from the review

- V4 seat count failed: 56,972 against 60,000 (limit 2%). P6 re-runs it after the dimensions and row structure are resolved.
- W3 (COLMAP) has no report yet. W6 uses procedural geometry, not Blender; Munene must approve that change.
- On phones `style.css` hides the side panel, charts and events, and nothing replaces them (P12).
