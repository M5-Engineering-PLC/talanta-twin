# Interior pass 01 (detail sheet 05, IT01-IT13)

Internal review only. The side-by-sides contain tour frames from JWNowpO44rw, which are internal reference only
(AGENTS.md rule 2). Do not put these sheets, or the frames in them, on a public page. No frame was used as a texture.

## Cameras C30-C35

Defined in blender/scripts/make_interior_cameras.py, written to blender/data/interior_cameras.json, and loaded by
render_cycles.py as extra cameras. They are render viewpoints for review, not real camera locations (rule 8). They are
not in app/cameras/manifest.json. The lead copies them there if they are wanted in the app.

| camera | frame | view | lens |
|---|---|---|---|
| C30 | 000945.200 | pitch level near the west touchline, across to the east stand | 26 mm |
| C31 | 002144.300 | west concourse at the top of the lower tier, along the concourse | 24 mm |
| C32 | 000735.433 | east concourse by a column, across the bowl to the west stand | 24 mm |
| C33 | 000154.067 | back of the east upper tier, up to the catwalk ring and the roof lattice | 30 mm, roll -12 |
| C34 | 002320.200 | north end, upper tier front walkway behind the glass balustrade | 22 mm |
| C35 | 000131.700 | east upper gallery behind the top row, along the gallery | 22 mm |

The cameras are matched by eye, not solved. Five of the six frames show no pitch lines or other fixed points to
solve from. The poses are on the measured bowl rings (blender/out/bowl_rings.json) at the tier and band heights.

Light: neutral daylight at 12:30 EAT on 2026-01-15, with +1 EV per camera (`exposure_ev` in the camera file). The tour
frames are hand-held with auto exposure, so the interiors read about 1 EV brighter than a fixed exposure would. The
first renders under the overcast key came out at L* 16-24 and blue (b* -10 to -17) against L* 40-60 and b* +2 to +10
in the frames. They were replaced.

Settings: check (960 x 540, 32 samples), TALANTA_LOOKDEV=1. The times are in render_log.jsonl.

## Built (blender/build_bowl_detail.py, section F, and the seat tones in section B)

| item | what |
|---|---|
| IT01-IT03, IT05 | three seeded seat tones per tier (ledger bowl.seat.*_tones, *_tone_weights): mint turquoise lower tier, red, salmon and pink middle mosaic with a little green, maroon and red upper mosaic; 12 middle-tier rows (bowl.tier_middle.rows_blockout) |
| IT03 | 27 upper-tier portals (one per aisle) and 14 middle-tier portals (every other aisle), with white frames and blank panels. Generic openings, no signs and no egress meaning |
| IT04 | glazed box band between the middle and upper tiers: dark glass, white sill and head, 54 white columns (2 bays per aisle block) |
| IT06 | tier-front rails (the aisle rails were already built) |
| IT07 | LED ribbon boards on the lower and middle tier fronts. Emission 0 by day, matchday only, labelled Visualization |
| IT08 | 1.1 m glass balustrade on the upper tier front |
| IT09 | upper gallery: the existing walkway, white rails, colonnade and louvred screen (section D) kept unchanged |
| IT10 | diagonal lattice members between neighbouring primary roof trusses |
| IT11 | 240 floodlight heads on the catwalk (4 per bay between primaries) |
| IT12 | the existing video boards kept; position not re-checked against 000137.333 |
| IT13 | open concourse bowl.concourse.depth (10 m) deep under the middle tier: grey floor, dark back wall, simple dark ducts, the white VIP column row moved to its back (1.5 m in from the back wall); the 2 m VIP glass wall at its front is hidden (the frames show a low kerb) |

Seats: 56,858 (unchanged count; tones only). 27 aisles per ring.

Not built: control rooms, CCTV, access control, gate hardware, exit signs and routing (rule 8). The three sensitive
frames are excluded and their rooms are not modelled. IT14 (interior rooms) is not built. No people are in the renders.
People would be labelled Visualization.

## Ledger rows (gis/scripts/build_parameter_ledger.py, `itr`)

bowl.seat.{lower,middle,upper}_tones and _tone_weights, bowl.tier_middle.rows_blockout, bowl.portals.upper_per_aisle,
bowl.portals.middle_every, bowl.portals.width, bowl.portals.height, bowl.portals.panel_hex, bowl.boxband.bays_per_aisle,
bowl.concourse.floor_hex, bowl.concourse.back_hex, bowl.concourse.depth, bowl.band.vip_glass_y0_blockout,
bowl.balustrade.h, bowl.led_ribbon.h, bowl.led_ribbon.strength, bowl.floodlights.per_bay. All are estimated from the
frames named in each row, apart from the middle row count (derived, 2 frames).

## For the lead

- The portals are generic openings. Keep them out of the public web export unless you approve them, because a public
  viewer could read them as exits (rule 8).
- To use C30-C35 in the app, copy them from blender/data/interior_cameras.json into app/cameras/manifest.json. The
  manifest fields are unchanged, apart from the optional `roll_deg` and `exposure_ev`.

## Files

- C3x_neutral_check.png: renders.
- C3x_side_by_side.jpg: render | frame (internal).
- metrics.csv: CIELAB mean, L* spread, edge density and clipping for the whole view and its top, middle and bottom
  thirds, render against frame (blender/concept_match/interior_metrics.py).
- scores.csv: 8-category scores. Total 56.1 over the observed categories.
- render_log.jsonl.

## Result and next fixes

Score 56.1 (scores.csv). Next:

- Re-pose C32 under the concourse ceiling, and pull C35 off the colonnade. Lower C30 to about 1.6 m eye height.
- Darken the membrane underside seen from inside: the frames show a dark, backlit roof with bright panels only near
  the outer edge (IT10).
- Warm the interior white balance (b* is 8 to 20 low), and give the turf mowing stripes and a deeper green.
- Add the concourse ceiling slab and its services to the 002144.300 view.
