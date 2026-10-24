# Layout final 01: pass F, the final layout from the dusk photo and the GE trace (finished state)

> **Withdrawn 2026-10-23.** The source image, `research/reference/dusk_aerial_finished_2026-10-17.jpg`, is AI-generated
> (made with Argon, confirmed by Munene). It is not a photo and not evidence for layout, positions or sizes. The layout in
> this pass is withdrawn (engineering/layout_audit_01/LEAD_REVIEW.md, revision 2). Pass I
> (`blender/context/layout_pass_i.py`, `blender/renders/layout_pass_i_01/`) replaces it. Camera P01 stays a viewpoint only.

Lead order of 2026-10-22, pass F.

The dusk aerial photo of the finished site is internal reference only. It is not a texture and not public.
- Photo: `research/reference/dusk_aerial_finished_2026-10-17.jpg`, merged from `lead/facade-measure`.
- The sheets that contain it are named `*_internal`.

## The photo looks south-south-east, not north-west

The photo's left/right reading in the order is reversed, so the station, railway and big car park belong on the **west**, not the east.

The camera was solved to the photo; it is now camera **P01** in `app/cameras/manifest.json`.
- **Bearing:** it hangs north-north-west of the bowl over Ngong Road, about 450 m out and 167 m up, looking SSE. The lens is 36.5 mm on 36 mm, horizontal field 52°.
- **Fit:** least squares on the bowl outline and opening, the NE track pitch centre and the Ngong Road kerb.
- **Residuals:** 1 to 12 px on the 1600 px photo; the opening is worse, at 17 to 40 px.
- **Ground fit:** the track pitch centre back-projects to within 3 m of its W1b position.
- **The order is reversed:** the order reads the photo as looking north-west. In fact:
  - Ngong Road is the road across the bottom.
  - The warm-up track pitch, with the east pitch and the east hardstanding behind it, is on the left.
  - The car park, the dual carriageway, the railway, the station and the footbridge are on the **right**, which is the **west** side of the site.
- **Other evidence agrees:** the D01 frame (from the north) and the D02 frame (from the south) both show the car park and a long road/rail corridor on the west.
- **Where things went:** the east keeps the GE hardstanding. The photo shows it as a yard full of plant, so it stays a car park.
- **The skyline:** the CBD skyline in the photo does not fit this camera direction; the CBD lies behind it, to the ENE. The backdrop is probably edited, so it is not used.

## Change list (finished state; the asbuilt state is unchanged)

All new positions are back-projected from the photo through P01 (`blender/data/layout_final.json`). They are good to about ±15 m near the camera and ±30 m on the far side. The dimensions are ledger rows `site.*` dated 2026-10-22.

| Feature | Old | New | Source |
|---|---|---|---|
| West dual carriageway | none (an OSM service road ran north–south through the site, not modelled) | 21 m road at x about -156, from Ngong Road south past the bowl to z 700. Median, verge, kerbs, lane markings, lamps every 40 m. 26 moving cars. | photo |
| Railway | none (the OSM metre-gauge line is 800 m north) | two tracks on an 11 m ballast bed at x about -204, from Ngong Road south; rails and sleepers | photo |
| Station | none | side platform 8.5 x 240 m between the road and the tracks; two plain canopies (74 m and 78 m long, 5.2 m high); paved station forecourt. No signs. | photo |
| Footbridge | none | 79 m enclosed deck over the road and both tracks, 6.6 m clear above the road, with three stair towers (car park verge, platform, west side). Plain masses. | photo |
| North-west car park | west forecourt lawn with murram X paths, palms and trees | asphalt car park of 9,400 m² between the plaza and the west road: bay rows on a 16.5 m module, lamp rows, 318 parked cars. The lawn, its paths, beds and palms are hidden in the finished state. | photo |
| Spine between plaza and car park | lawn edge bed | murram beds with planted wedges | photo |
| South-west lot | lawn pitch inside the loop road (trace from D02) | asphalt lot inside the same loop road: bay rows, a planted diagonal strip, 207 parked cars. The pitch lines and the small stand west of it are hidden; the stand is kept in the asbuilt state. | photo (far side); loop road from D02 |
| Road between the training pitches | radial footpath | 8 m road from the north-east road, between the track pitch's south end and the east pitch, to the bowl apron | photo |
| Road from the east along the frontage, past the track pitch to the plaza | already modelled as `ge_road_north_east` (step L) | kept. The photo confirms it: it is the road the order reports as missing. | GE + photo |
| Forecourt paths and beds | pale paving paths (`fp_paths`), green beds (`fp_beds`) | red murram paths; murram beds with planted wedges. The plaza and the bowl apron stay pale, as in the photo. | photo |
| Old OSM footways inside the site | pale strips across the lawns | dropped inside the W1b site boundary in the finished state | photo + GE |
| NE track ring | terracotta | dark asphalt grey | photo |
| East car park cars | white boxes (pass E) | car figures (body, glass cabin, painted roof, tyres) in eight paint colours, same places, 226 cars. Visualization. | order |
| Ngong Road traffic | white boxes (pass D) | the same car figures, 420 cars, plus 73 matatus and buses as plain bodies with a glass band. Visualization. | order |

Shared objects that the new layout covers (trees, the boundary fence, the facade apron, OSM roads, traffic) get a cut copy for the finished state. The uncut original stays for the asbuilt state (`blender/scene_state.py`, new per-object `state_only`).

## Renders (1080p, Cycles 128 samples, look layer on, step_FF = step_FE + `blender/context/layout_final.py`)

| Render | Camera | Light | Time |
|---|---|---|---|
| P01_sunset_landing_hero.png | P01, solved to the dusk photo, 1920 x 1288 (photo aspect) | sunset_landing (dusk lights) | 17.0 min |
| D01_daylight_landing_hero.png | D01 | daylight_landing, -1.2 EV | 8.3 min |
| D02_daylight_landing_hero.png | D02 | daylight_landing, -1.2 EV | 9.7 min |

`sheets/P01_vs_photo_internal.jpg` sets the P01 render against the photo:
- side by side;
- a 50 % overlay;
- an edge comparison, photo edges in cyan and render edges in orange.

It is built with `blender/scripts/photo_sheet.py`.

## Gaps

1. **The camera solve is not exact.**
   - The front shield sits about half a shield spacing off between photo and render. Either the photo's lens distorts (a wide drone lens), or the bowl's shield bearing is off by about 10°.
   - The far side (more than 300 m from the camera) is good only to about ±30 m.
2. **The railway's real alignment is not known.**
   - It is not in OSM; the OSM metre-gauge line runs 800 m north. It is placed from the photo alone.
   - It ends at the Ngong Road kerb. The crossing (bridge, underpass or level crossing) is not modelled.
3. **The station and footbridge are plain masses.** There are no stairs, lifts, glazing detail, signs or people flows (AGENTS.md rule 8).
4. **The south-west construction site** with cranes, beyond the far west lot, is not modelled. It is temporary.
5. **The far track pitch beyond the east pitch is not modelled.** The photo shows one (top left), and the equipment yard beside it. It back-projects outside the W1b site and is not in the GE trace.
6. **The east pitch's position is uncertain.** The photo puts its centre about 70 m north-west of the W1b position. W1b was kept, because the far-left error of the photo camera is that large.
7. **People here are still pass E's stick figures**, thinned where the new layout covers them. Pass H replaces them (`blender/renders/people_final_01`).
