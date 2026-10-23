# Lead review of layout audit 01

Date: 2026-10-23
Project: Talanta twin (M5)
Reviewed: engineering/layout_audit_01/LAYOUT_AUDIT.md at commit 33ca660 (Sol)
Decision by: Munene, 2026-10-23
Status: released for pass I

This file releases pass I in engineering/cloud_handoff_2026-10-23.md, Step 1. Where this file and LAYOUT_AUDIT.md differ, this file wins.

## Decision on the dusk photo (Q1)

The dusk photo research/reference/dusk_aerial_finished_2026-10-17.jpg came from WhatsApp. The photographer and the capture date are not known. Pass F found that its skyline does not fit the camera, so the photo is probably edited.

For this reason, the drone frames win where they disagree with the photo. The photo stays a look reference only.

## Apply in pass I

All changes apply to the finished state only. The asbuilt state does not change. Add a ledger row for each change, with the evidence frame and the label "estimate from a camera solve" where the audit gives that label.

1. South-west lot (audit fix 1). Remove `layout_final.json:carpark_south_west`, its 207 cars and its planted strip. Show `sw_lawn` and `sw_stand` again. Use the grass ring [-139,122], [-73,135], [-80,233], [-153,228]. Keep the loop road around it. Do not add pitch markings. Evidence: JWNowpO44rw_000714.767, 000716.317.

2. North-west car park (audit fix 2). Remove `layout_final.json:carpark_north_west` and its 318 cars. Show the `fc_west_lawn` and `fc_path_west` objects again, from `forecourt_layout.json:west_lawn`. Remove `spine_beds` from the finished state, and show the lawn edge as it was before pass F. The area is about x -125 to -57, z -238 to -143. Evidence: JWNowpO44rw_000645.000, 000659.633.

3. East approach (audit fix 3). Remove the 8 m ribbon `lf_road_between_pitches`. Put a pale paved area in its place, with the corners [129,25], [129,-21], [283,-37], [298,10]. Add a raised planted island with the corners [144,2], [184,-11], [223,-1], [192,13]. Blend the west edge into the outer apron. Spread the east end into the peripheral route. The total width is about 40 to 50 m. Show no lane markings and no cars on this area. Evidence: JWNowpO44rw_000617.567.

4. Peripheral route junction (audit fix 6). Keep the 9 m route in `site_layout_ge.json:roads[0]`. Join it to the east edge of item 3. Keep trees out of the approach area and out of the junction.

5. Forecourt paths (audit fix 7). Keep both pale plazas, the round beds, the axial beds and the red crossed paths. After item 2, show the west paths again with the widths that they had before pass F (3 to 5 m).

6. Vehicle access (audit fix 9). Add no vehicle route across the north plaza or into the bowl.

## Hold: no change in pass I

- West corridor (audit fix 4, Q2). Keep the west dual carriageway, the railway, the station and the footbridge exactly as they are now. Do not extend, move or remove them. Only the drone frames and the photo were examined, and no drone frame shows them. They stay until a second source settles them.
- Track surface (audit fix 5, Q5). Keep the current material and the footprint at [171,-120].
- East hardstanding (audit fix 8, Q6). Keep the current car park. Add no new bay rows.
- Ngong Road frontage (audit fix 9, Q7). Keep the current centrelines, lane count and junctions.
- Tree maturity (Q8) and the third track (Q9). No change.
- Jamhuri sports ground. It stays a field (about x 224, z -288, from Munene's map screenshot).

## Checks after pass I

- Render D01, D02, D03 and P01 at 1080p, as in Step 3 of the handoff.
- Make sheets: D01 against 000645.000, D02 against 000714.767, D03 against 000617.567.
- In D02, the south-west area must show grass inside the loop road, with no cars.
- In D01 and P01, the west forecourt must show lawn and red crossed paths, with no cars.
- In D03, the east approach must show a broad pale area with a centre island, not a narrow road.
- Write the gaps in the pass I README. Write any conflict with this file under "Questions for the lead".
