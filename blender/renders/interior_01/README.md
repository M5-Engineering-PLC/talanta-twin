# Interior 01: 16-sample previews of the chapter 3 and 4 interior

Internal check images. Not for a public page. People, vehicles and lighting are illustrative (Visualization).
Plan: engineering/interior_plan_2026-10-26.md. Builder: blender/build_interior.py. Previews: blender/landing_reel/preview_interior.py.
Scene: blender/out/frozen_FK_interior.blend (frozen_FK.blend plus the interior_* collections). Look: L07 hero_artistic day (10:30, daylight_artistic), haze volume off, 16 samples, 960 x 540, on the 4-core cloud CPU.
No reference frame is in these images (AGENTS.md rule 2).

## Part 1: concourse and entry (part1_concourse_16spp.jpg)

- p1: the outer concourse (pale panels, white round column, slat ceiling with an LED line, closed kiosk shutter, no text).
- p2: the chapter 3 entry passage from the outer concourse, with the inner concourse and the bowl beyond.
- p3: the inner concourse from the entry, towards the bowl.
- p4: the head of a lower-tier aisle, across the bowl (the planned last frame of chapter 3; the final aim goes further north, so that the tunnel placeholder on the west side is out of the frame).
- p5: from the lower tier back to the concourse front (soffit, fittings, entries; rendered before part 2, so it shows the old seats).
- Build time: 2 s. Preview time: 82 to 137 s a view (8.9 min for the first run, 3.1 min for the two fixed views).
- Fixes after the first run: p1 stood outside the outer wall and p5 under the stand; both camera points were moved.

## Part 2: stand surfaces (part2_stand_16spp.jpg)

- s1 to s3: lap points at the middle of the lower tier, 3 m (s3: 1.9 m) above the stand surface, looking ahead and inwards.
- s4: down a lower-tier aisle from its head (nosings, rail posts, the centre rail).
- s5: the new seat (616 triangles, moulded shell, blank number plate, pedestal) at close range.
- Build time: 1 s. Preview time: 42 to 90 s a view (6.4 min).
- Seen: the deep lower-tier treads (1.32 m, plan section 8) show in s4 and s5 as a wide row spacing.

## Part 3: roof underside (part3_roof_16spp.jpg)

- Added under the membrane: 180 secondary ribs (4 per primary bay), 28 secondary rings and one diagonal in each cell (6,480), white steel, 0.55 m below the membrane, for the dense triangulated lattice of frames 000155.599, 000200.000 and IF22. The primaries, cables, struts, purlins, catwalk, floodlights, speakers and hung screens were already built.
- r1: from a chapter 4 lap point across the bowl to the far roof. r3: from the chapter 3 end point (aisle head) to the far stand and roof.
- Build time: 0.3 s. Preview time: 44 to 50 s a view (3.7 min).

## Step 3: chapter 3 and 4 camera paths (chapters_3_4_preview.jpg)

- blender/landing_reel/make_interior_paths.py writes the waypoints into chapters.json; paths.py interpolates them (Catmull-Rom spline, constant speed). Lens: L07 (38 mm, vertical FOV 29.84 deg). Portrait 720 x 1280: the same paths and vertical FOV, lens not shifted.
- ch3_going_in, 10 s, 240 frames: the outer concourse, a turn into the entry passage, the passage, the inner concourse, the aisle head; the last 12 frames hold on the north stand. Speed at most 0.25 m a frame. Camera clearance to walls and columns at least 1.27 m (ray cast every 8 frames).
- ch4_bowl_lap, 10 s, 240 frames: one closed lap at the middle of the lower tier, 3 m above the seats (9.65 to 9.89 m above the pad), looking ahead and 50 deg inwards. Speed 1.81 m a frame: the near seats can strobe at 24 fps; check it in the first full-quality frames.
- Fixes found by the previews: the first chapter 3 path met a column and the side of the entry block; the entry block returns were cut from 2 m to 0.6 m; the outer concourse waypoints are placed by ray casts to the walls only (the columns had stopped the first ray casts).
- Preview time on the 4-core CPU: 84 to 115 s a frame at 16 samples, 960 x 540 (ch3 and ch4 alike); the portrait frames 40 to 45 s at 360 x 640.
- The west tunnel placeholder: out of the chapter 3 frames; in chapter 4 the dugouts and the dark tunnel mouth pass at mid distance on the west side (frames 30 to 50).

## Time used (cloud session, 2026-10-26)

| Step | Wall time |
|---|---|
| 1 plan (sources, frames, estimates, budget) | 05:15 to 05:27, 0.2 h |
| 2 part 1 concourse and entry, with previews and fixes | 05:27 to 05:45, 0.3 h |
| 2 part 2 stand surfaces, with previews | 05:42 to 05:51, 0.15 h |
| 2 part 3 roof underside, with previews | 05:51 to 05:59, 0.15 h |
| 3 paths, previews and three path fixes | 06:10 to 07:25, 1.25 h |
| Total so far | about 2.1 h (previews ran beside the parity, phone and flicker renders) |

## Stand changes that the aerial views can see (for the next bake)

- The seat model v2 (616 triangles) replaces seat_proto on all 48,664 regular seats; positions and colours are unchanged. The aerial views see a slightly different shading of the seat blocks.
- Step nosings on every aisle step of all three tiers (pale strips), rail posts every 2 rows and bent rail ends at the lower-tier aisle heads: thin, seen in the near aerial views only.
- Under the middle tier overhang, probably not seen from the aerial cameras: the inner concourse soffit at 4.4 m, its pale fascia, the pale back wall with 14 entries (it was dark), the outer concourse.
- The secondary roof grid hangs under the membrane: not seen from above.
- No change to the tier envelope, the row counts, the roof top surface or the facade.
- Seat re-check (Munene, 2026-10-26): the stand detail goes into everything; the lower tier is kept as it is. blender/out/frozen_FL.blend = frozen_FK.blend plus the seat v2, nosings, rail posts and rail ends in bowl_detail (the twin export reads it; the bakes see it in shading and shadow; the baked groups and their UVs are unchanged). blender/out/frozen_FL_interior.blend = frozen_FL.blend plus the concourse, entry and roof grid (interior_* collections, film only). The P2 bakes and chapters 1 to 4 use these two scenes.
