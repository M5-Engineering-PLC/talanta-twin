# Pass I and J check renders (1080p, step_FJ)

Work order: engineering/cloud_handoff_2026-10-23.md, Step 3. Internal only: the sheets hold drone frames.

## Scene and settings

- Scene: `step_FJ` = step_FE + `layout_pass_i.py` (pass I) + `people_figures.py` + `crown_detail.py` + `landmarks_pass_j.py` (pass J).
- Finished state, look layer on (`TALANTA_LOOKDEV=1`), Cycles hero quality (128 samples), 1920 x 1080 (P01 at its own aspect).
- People, cars and lights are a Visualization, not a count, occupancy or safety study.

| Render | Light | Time |
|---|---|---|
| D03_daylight_landing_hero.png | daylight_landing | 15.1 min |
| D02_daylight_landing_hero.png | daylight_landing | 12.2 min |
| D01_daylight_landing_hero.png | daylight_landing | 9.8 min |
| L07_daylight_landing_hero.png | daylight_landing | 11.5 min |
| P01_sunset_landing_hero.png | sunset_landing | 19.4 min |

## Sheets (`engineering/review_sheet.py`: render, frame, 50 % blend, edges; JPG quality 90)

- `sheets/001_D01_..._000645.000_internal.jpg`
- `sheets/002_D02_..._000714.767_internal.jpg`
- `sheets/003_D03_..._000617.567_internal.jpg`

There is no P01 sheet. Its reference is the AI-generated image (LEAD_REVIEW.md), which proves nothing.

## Checks from LEAD_REVIEW.md

| Check | Result |
|---|---|
| D02: grass inside the loop road, no cars | pass: green lawn, no markings, no cars; loop road and small stand shown; lines up with the frame's grass rectangle |
| D01 and P01: west forecourt lawn and red crossed paths, no cars | pass |
| D01, D02, L07: no west dual carriageway, railway, station or footbridge | pass |
| D03: broad pale east approach with a centre island, not a narrow road | pass: pale paving from the apron to the east, island in the centre, the peripheral road stops at the paved edge, no lanes or cars |

## Change list

- **Pass I** (`blender/renders/layout_pass_i_01/README.md`): the pass F layout is removed and its hidden or cut objects
  are back. Added: east approach and island, SW grass without markings, NW lawn and paths. Kept: red murram paths,
  dropped OSM footways, car figures.
- **Pass J** (`blender/renders/landmarks_pass_j_01/README.md`): 12 real buildings as plain masses from the gpkg.
  Generic masses on their footprints are removed.

## Gaps

1. The renders show the finished state. The frames show construction (murram, bare earth), so the colour of the
   ground differs everywhere in the sheets. The as-built state is unchanged and is not re-rendered here.
2. D03: the frame's island is a longer, pointed lens. Ours is the review's four-corner kite (±20 m).
3. D03: the frame's approach is warm pale murram; ours uses the apron's pale paving. The finish is unknown (Q4).
4. L07 and D02: the Enkang blocks show only their top floors above the bowl roof. Denali, Alba and White Village show
   in the city behind. Ngando, Liberty Centre and Racecourse Gardens are hidden or too low to read.
5. D01: the track pitch is green and terracotta in the finished state; the frame shows construction there (held, Q5).
6. P01: the dusk view still carries the pass E town lights and fixtures. Nothing in this render comes from the AI image.

## Questions for the lead

None that conflict with LEAD_REVIEW.md.
