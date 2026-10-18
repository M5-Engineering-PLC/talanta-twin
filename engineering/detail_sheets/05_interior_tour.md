# Detail sheet: INTERIOR FROM THE ARCHITECT TOUR (IT)

Date: 2026-10-18. Source: JWNowpO44rw, the tour chapters 0:00-2:50, 4:42-12:39 and 18:52-28:34, with the KDF project architect.
Frames: 160 new keyframes in research/frames/JWNowpO44rw/, listed in research/video_index/interior_keyframes_2026-10-18.csv. Luna labelled them from contact sheets. The lead checked 11 frames at full size (the IT rows below cite them).
Three frames were marked sensitive (control, security or equipment rooms). They are not in the repository. Do not model those rooms.
This sheet adds to 02_bowl_seats.md (BS). Where the two disagree, this sheet wins, because it uses newer and closer frames. Everything here is "by eye" unless a measurement is named.

## Findings that change the model

| id | element | what the frames show | source frames | status | build note |
|---|---|---|---|---|---|
| IT01 | Tier structure | Three seating tiers. Lower tier mint turquoise. Middle tier a red and salmon mosaic. Upper tier a maroon and red mosaic. A continuous band of glazed boxes with white columns sits between the middle and upper tiers. | 000945.200, 002144.300, 000735.433 | estimated | Check the tier breaks and the box band height against these frames. |
| IT02 | Middle-tier mosaic | Seats in two or three red tones (red, salmon, pink) mixed in a fine random mosaic, not a single red field. Small pale panels on the tier front. | 000945.200 | estimated | Use a seeded per-seat mix of 3 red tones. Replace the BS03 green flecks only if the frames confirm no green. |
| IT03 | Upper-tier mosaic | Maroon and red mosaic with lighter seats scattered through it. Vomitory portals with signs above them at regular spacing. | 000945.200, 002320.200 | estimated | Mix 3 tones. Add portal openings with a plain sign panel. Do not copy the sign text. |
| IT04 | Box band | A row of glazed boxes with dark glass and white mullions or columns, between the middle and upper tiers, all around the bowl. | 000945.200, 000735.433 | estimated | Model as a continuous glazed band with regular white columns. Count the bays in one quarter from the frames. |
| IT05 | Lower-tier seats | Mint turquoise seats with white or pale stair aisles. Confirms BS01. | 000043.333, 000945.200 | estimated | Keep BS01. Check the hex against 000945.200 in daylight. |
| IT06 | Aisle stairs | Pale concrete aisle stairs cut through each tier. Metal handrails along the aisles and at the tier fronts. | 000735.433, 000738.500, 000952.600 | estimated | Add a handrail down each aisle and along each tier front. |
| IT07 | LED ribbon boards | Continuous LED ribbon boards along the tier fronts (green and blue in the frames). | 001940.267 | estimated | Add an emissive ribbon on the lower and middle tier fronts. Matchday mode only. |
| IT08 | Glass balustrades | Glass balustrades at the front of the upper levels and walkways. | 002320.200 | estimated | Glass panels about 1.1 m high on the upper tier front. |
| IT09 | Upper gallery | A walkway behind the upper tier with white railings and tall white round columns that carry the roof. The roof edge is visible above it. | 000131.700, 000137.333 | estimated | Check against the existing gallery_rail (bowl.gallery.*). |
| IT10 | Roof underside | A diagonal steel lattice of primary trusses and secondary members, under translucent membrane panels. The panels are brighter near the outer edge. Hanging cables. | 000154.067, 000131.700, 000137.333 | estimated | Light grey steel. It reads dark against the bright membrane. Keep the membrane translucent. |
| IT11 | Floodlight catwalk | A truss catwalk ring under the roof near the opening, with a dense row of LED floodlight heads. | 000154.067 | estimated | Check against the existing floodlights (bowl.roofsteel.*). Spacing by eye from 000154.067. |
| IT12 | Video screen | A large screen hangs under the roof. | 000137.333 | estimated | Keep the existing screen (bowl.screen.*). Check the position against this frame. |
| IT13 | Concourse under the upper tier | An open concourse with a long row of white round columns, a grey concrete floor and exposed services above. It looks onto the bowl. | 002144.300 | estimated | Model the column row and the floor. Services as simple dark ducts. |
| IT14 | Interior rooms and corridors | Pale walls, polished or tiled floors, door openings, recessed ceiling lights, dark linear ceiling panels. | 000833.400, 002212.567 to 002317.200 | estimated | Low priority. Only for interior views. No room may show security or control functions. |
| IT15 | Pitch | Natural grass pitch with a pale apron and a ring of advertising and technical space. | 000945.200, 002331.700 to 002405.667 | estimated | Keep. |

## Method for the interior pass

1. Frame-matched cameras: for 6 interior frames (000945.200, 002144.300, 000735.433, 000154.067, 002320.200, 000131.700), place a Blender camera that matches the frame. Use the pitch lines (known IFAB dimensions) and the bowl rings as anchors. Record the cameras as C30 to C35.
2. Counts from the frames: rows per tier, aisle spacing, vomitory count per side, box bays per side, floodlight heads per segment. Write each count to the ledger as "estimated (frames ...)", or as "derived" when two or more frames agree.
3. Build the changes IT01 to IT13 in blender/build_bowl_detail.py.
4. Render the 6 matched cameras at the check settings and make side by sides against the frames.
5. Score each view on the 8-category rubric. Mark people "Visualization".

## Rules

- The frames are internal reference only. Never use them as textures.
- No security detail: no control rooms, CCTV, access control, exit signs or gate hardware in any public output.
- The architect's name appears in the video. Do not put it in public output.
