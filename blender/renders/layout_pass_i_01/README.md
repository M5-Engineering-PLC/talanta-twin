# Layout pass I 01: the layout fix after the lead review (finished state)

Work order: engineering/cloud_handoff_2026-10-23.md, Step 1. Rules: engineering/layout_audit_01/LEAD_REVIEW.md, revision 2.
Internal only.

## Why

`research/reference/dusk_aerial_finished_2026-10-17.jpg` is an AI-generated image (Argon), not a photo. Pass F
(`blender/context/layout_final.py`, `blender/renders/layout_final_01/`) took its layout from it, so that layout has no
evidence and is withdrawn. The drone frames and the GE trace stay the layout sources.

## Scene chain

`step_FI` = `step_FE` + `blender/context/layout_pass_i.py` (data: `blender/data/layout_pass_i.json`).
`layout_final.py` is out of the chain. Because pass I starts from step_FE, every object that pass F hid or cut is back
uncut. The asbuilt state does not change: every pass I object is `state_only = "finished"`, and each shared object that
pass I cuts keeps its uncut original for the asbuilt state (`blender/scene_state.py`).

## Change list (finished state)

| Item | Pass F (withdrawn) | Pass I | Evidence |
|---|---|---|---|
| 1. Pass F layout | west road (26 moving cars), railway, station, footbridge, NW car park (318 cars), spine beds, SW lot (207 cars, planted strip), road between the pitches, dark NE track | not built; trees, fence, facade apron, OSM roads and traffic uncut; NE track terracotta | LEAD_REVIEW items 1, 2 |
| 3. South-west | asphalt lot | `sw_lawn` grass inside the loop road; `sw_stand` shown; pitch markings removed in the finished state (`sw_pitch_lines_*` hidden, 130 faces of `training_pitch_lines` cut on this lawn); loop road kept | JWNowpO44rw_000714.767, 000716.317 |
| 4. North-west | asphalt lot | `fc_west_lawn` and the `fc_path_west_*` red paths shown | JWNowpO44rw_000645.000, 000659.633 |
| 5. East approach | 8 m asphalt road | `pi_east_approach`: pale paving (the apron material), 8,765 m²; its west edge follows the outer edge of `ge_apron_ring` (18 points), so it runs into the apron; east corners [283,-37], [298,10]. `pi_east_approach_island`: raised planted island [144,2], [184,-11], [223,-1], [192,13], 960 m², 0.25 m kerb. No lanes, no markings, no cars | JWNowpO44rw_000617.567 (estimate from a camera solve, ±20 m) |
| 6. Junction | — | `ge_road_north_east` stops at the paved edge (12 faces cut in the finished state). Trees within 6 m of the approach removed: 8 roadside eucalyptus, 4 plaza trees, scatter palms, shrubs and trees; also 4 road lamps and 3 plaza lamps inside the paving | JWNowpO44rw_000617.567 |
| 7. Kept from pass F | — | red murram forecourt paths and beds; old OSM footways dropped inside the W1b site (268 road faces, 70 marking faces); car figures for the east hardstanding (226) and Ngong Road traffic (421 cars, 74 matatus and buses). Visualization | JWNowpO44rw_000645.000, 000659.633 |
| 8. North plaza | — | no vehicle route across the plaza or into the bowl | audit fix 9 |

Ledger: 14 correction rows (status "withdrawn 2026-10-23: source is an AI-generated image") for the pass F rows, and
10 new rows (`site.east_approach.*`, `site.south_west.grass`, `site.north_west.lawn`, `site.forecourt_paths.colour`,
`site.osm_footways_inside_w1b`, `site.north_plaza.vehicle_route`, `site.pass_f_layout.finished`).

## Held (no change in pass I)

Track surface (terracotta, footprint at [171,-120]), east hardstanding (GE car park, no new bay rows), Ngong Road
frontage, tree maturity, the third track, Jamhuri sports ground (stays a field, about x 224, z -288).

## Checks

Check renders at 960 x 540, 32 samples, finished state (not committed): D03 shows the broad pale approach with its
centre island and no road through it; D02 shows grass inside the loop road with no cars or markings, the stand and the
loop road. The 1080p renders and the sheets against the drone frames are in Step 3 (`blender/renders/pass_ij_check_01/`).

## Gaps

1. The island is the review's four-corner kite. In D03 the frame's island is a longer, pointed lens; the corners are
   ±20 m camera estimates.
2. The island top uses the murram bed material with planted strips; the frame shows a pale, partly paved island under
   construction. Its finish is unknown (Q4).
3. Short pieces of the training pitch touchlines can remain just outside the `sw_lawn` box, under the loop road edge.
4. The paving lies over the east end of the finish plaza design (`fp_*` beds, shrubs and lamps there are cleared).

## Questions for the lead

None that conflict with LEAD_REVIEW.md.
