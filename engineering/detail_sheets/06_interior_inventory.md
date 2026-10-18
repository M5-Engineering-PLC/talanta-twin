# Detail sheet: FULL INTERIOR INVENTORY (IF)

Date: 2026-10-18. Source: JWNowpO44rw, the full video (0:00 to 31:01) and its YouTube auto transcript.
Frames: the 160 tour keyframes, plus 457 dense frames (one every 2 to 8 s) from the transcript spans that show the interior. 29 dense frames are cited and are now in research/frames/JWNowpO44rw/. The other dense frames stay on the lead machine.
Method: Luna read 33 contact sheets and the transcript and wrote 69 rows. The lead checked the media, VIP and closing spans at full size. The lead corrected 4 rows and added 5 rows.
Feature table: engineering/detail_sheets/06_interior_features.csv (74 rows, IF01 to IF74). This sheet adds to 05_interior_tour.md. Where they disagree, the IF rows win.
Everything is "by eye" unless a frame count or a transcript time is given.

## Facts from the transcript

| time | fact | use |
|---|---|---|
| 2:11, 3:43, 7:05 | 60,000 seat capacity | capacity target (see the seat section) |
| 5:01 | VIP parking on the west side of the stadium | puts the VIP stand on the west side |
| 5:32 to 5:49 | three training pitches; the west one has a 1,500 seat stand, changing rooms and an 8 lane track | site context |
| 6:32 to 6:57 | north, south and east plazas; a fan zone by Ngong Road with a giant screen and terraces | site context |
| 7:41 to 8:33 | media section high in the bowl, media sockets, media offices; one office door reads L416 | media tribune is likely on level 4 |
| 10:27 | the roof structure rises to roughly 54 m | supports the kept 54 m crest in the geometry pass |
| 12:08 | the 8 shields mark the 8 main gateways | exterior; confirms 8 |
| 20:03 | musical water fountain | plaza feature |
| 22:47 to 23:12 | VIP section with lifts; a presidential lounge | VIP level |
| 23:55 | 52 sky boxes | box band count |
| 24:17 to 24:30 | VIP seats with cup holders | VIP seat type |

Access gates, turnstiles and exit functions are in the transcript (5:01 to 5:23, 12:08 to 12:29). They are security detail. They are marked sensitive in the CSV and have no build note. Do not model them in any public output.

## Lead corrections to the Luna rows

- IF08 VIP seat position: the VIP seats are not beside the pitch. They sit high, in rows in front of the presidential lounge glazing, with the green lower tier below. A glass balustrade with a steel top rail guards the front (002400.000, 002406.000, 002421.000, 002433.000).
- IF31, IF32 media desks: not seen. Frames 000745 to 000805 show plain red seats on a steep high tier. The desks may not be installed yet. Do not model desks.
- IF36 media opening: the media seats are open to the bowl. No glazing is seen.
- Added IF70 changing room showers, IF71 tunnel mouth at pitch level, IF72 corridor ceilings, IF73 aisle sign columns, IF74 lower concourse view.

## Build priorities for the cloud

Priority 1 changes what a bowl camera sees:
1. VIP stand on the west side: a lounge with full height glazing, 3 to 4 rows of wide red upholstered seats with cup holders, a glass balustrade (IF07, IF08, IF39, IF40).
2. Media tribune: a block of plain red seats high on one long side, open to the bowl, with a row of offices behind it (IF30, IF33, IF34). Side not confirmed; use the east stand until a frame proves otherwise.
3. Tunnel mouth at pitch level in the lower tier front, and two dugouts on the same long side (IF44, IF45, IF71).
4. Aisle sign columns, portal sign panels and dark tier front bands (IF15, IF16, IF17, IF73). No sign text.
5. Two LED ribbons, green and blue, around the bowl (IF18). Matchday mode only.
6. Small screens hung from the roof trusses, and visible hanging cables (IF20, IF25).
7. Lower concourse: the top row of the lower tier is level with the concourse floor (IF74).

Priority 2 is only for interior views (low priority):
- VIP lobby and lifts, media offices, corridors with dark slat ceilings and linear lights, toilets, changing room showers (IF35, IF37, IF38, IF51 to IF54, IF70, IF72).
- Musical fountain on a plaza (IF56, IF57).

## Seat capacity: 56,972 modelled against 60,000

- The model makes its seats from estimated tier rows (lower 24, middle 13, upper 21), a 0.5 m seat pitch and an aisle every 16 m. The result is 56,972, which is 3,028 seats (5.0%) short.
- Luna's frame counts are wide: lower 18 to 24, middle 12 to 16, upper 19 to 24 rows. They do not settle the gap.
- The 60,000 is a narrated design capacity. It may include the VIP seats, the media seats and the 52 sky boxes (about 10 to 20 places each, so 500 to 1,000 places). The model does not count these as seats now.
- Most likely cause: the middle tier has more than 13 rows, and the curved ends hold more seats than the model gives them.
- Next step: count the rows on the matched interior cameras C30 to C35 (the cloud has them). Count one full block per tier, square on. Then set the rows from that count and add the VIP, media and box places as separate counts. Do not tune the seat pitch to reach 60,000.

## Gaps

Luna listed 15 features that this video cannot settle (seat schedule, box seats, media side and desks, lift count, tunnel and dugout size, kiosks, floodlight count). See engineering/detail_sheets/06_interior_gaps.md.

## Rules

- The frames are internal reference only. Never use them as textures.
- No security detail in public output: no gates, turnstiles, exits, exit signs, CCTV, control rooms or access routes.
- Do not copy sign or door text into the model.
- Do not name the architect or the guides in public output. Mark people "Visualization".
