# Work order: hyperreal phase A, cloud only, no GPU

Date: 2026-10-17
For: the cloud Talanta build chat. Do this after steps 1 and 2 of workorder_sol_review_2026-10-17.md.
Basis: review_astra_hyperreal_2026-10-17.md, option (b). Blender is the source of hero geometry and materials. three.js loads the optimized exports.

## Constraints

- No GPU is available. Do not rent one. All rendering runs on CPU in this cloud session with `blender -b` (installed by engineering/cloud_setup.sh).
- Do not use Eevee. It needs a graphics context. Use Workbench for geometry gates and CPU Cycles for look checks.
- CPU Cycles settings for look checks: 960 x 540, 32 to 64 samples, OpenImageDenoise on, adaptive sampling on.
- The hero still uses 1920 x 1080, 128 samples and the denoiser. Render it once, after the geometry gate passes.
- If one frame takes more than 20 minutes, stop. Report the time and the scene statistics.
- The laptop stays cool. Do not ask Munene to render locally.

## Measurement status (W1b)

- Done, in gis/measurements: site boundary (8 vertices) and pitch zone (4 vertices). Both come from the Google Earth Pro image of 26 Dec 2025 (Airbus). They match Munene's saved places exactly.
- The pitch zone is the bare-earth zone, not the marked pitch. It measures about 116 x 76 m. Compare it with the grass area (about 130 x 85 m expected) and do not use it as the 105 x 68 m pitch.
- The newest Google Earth Pro image is 26 Dec 2025. The roof was still an open steel frame on that date, and the pitch had no markings. The scale checks in site_measurements.md cannot be done on this image. Mark them "not possible: no markings on the newest image". Do not mark them as failed.
- The outer steel ring of the roof is visible on that image. Munene can save these items as polygons or paths in Google Earth Pro: the roof outer ring, the roof inner ring, the bowl plinth outline, the training pitch, the track, and the plaza. The lead reads the coordinates from his myplaces.kml and sends them to you as CSV. Do not ask for screenshots.

## Stage 00: ledger and cameras (first)

1. Write gis/parameter_ledger.csv. Make one row for each dimension that the model uses. The columns are: name, value, unit, source, date, method, uncertainty, status (measured, derived or estimated).
2. Write app/cameras/manifest.json with the 16 critic cameras C01 to C16 from the Astra review. For each camera, freeze the transform, lens, sensor (36 mm), resolution, exposure, sun state and seed.
3. Acceptance: every number in bowl.js, site.js and pitch.js has a ledger row, and every camera loads in Blender and in three.js.

## Stage 01: Blender blockout (W6 restored)

1. Write blender/build_blockout.py. It reads parameter_ledger.csv and builds the bowl shell, roof ring, tiers, plinth, pitch and forecourt as named collections.
2. Run `blender -b -P blender/build_blockout.py`. Save blender/talanta_blockout.blend. Do not commit .blend files over 50 MB.
3. Render C01 to C05 (the elevations and the roof plan) with Workbench. Save the renders to blender/renders/pass_NN/.
4. Geometry gate: the roof outer ring, the bowl outline and the pitch match the ledger within the stated uncertainty. Each estimated part keeps its "estimated" label.
5. Export a glTF of the blockout. Load it in the app behind `?blender` to test the round trip. Do not remove the procedural bowl yet.

## Stage 01b: measure the finished stadium from the historian video (JWNowpO44rw)

The historian video shows the finished stadium. Its 91 indexed frames are real references, which are better than the generated images that the pagoda project used. Use them to measure and to set details, not as textures.

1. Camera match. Select 3 to 5 frames in which the pitch markings and the seating tiers are clearly visible (for example, the "pitch markings and seating tiers at 00m46s" frame). Use the pitch markings fixed by the Laws of the Game as the known geometry: the penalty area is 40.32 x 16.50 m, the goal area is 18.32 x 5.50 m, and the centre circle is 18.30 m across. Solve the camera for each frame in Blender (vanishing-point camera match, or a pose solve from the known points). Record the solve error in pixels.
2. Measure through the solved cameras: the tier heights, the roof edge height, the roof opening outline, the depth of the roof overhang, and the actual pitch length and width. Add each value to parameter_ledger.csv with status "derived (camera match)", the frame ID and the solve error.
3. Count from the frames: the roof ribs, the lattice bays, the louvre rows, the shield positions, and the seat rows in each tier. Divide each measured perimeter by its count to set the spacing. Record each count with its frame IDs.
4. Detail sheets. For the shield, the lattice node, the roof rib, the membrane edge, the seat and the VIP glazing, write a short spec (shape, colours as hex, proportions) from the frames. These specs replace the AI concept images as the reference for stage 03.
5. Check against the held-out frames in gis/heldout_frames.csv only at the end. Do not use a held-out frame for the camera match.
6. Acceptance: at least 3 frames solve with an error below 3 px, and the derived pitch size is within 2 m of a legal pitch. The measured roof outer ring agrees with the W1b value (252.0 x 214.4 m) within its uncertainty.

## Stage 02: first look pass (hero shot only)

1. Hero shot: a dry golden-hour aerial from the north-east, looking south-west toward the bowl and the Ngong Hills. Use camera C06. Show no crowd, rain or show.
2. Add only what C06 shows: physically based materials for the white metal, membrane, concrete, glass, seats and paving; a sun and sky for 17:45 East Africa Time; and light haze.
3. Use edge wear only where weather would cause it. The stadium is new.
4. Render C06 with CPU Cycles at look-check settings. Score it with the eight Astra categories. Fix the two lowest categories, then render again.
5. Stop after three passes, or when the score is 85/100 or higher. Report the scores and the render times.

## Report back

For each stage, report the commits, the render times for each camera, the gate result, and the open questions. The lead reviews the C06 renders before stage 03 (the four specialist builds) starts.

## Rules

- Follow AGENTS.md.
- Do not use frames, Google Earth imagery or concept renders as textures.
- Keep security detail out of public output.
- Measured facts outrank looks.
- Commit as Munene, with no Claude attribution.
