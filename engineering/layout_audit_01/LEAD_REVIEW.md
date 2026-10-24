# Lead review of layout audit 01

Date: 2026-10-23
Project: Talanta twin (M5)
Reviewed: engineering/layout_audit_01/LAYOUT_AUDIT.md at commit 33ca660 (Sol)
Decision by: Munene, 2026-10-23
Status: released for pass I (revision 2)

This file releases pass I in engineering/cloud_handoff_2026-10-23.md, Step 1. Where this file and LAYOUT_AUDIT.md differ, this file wins.

Revision 2 replaces revision 1 (commit 7a9c341). Revision 1 held the west corridor. Revision 2 removes it, because of the decision below.

## Decision on the dusk image (Q1)

The file research/reference/dusk_aerial_finished_2026-10-17.jpg is not a photo. Munene confirmed on 2026-10-23 that it is an AI-generated image (made with Argon). It is not evidence for geometry, layout, positions or sizes.

Pass F (layout_final_01) took its layout from this image through camera P01. Every pass F feature that has no other source is therefore without evidence. The drone frames and the GE trace stay the sources for the layout.

The image can stay a look reference, at the same level as the landing mockups 06 and 07. Keep camera P01 as a viewpoint only. A P01 render against this image does not prove anything.

## Apply in pass I

All changes apply to the finished state only. The asbuilt state does not change.

1. Remove all pass F layout features from the finished state. These are the features in blender/data/layout_final.json and their objects from blender/context/layout_final.py:
   - `west_road`, with its median, kerbs, markings, lamps and 26 moving cars
   - `railway`
   - `station`
   - `footbridge`
   - `carpark_north_west` and its 318 cars
   - `spine_beds`
   - `carpark_south_west`, its 207 cars and its planted strip
   - `road_between_pitches` (`lf_road_between_pitches`)
   - the `track_ring_ne` recolour to dark asphalt grey
2. Show again all the objects that pass F hid or cut for these features. These include the trees, the boundary fence, the facade apron, the OSM roads and the traffic. Use the uncut originals (the `state_only` copies in blender/scene_state.py). This restores the west forecourt lawn and its paths, `sw_lawn`, `sw_stand` and the terracotta track ring.
3. South-west area (audit fix 1). Make sure that the area inside the loop road is grass, with the ring [-139,122], [-73,135], [-80,233], [-153,228]. Keep the loop road. Do not add pitch markings. Evidence: JWNowpO44rw_000714.767, 000716.317.
4. North-west area (audit fix 2). Make sure that the area at about x -125 to -57, z -238 to -143 shows the `fc_west_lawn` and the `fc_path_west` objects, from `forecourt_layout.json:west_lawn`. Evidence: JWNowpO44rw_000645.000, 000659.633.
5. East approach (audit fix 3). Put a pale paved area with the corners [129,25], [129,-21], [283,-37], [298,10]. Add a raised planted island with the corners [144,2], [184,-11], [223,-1], [192,13]. Blend the west edge into the outer apron. Spread the east end into the peripheral route. The total width is about 40 to 50 m. Show no lane markings and no cars on this area. Evidence: JWNowpO44rw_000617.567 (estimate from a camera solve).
6. Peripheral route junction (audit fix 6). Keep the 9 m route in `site_layout_ge.json:roads[0]`. Join it to the east edge of item 5. Keep trees out of the approach area and out of the junction.
7. Keep these pass F changes, because other sources support them:
   - The red murram forecourt paths and beds. The drone frames show red crossed paths (JWNowpO44rw_000645.000, 000659.633).
   - The removal of the old OSM footways inside the W1b site boundary. The drone frames show the new path network, not the old footways. Change the stated source from the image to these frames.
   - The car figures for the east hardstanding and for the Ngong Road traffic. They are a Visualization upgrade of existing cars, not a layout change.
8. Add no vehicle route across the north plaza or into the bowl (audit fix 9).

## Ledger and records

- gis/parameter_ledger.csv rows 413 to 426 (site.west_road, site.railway, site.station, site.footbridge, site.carpark, site.carpark_north_west, site.road_between_pitches) cite the AI image. Do not delete them. Add a correction row for each one with the status "withdrawn 2026-10-23: source is an AI-generated image".
- Add ledger rows for the items in "Apply in pass I", with the evidence frame and the label that the audit gives.
- Add a note at the top of blender/renders/layout_final_01/README.md: the source image is AI-generated, and the layout in this pass is withdrawn.
- research/reference/README.md is corrected on this branch already.

## Hold: no change in pass I

- Track surface (audit fix 5, Q5). Use the terracotta material from before pass F. Keep the footprint at [171,-120].
- East hardstanding (audit fix 8, Q6). Keep the GE car park. Add no new bay rows.
- Ngong Road frontage (audit fix 9, Q7). Keep the current centrelines, lane count and junctions.
- Tree maturity (Q8) and the third track (Q9). No change.
- Jamhuri sports ground. It stays a field (about x 224, z -288, from Munene's map screenshot).

## Checks after pass I

- Render D01, D02, D03 and P01 at 1080p, as in Step 3 of the handoff.
- Make sheets: D01 against 000645.000, D02 against 000714.767, D03 against 000617.567. Do not make a P01 sheet against the AI image.
- In D02, the south-west area must show grass inside the loop road, with no cars.
- In D01 and P01, the west forecourt must show lawn and red crossed paths, with no cars.
- In D01, D02 and L07, no west dual carriageway, railway, station or footbridge must be visible.
- In D03, the east approach must show a broad pale area with a centre island, not a narrow road.
- Write the gaps in the pass I README. Write any conflict with this file under "Questions for the lead".
