# Concept match, pass 2: canopy, suburbs, horizon, forecourt, traffic, surfaces

Plan: engineering/plan_concept_match_2026-10-17.md. Renders are Visualization. Footage decides geometry; concepts 06 and 07 decide look only.

Site build (blender/build_site_detail.py, 18 s): forecourt.py, horizon.py, suburbs.py, traffic.py (Visualization), canopy.py,
the palm_slot_/tree_slot_ instancing step, far_land.py (lead review of pass 1), materials_pbr.apply last, then the Ground109
detail on the open ground. Module reports: blender/data/context_build_report.json.

Lead review items:
1. Haze: aerial haze max 0.55 -> 0.36; fixed haze per band (horizon_band_1..4: 0.12, 0.18, 0.26, 0.36; terrain_horizon layers 0.42, 0.58, 0.70), outer layers in a cooler, bluer haze colour, the warm grade kept off the haze. The bands no longer z-fight with terrain_far (the cause of the pale stripes).
2. Hills: terrain_horizon (build_scene.py, 100 m DEM over 40 km) already holds the Ngong Hills: crest 2,395 m at 17.7 km, bearing 224 deg (153,106 triangles in the hills layer). It is split into three distance layers (to 12.5 km, 12.5 to 20 km, beyond) and hazed per layer, instead of an invented profile. Claim: measured (DEM), smoothed by the 100 m grid.
3. Ground: car-park asphalt -> murram (as built, frame 001246.333); the raw imagery round the site -> grass and murram classes with CC0 Ground109 detail.
4. City: storey window rows and per-building cream and grey tones on the OSM/Overture buildings, suburb walls and the 21 horizon towers.

Rendered scene: 5.53 M triangles including instances (bowl detail 2.16 M, context with 1.50 M canopy 2.00 M, suburbs 0.40 M, forecourt 0.40 M, traffic 0.04 M).
Render: C19 82 s, C20 80 s (960 x 540, 32 samples, lookdev on). Files as in concept_pass_01.
