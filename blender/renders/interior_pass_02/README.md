# Interior pass 02 (detail sheet 06, interior inventory, Priority 1)

Internal review only. The side-by-sides contain tour frames from JWNowpO44rw, which are internal reference only
(AGENTS.md rule 2). Do not put these sheets on a public page. No frame was used as a texture. Where sheet 06 and
sheet 05 disagree, the IF rows win.

Not modelled: gates, turnstiles, exits, exit signs, CCTV, control rooms and access routes (IF62, IF69, rule 8). No sign
or door text was copied. People are not built. Any added later are labelled Visualization.

## Seat count (sheet 06 step 1)

Method: one full block per tier, square on, in frames 000945.200 (C30) and 000735.433 (C32). A vertical brightness
profile through the middle of the block, with the row period taken from its FFT peak. Rows = block height / period.

| tier | 000945.200 | 000735.433 | set | status |
|---|---|---|---|---|
| lower | 50 px / 3.16 px = 15.8 | 38 px / 2.2-2.5 px = 14.9-17.2 | 16 (was 24) | derived (2 frames, +-1) |
| middle | 40 px / 3.73 px = 10.7 | 28 px / 2.5 px = 11.1 | 11 (was 12) | derived (2 frames, +-1) |
| upper | cut by the frame top | cut by the concourse ceiling | 21 (kept) | estimated |

Check: in 000945.200 the seats repeat every 2.54 px across the block, against 3.16 px for the rows. The row period
is well above the 2 px pixel limit and is the strongest peak by a factor of 3, so every-other-row aliasing is unlikely.
The periods in 000735.433 are close to the pixel limit and less sure.

The seat pitch is unchanged (bowl.seat_pitch 0.5 m).

| places | count |
|---|---|
| bowl seats (regular) | 48,664 |
| media seats (in the bowl, plain red) | 581 |
| VIP seats (0.75 m chairs) | 216 |
| sky boxes, 52 x 12 places (estimated, 10-20 each) | 624 |
| total | 50,085 |
| narrated capacity | 60,000 |
| gap | 9,915 (16.5 %) |

Pass 1 had 56,858 seats. The gap grew because the counted lower tier has 16 rows, not 24.

Open geometry issue: the lower-tier rake keeps its estimated depth (t 0 to 0.38 of the bowl, about 21.8 m) and rise
(1.2 to 12.5 m). With 16 rows the treads are 1.36 m deep and the risers 0.71 m, which is not plausible. Either the
lower tier is shallower than modelled, or the count misses the front rows. The upper tier was not counted. A
square-on view of a full upper block, and a frame that shows the lower-tier depth (from the pitch edge to the
concourse), would settle both. The capacity gap is best read as an open question, not as a missing 10,000 seats.

## Built (blender/build_bowl_detail.py, sections A and F2)

| item | IF rows | what |
|---|---|---|
| VIP stand, west | IF07, IF08, IF39, IF40 | top 4 rows of the lower tier over a 48 m arc on the west side: wider red upholstered chairs with armrests and a cup holder (vip_seats), glass balustrade with a steel top rail in front of them, full-height lounge glazing with white mullions at the concourse front behind them, a dark tiled lounge floor and beige sofa groups |
| media block, east (placeholder side) | IF30, IF34 | plain red seats in the front 8 rows of the upper tier over a 40 m arc. The 2 box-band bays behind it have pale closed office fronts with plain doors, which leaves 52 sky boxes. No desks (lead: not seen). IF33 sockets are not built (too small to see from the bowl cameras) |
| tunnel mouth, west (placeholder side) | IF44, IF71 | 8 m x 3.2 m dark opening at pitch level in the lower tier front, pale concrete walls and lintel; the front rows above it are cut |
| dugouts | IF45 | two low covered shelters on the tunnel side, 12 m long, from 4 m to 16 m either side of the halfway line, starting 2.5 m outside the touchline (the west tier front is only about 5.3 m out): smoked shell, white front edge, red bench. They replace the BS44 dugouts on the east, whose builder swapped the height and z coordinates and made each one a 28 m tall white box. That box was the white pillar in pass 1's C30. C12 (west touchline) looks out through the gap between the two |
| aisle sign columns | IF73 | white bands on the box-band face at the head of each middle-tier aisle (27), with a blank blue plate, and a blank blue plate on each upper-tier portal head |
| portal panels | IF15, IF16 | kept from pass 1 (generic openings, blank panels) |
| tier front bands | IF17 | dark fascia bands under the middle and upper tiers |
| LED ribbons | IF18 | blue under the middle tier, green under the upper tier, on the dark bands. Emission 0 by day, matchday only, Visualization |
| hung screens and cables | IF20, IF25 | 8 small dark screens (4 x 2.4 m) hung 4 m below the primaries on cables |
| old VIP mullions | IT13 | hidden with the VIP glass they belonged to; they stood in the open concourse front |
| lower concourse | IF74 | the concourse floor is at the lower tier's top tread height (already so in pass 1); checked |

## Cameras (pass 1 fixes)

- C30: eye height 1.6 m, aimed 7.6 deg down so the horizon sits at y 237 of 720 as in 000945.200.
- C32: moved under the middle-tier soffit (tier fraction 0.53; the soffit spans 0.45 to 0.62).
- C35: moved to 0.5 m behind the top row, near the rail, off the colonnade.

- C31: moved from 180 deg to 150 deg (target 115 deg). At 180 deg it landed inside the new VIP lounge, and 002144.300
  shows an open concourse, so that frame is not at the west centre.

C33 and C34 are unchanged. Same light as pass 1: neutral daylight at 12:30 EAT, +1 EV per camera, check settings
(960 x 540, 32 samples), lookdev on.

## Ledger rows

New (`ifr`, gis/scripts/build_parameter_ledger.py): bowl.vip.{side, arc, rows, seat_pitch, seat_hex, balustrade_h},
bowl.media.{side, arc, rows, seat_hex, office_bays}, bowl.skybox.{count, places_each}, bowl.tunnel.{side, width,
height}, bowl.dugout.from_touchline_blockout, bowl.aisle_sign.plate_hex, bowl.tier_front_band.hex, bowl.led_ribbon.colours,
bowl.hung_screens.{count, size, drop}. Changed: bowl.tier_lower.rows_blockout 16 (new) and
bowl.tier_middle.rows_blockout 11 (was 12), both derived (2 frames).

## For the lead

- Media side, tunnel side and dugout positions are placeholders (west for the tunnel with the VIP stand, east for
  the media block). Change bowl.media.side and bowl.tunnel.side when a frame proves the sides.
- The tunnel and portals are generic openings. Keep them out of the public web export unless you approve them, because
  a public viewer could read them as routes (rule 8).

## Result

Score 56.7 (scores.csv; pass 1 56.1). The Priority 1 items read in the views that face them (C32: VIP glazing and
tunnel across the bowl; C33: hung screens). The main remaining mismatch is geometric. The frames show a low concourse
ceiling (C31, C32) and a lower first tier (C30) than the model. That fits the row count (16 lower rows) and the
3.1 deg elevation of the lower-tier top in 000945.200, which puts it near 7 m, not 12.5 m. A tier-section pass from
these frames should come before more interior detail.

Files: C3x_neutral_check.png, C3x_side_by_side.jpg (internal), metrics.csv (interior_metrics.py), scores.csv,
render_log.jsonl (C31 twice: the second line is the re-render at the new pose).
