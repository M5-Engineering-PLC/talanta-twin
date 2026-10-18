# Forecourt layout

Date: 2026-10-18. Project: Talanta twin, separate venture track pending the owner decision.
Status: software geometry and internal Visualization. Source files remain intact.
Source paths: `blender/data/forecourt_layout.json`, the keep CSV, W1b normalized measurements, and `blender/data/site_plan.json`.
Handoff: the cloud owner calls `build(scene, root)` before saving the site scene and before the canopy module consumes palm slots.

## Authority and coordinates

The Kenyan Historian frames decide layout. Concept 06 sets light, color, and composition only.
The build shows the finished design intent. Per-element properties distinguish observed forms from future planting and estimated furniture.
An `as_built` state means that a form appears in drone footage. It does not mean that its coordinates or finish were surveyed.

Coordinates use meters: Blender X east, Y north, Z up, with the W1b pitch center as origin.
The existing site JSON uses X east and Z south. This layout negates its second coordinate exactly once.
The module samples terrain height from `terrain_site`, then `terrain_far`. Without either terrain object, it uses Z = 0 for the smoke test.

The environment notes use seconds as frame IDs. Actual filenames use HHMMSS.mmm, as listed in the keep CSV.
For example, 419.633 seconds identifies `JWNowpO44rw_000659.633.jpg`, and 281.933 seconds identifies `JWNowpO44rw_000441.933.jpg`.
The frame files exist. The report uses actual filenames below.

## Measured constraints

The plaza polygon copies all 176 normalized W1b vertices without a fit or rescale.
Its computed area is 8219.33 m2, against the ledger value of 8219 m2.
Its east-west extent is 102.956 m, and its north-south extent is 92.928 m.
These extents differ from the ledger minimum-area rectangle, which measures 102.5 × 92.9 m and has uncertainty +/-2 m.

The measured plinth reaches Y = 128.621 m. The replacement domain begins at Y = 134 m, outside that footprint.
The north edge follows interpolated Ngong Road centerline coordinates with a 25 m southward offset.
The existing road half-width is 22.4 m, including its verge. Road position is OSM-derived, and its width is estimated.
The 25 m offset is along north-south coordinates, not perpendicular to the road.
A 101-point software sample gives minimum clearance of 22.452 m, against the existing 22.4 m half-width.
The small margin requires assembled-scene review because road widths and positions retain their stated uncertainty.
The domain limits are estimates, not measured boundaries. The original warm-up and training tracks remain unchanged.

No camera solution or independent metric frame scale exists for these oblique views.
No new greater-than-5 m contradiction was established. The footage cannot prove that every estimated position is within 5 m.
The build keeps the measured footprint and plaza outline instead of moving them to match an image.

## Elements and claims

Every JSON element has an ID, source, claim, state, and explicit geometry.
Path polylines include width. Mast clusters list every position. Palm slots list every position separately.
The source column uses paths relative to the repository. Frame paths are internal references only.

| Element | Type / state | Source | Claim |
|---|---|---|---|
| `forecourt_extent` | extent / as_built | `JWNowpO44rw_000659.633.jpg` | derived: bounded north of W1b plinth and 25 m south of OSM Ngong centreline; lateral limits estimated |
| `plaza_edge` | plaza / as_built | `gis/measurements/normalized/north_plaza_w1b_2026-10-17.csv` | measured from W1b: normalized ground outline, image 2025-12-26 Airbus, uncertainty +/-2 m; paving finish estimated from model frame |
| `facade_apron` | surface / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `west_lawn` | lawn / as_built | `JWNowpO44rw_000714.767.jpg` | estimated from frame JWNowpO44rw_000714.767.jpg: position, dimensions and count by eye; not a camera solve |
| `east_lawn` | lawn / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `roadside_lawn` | lawn / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_west_diagonal` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_west_cross` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_west_connector` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_east_diagonal` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_east_cross` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_east_outer` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_road_approach` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_plaza_west_axis` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `path_plaza_east_axis` | path / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: position, dimensions and count by eye; not a camera solve |
| `plaza_ring_walk` | path / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated from frame JWNowpO44rw_000441.933.jpg: position, dimensions and count by eye; not a camera solve |
| `central_round_bed` | roundabout / as_built | `JWNowpO44rw_000714.767.jpg` | estimated from frame JWNowpO44rw_000714.767.jpg: position, dimensions and count by eye; not a camera solve |
| `axial_bed_south` | bed / as_built | `JWNowpO44rw_000714.767.jpg` | estimated from frame JWNowpO44rw_000714.767.jpg: position, dimensions and count by eye; not a camera solve |
| `axial_bed_north` | bed / as_built | `JWNowpO44rw_000714.767.jpg` | estimated from frame JWNowpO44rw_000714.767.jpg: position, dimensions and count by eye; not a camera solve |
| `edge_bed_west` | bed / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated from frame JWNowpO44rw_000441.933.jpg: position, dimensions and count by eye; not a camera solve |
| `edge_bed_east` | bed / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated from frame JWNowpO44rw_000441.933.jpg: position, dimensions and count by eye; not a camera solve |
| `mast_cluster_west` | mast_cluster / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; cluster visible also in JWNowpO44rw_000714.767.jpg; exact six-mast count and 17 m height unmeasured |
| `mast_cluster_east` | mast_cluster / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; cluster visible also in JWNowpO44rw_000714.767.jpg; exact six-mast count and 17 m height unmeasured |
| `palm_slot_west_00` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_01` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_02` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_03` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_04` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_05` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_06` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_west_07` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_00` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_01` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_02` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_03` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_04` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_05` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_06` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_07` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_08` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_east_09` | palm / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_00` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_01` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_02` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_03` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_04` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_05` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_06` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_07` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_08` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_09` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_10` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_11` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_12` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_13` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_14` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_15` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_16` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `palm_slot_verge_17` | palm / design_intent | `JWNowpO44rw_000606.233.jpg` | estimated: design intent from model frame JWNowpO44rw_000606.233.jpg; avenue placement inferred, exact count, species and mature height unresolved |
| `street_light_west_00` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_west_01` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_west_02` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_west_03` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_east_00` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_east_01` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_east_02` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_east_03` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_east_04` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_plaza_00` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_plaza_01` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `street_light_plaza_02` | street_light / as_built | `JWNowpO44rw_000659.633.jpg` | estimated from frame JWNowpO44rw_000659.633.jpg: white path fixtures; 5 m height and spacing provisional; no photometric claim |
| `bench_line_west` | bench_line / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; small white furniture forms unresolved; bench function and count are visualization assumptions |
| `bench_line_east` | bench_line / design_intent | `JWNowpO44rw_000441.933.jpg` | estimated: design intent from model frame JWNowpO44rw_000441.933.jpg; small white furniture forms unresolved; bench function and count are visualization assumptions |

## Differences from concept 06

The W1b outline fixes the plaza size. The model does not expand it into the broad fan shown in concept 06.
The central circle is a pedestrian planter island, not evidence of a vehicle roundabout.
Two narrow axial beds follow the as-built aerial. Generic evenly spaced circular planters no longer define this forecourt.
Red paths divide lawn wedges beside the pale plaza. Concept 06 does not establish extra paths or a fully paved frontage.
The diagonal paths follow the visible pattern, but their coordinates remain estimates without a solved camera.

Masts form two clusters near the facade, rather than eight isolated poles spaced along the plaza sides.
Six poles per cluster and 17 m height remain estimates. White poles carry no flags, text, or symbols.
Palms represent future planting from the physical model. The as-built frame does not establish mature palm avenues.
The module creates plain empties named `palm_slot_*`. It leaves palm geometry to the canopy owner.
Benches represent unresolved white furniture forms in the model. Their function, count, and positions remain explicit Visualization assumptions.

The existing warm-up track retains its W1b outline and existing finished-state detail.
Concept 06 does not move, enlarge, or duplicate that track.
No reference image becomes a texture. This module uses plain materials and its own geometry.

## Replacement and integration

The module hides these original objects with both `hide_render` and `hide_viewport`:
`north_plaza`, `palms`, `site_trees`, `shrubs`, `planters`, `flag_masts`, `path_lights`, `light_masts`, and `bollards`.
Missing originals are allowed in an empty scene. The module never deletes an original object.
For each visible batched mesh, a retained copy preserves vertices outside the forecourt domain and keeps its modifiers.
Original mesh data remains intact. The copied point attributes support the existing scatter modifiers.
The existing terrain stays intact beneath new ground surfaces. A lawn overlay covers the old ground mask inside this domain.
Roads, tracks, buildings, and their original geometry remain outside the replacement list.

The public function is `build(scene, root)`. It returns software counts and the hidden and retained object names.
The module rejects a second call when `forecourt_context` exists. Call it once per loaded scene.
Add these exact lines at the end of `blender/build_site_detail.py`, before its save:

```python
import importlib.util
_fc_spec = importlib.util.spec_from_file_location("talanta_forecourt", ROOT / "blender/context/forecourt.py")
_fc_module = importlib.util.module_from_spec(_fc_spec)
_fc_spec.loader.exec_module(_fc_module)
_fc_module.build(scene, ROOT)
```

Call the canopy module after these lines so that it can consume the 36 palm slots.
No owned source contains gates, turnstiles, access-control barriers, security cameras, or control rooms.
The facade frontage consists of paving only. No people or traffic are added.

## Software evidence and limits

JSON provenance result: `JSON provenance: 73/73 elements have claim and source`.
`python3 -m py_compile blender/context/forecourt.py` completed without output.
The module enforces a 70000-triangle limit for added forecourt meshes. Retained existing context is reported separately from new geometry.
No render, heavy scene load, physical measurement, material export, or cloud integration was performed.
Terrain sampling, final appearance, copied scatter modifiers, and canopy consumption require cloud review in the assembled scene.
The empty-scene test covers geometry creation, provenance, palm slots, hiding, and preservation of an outside point with a vector attribute.

Data audit result: `DATA PASS: 73 unique IDs; all frame sources exist; path widths positive; 176 W1b plaza vertices unchanged; domain outside measured plinth`.
Road audit result: `ROAD PASS: minimum sampled forecourt edge clearance 22.452 m > existing road half-width 22.4 m`.
