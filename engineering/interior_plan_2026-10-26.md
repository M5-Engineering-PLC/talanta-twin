# Interior plan for walkthrough chapters 3 and 4 (workstream A)

Date: 2026-10-26
From: the cloud build session, for the lead and Munene
Branch: `wo/web-hero-v2`
Order: lead order 2026-10-26, item 2. This plan does not wait for approval. The work continues after the push.

## 1. What the chapters show

- Chapter 3 "Going in" (6 to 10 s): the camera starts in the enclosed outer concourse (frame 000404.000: dark slatted ceiling with LED lines, white round columns). It moves along the concourse, turns into one spectator entry in the concourse back wall, goes through the entry passage into the open inner concourse (frame 002144.300: low soffit, exposed ducts, open to the bowl) and comes out at the head of a lower-tier aisle. The last frame looks across the bowl to the far stand and the roof.
- Chapter 4 "A lap of the bowl" (6 to 10 s): one closed loop at stand height, at about the middle of the lower tier (row 8 of 15), with the camera above the seats and looking into the bowl. The last frame is the first frame, so the chapter can loop.
- Chapter 3 ends at the top of the lower tier, and chapter 4 starts in the same stand, so the cut between them is short.

## 2. The entry for chapter 3

- Side: south-east, about 120 deg round the bowl from the west side. The west side has the tunnel mouth and the VIP stand (placeholders, bowl.tunnel.side and bowl.vip.side). The entry is far from both.
- The entry is a generic spectator entry through the concourse back wall (the IT13 back wall line), on the axis of a lower-tier aisle. The same plain openings repeat at every second lower-tier aisle (14 round the bowl); only the chapter 3 entry has a full passage (3.0 m wide, 3.2 m high, 5.4 m long). No source marks it as an emergency exit, and the model does not mark it as one.
- Frame 000412.000 (a passage at pitch level) is not used: it is near the players' area.
- Rule 8: no shot frames an exit, an exit sign, a control room, a security room or a camera position. The model has no exit signs, no signs with text, no turnstiles, no gates, no CCTV, no doors to back-of-house rooms and no stair cores in the camera views. The concourse is generic where no frame shows it.
- Not modelled: the player tunnel (only the existing dark mouth stays, and no shot frames it), the dressing rooms, the media offices, the toilets and any back-of-house space.

## 3. What is modelled

All new objects go in new collections. They are not in the web_hero_v2 twin export (export_web.py does not read these collections). A later bundle can export them.

| Collection | Contents | Seen in |
|---|---|---|
| interior_concourse | inner concourse (open to the bowl): polished floor, a low concrete soffit, a pale fascia up to the middle tier, exposed ducts, linear fittings; the back wall with pale panels, the entries and blank panels (no text) | ch3; ch4 at distance |
| interior_outer_concourse | outer concourse (enclosed): polished floor, dark slatted ceiling, white round columns, pale outer wall with closed kiosk shutters (generic, no text) | ch3 |
| interior_concourse_lights | the LED lines and fittings as emission, plus Cycles area lights within 60 m of the entry (real lights for the dusk and night looks) | ch3 |
| interior_entry | the chapter 3 entry passage: wall returns, a lintel, wall light lines | ch3 |
| interior_stand | the lower-tier surfaces at close range: a new seat model, step nosings, aisle handrails, the rail at the aisle head, a tread edge strip | ch3, ch4 |
| interior_roof_under | the roof underside as seen from the stands: secondary lattice members, cable clamps and the catwalk detail (the primaries, cables, catwalk and floodlights exist) | ch3 end, ch4 |

The stand surfaces stay in the existing objects where they exist (tiers, aisle_steps, seats). Section 7 lists the changes that the aerial views can see.

## 4. Sources

Facts: research/Talanta_design_facts_2026-10-16.md (seat colour gradient green, red, black; fixed canopy on tensioned cables). Geometry and finishes: the reference frames by view class (research/video_index/MASTER_INDEX.csv), the detail sheets 05 and 06 (engineering/detail_sheets/) and the parameter ledger (gis/parameter_ledger.csv).

| View class | Frames used (internal reference only) | For |
|---|---|---|
| concourse_interior | JWNowpO44rw 000404.000, 002600.000, 002144.300 (sheet 05 IT13); IF72 frames 002530.000, 002545.000, 002550.000 | concourse height, slatted ceiling with LED lines, white round columns, grey polished floor, pale walls |
| concourse_interior | cyNgbyZv6BM 001002.000, 001118.000 | pale walls, closed roller shutter (kiosk front), polished floor |
| bowl_seating | JWNowpO44rw 002714.067, 002746.867 (seat detail), 000751.000, 002427.667, 002637.467, 002320.200 | seat shape, aisle steps and rails, glass balustrade, tier fronts |
| bowl_seating, roof_canopy | JWNowpO44rw 000155.599, 000200.000, 002828.467; IF22 and IF23 frames | roof underside lattice, membrane, speakers, catwalk |

- The frames are used to model. No frame goes into a texture or a render (AGENTS.md rule 2). The finishes are plain materials with CC0 PBR maps from blender/assets.
- Rules 5 and 6: no geometry from video oL3wsPsx4Jw or from Nyayo frames (video PWj9s_v3G6U). None of the frames above is from them.
- Sign and door text in the frames is not copied. Frame 002256.000 shows an exit sign over a door; it is not modelled.

## 5. Facts table

Status: measured (from a plan or a survey), derived (from two or more frames), or estimated (by eye or by typical practice). Values marked estimated go into the ledger as estimated.

| Item | Value | Status | Source |
|---|---|---|---|
| lower tier front row radius (east) | 39.5 m from the pitch centre | estimated | ledger bowl.seat_start.*, bowl_rings.json rIn |
| lower tier rows | 15 | derived (2 frames) | ledger bowl.tier_lower.rows_blockout |
| lower tier rise | 1.2 m to 12.5 m above the pitch pad | estimated | ledger bowl.tier_lower.y0, y1 |
| lower tier tread and riser (from the envelope) | 1.32 m and 0.75 m | estimated | 15 rows over the modelled depth; see section 8 |
| concourse floor | at the top tread of the lower tier | estimated | sheet 06 IF74, ledger |
| concourse depth under the middle tier | 10 m | estimated | ledger bowl.concourse.depth (+-3 m) |
| concourse height to the middle tier underside | about 7.4 m at the front (the new soffit closes it at 4.4 m) | estimated | model geometry |
| ceiling slats | 0.10 m wide, 0.30 m deep, at 0.40 m centres, dark grey | estimated | frames 000404.000, 002600.000 (IF72) |
| LED strips | 0.08 m wide lines across the slats at about 3 m centres, about 4,000 K | estimated | frames 000404.000, 002600.000 |
| concourse columns | white, round, 0.45 m radius, 8 m centres | estimated | ledger bowl.vip.column_*, frame 000404.000 |
| back wall panels | pale grey-white, 1.2 m x 2.4 m with 10 mm joints | estimated | frames cyNgbyZv6BM 001002.000, JWNowpO44rw 002248.000 |
| floor | grey polished concrete, 1.2 m joints | estimated | frames cyNgbyZv6BM 001002.000, 001118.000 |
| kiosk fronts | 6 m wide closed roller shutters, about 3 m high, every 2nd column bay on the back wall, no text | estimated | frame cyNgbyZv6BM 001002.000 (shutter); sheet 06 gap list (no clear kiosk) |
| inner concourse clear height (to the new soffit) | 4.4 m | estimated | frame 002144.300 (about 2.5 person heights) |
| outer concourse | 11 m deep behind a 0.4 m back wall, 4.6 m to the slats | estimated | frame 000404.000; generic |
| entry passage | 3.0 m wide, 3.2 m high, 5.4 m long, through the back wall | estimated | ledger bowl.portals.* scale; generic |
| entry position | the back wall on the axis of lower-tier aisle 4 of 27, at 62.9 deg from east towards south (about 117 deg from the west centre line) | estimated | chosen (section 2) |
| seat | 0.44 m wide, pan at 0.42 m, back about 0.40 m above the pan, moulded shell with a rolled top edge, a number plate on the back (blank) | estimated | ledger bowl.seat.*, frames 002714.067, 002746.867 |
| seat pitch along the row | 0.50 m | estimated | ledger bowl.seat_pitch |
| aisle handrails | steel, 0.05 m tube, 0.9 m high, posts every 2 rows, one rail in the aisle centre | estimated | frames 000751.000, 002637.467 |
| step nosing | 0.05 m pale strip on each aisle step | estimated | frame 000751.000 |
| aisle-head rail and glass | glass balustrade 1.1 m with a steel top rail | estimated | frames 002320.200, 002427.667 (sheet 06 IF08 scale) |

## 6. Budget

| Item | Triangles (unique) | Instances | Memory (CPU render) |
|---|---|---|---|
| concourse ring (floor, ceiling slats, columns, walls, shutters, rail) | about 600,000 (slats and columns instanced from 2 protos) | about 30,000 slats, 70 columns | about 0.3 GB |
| LED strips and area lights | about 20,000 | about 400 lights (area lights in the ch3 arc only; emission elsewhere) | small |
| entry passage | about 20,000 | | small |
| new seat model | about 600 per seat (was 36) | the existing 48,664 seat instances | about 0.2 GB (instances) |
| aisle handrails, nosings, aisle-head rails | about 300,000 | | about 0.1 GB |
| roof underside members and clamps | about 200,000 | | about 0.1 GB |
| Total added | about 1.1 M unique, 29 M instanced | | about 0.7 GB more than the 4.5 GB now; inside the 16 GB of a Kaggle T4 |

Render time: chapter 3 is lit by the concourse lights and the bowl daylight, so the frame time can be about 1.5 times the day exterior. The 16-sample previews measure it.

## 7. Stand changes that the aerial views can see (they change the next bake)

- The new seat model replaces seat_proto in the bowl. The seat colours, rows and positions do not change. From the aerial views only the shading of the seat blocks changes a little.
- Aisle handrails on every lower-tier aisle (new): thin steel lines, seen in the near-aerial views.
- Step nosings on the lower-tier aisle steps (new): pale lines, seen in the near-aerial views.
- The inner concourse soffit, the pale fascia above it and the pale back wall with its entries (it was dark): under the middle tier overhang, probably not seen from the aerial cameras. The preview from L06 and L07 checks this.
- No change to the tier envelope, the row counts, the middle and upper tiers, the roof top surface or the facade.

These changes go into the bake only if the lead approves them for the twin. Until then the twin export keeps the existing seats and aisles. The film uses the new parts.

## 8. Known issue and decision for the lead

- The lower tier has 15 rows (hand count, derived) in a modelled depth of about 19.8 m and a rise of 11.3 m. That makes treads of 1.32 m and risers of 0.75 m (sheet 06 and tier_section_01 already note this). Typical treads are 0.8 m to 0.9 m. At chapter 4 camera distances the deep treads can show.
- Default in this plan: keep the tier envelope, so the aerial views and the bakes do not change. Chapter 4 keeps the camera above the seats and looks across the bowl, so the treads are seen at a low angle.
- Alternative (needs a lead decision, because the aerial views and every bake change): rebuild the lower tier at 15 rows of 0.80 m by 0.45 m (top at about 7.9 m, as the 3.1 deg view in 000945.200 suggests) and move the concourse down to it.

## 9. Parts (each less than 4 h), with a stop after each part

| Part | Work | Output |
|---|---|---|
| 1 | concourse ring and its lights; the entry passage | blender/build_interior.py part concourse; 16-sample previews from the ch3 cameras; the time used |
| 2 | stand surfaces: the seat model, nosings, handrails, aisle-head rail | part stand; 16-sample previews from the ch3 end and ch4 cameras; the time used |
| 3 | roof underside from the stands | part roof; 16-sample previews from the ch4 cameras; the time used |
| 4 | camera paths ch3_going_in and ch4_bowl_lap in chapters.json and paths.py (6 to 10 s, the L07 lens rules, portrait cuts as for chapters 1 and 2); a 16-sample preview sheet | chapters.json, paths.py, chapters_3_4_preview.jpg |
| 5 | a new render pack with the interior and the G2 state (assets/render_pack, parts under 95 MB, sha256) | then stop and report the time, the preview sheets and the stand change list |

- blender/build_interior.py runs on blender/out/frozen_FK.blend and saves blender/out/frozen_FK_interior.blend. frozen_FK.blend stays as it is (the twin export and the bakes use it).
- The chapter cameras for the previews come from a first version of the chapter 3 and 4 paths. Part 4 makes them final.
- Then the P2 bakes (10:30, 18:05, 20:00 night), as ordered, with a stop after each set.

## 10. Not in this plan

- People, crowds, the concert and the football match. The laptop builds them in the app as data (EVT-01, SPT-01, the data bridge). Nothing is modelled by hand in Blender. The Blender importer comes later.
- Signs with text, wayfinding, exit and safety signs, access control, CCTV, control and security rooms, the player tunnel interior, dressing rooms, media offices and toilets.
